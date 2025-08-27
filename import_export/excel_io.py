from __future__ import annotations

from pathlib import Path
import logging
import sqlite3
from typing import Iterable, Sequence

import pandas as pd
import re
from datetime import datetime

from db import queries as q
from db.sqlite import get_connection
from config.settings import CONFIG
from config.settings import CONFIG

logger = logging.getLogger(__name__)


# Настройки экспорта человеческих заголовков и набора колонок
TABLE_EXPORT_CONFIG: dict[str, dict] = {
    "workers": {
        "columns": ["id", "full_name", "dept", "position", "personnel_no", "status"],
        "headers": {
            "id": "Идентификатор",
            "full_name": "ФИО",
            "dept": "Цех",
            "position": "Должность",
            "personnel_no": "Таб. номер",
            "status": "Статус",
        },
    },
    "job_types": {
        "columns": ["id", "name", "unit", "price"],
        "headers": {
            "id": "Идентификатор",
            "name": "Вид работ",
            "unit": "Ед. изм.",
            "price": "Цена",
        },
    },
    "products": {
        "columns": ["id", "name", "product_no"],
        "headers": {
            "id": "Идентификатор",
            "name": "Наименование",
            "product_no": "№ изд.",
        },
    },
    "contracts": {
        "columns": ["id", "code", "start_date", "end_date", "description"],
        "headers": {
            "id": "Идентификатор",
            "code": "Шифр контракта",
            "start_date": "Дата начала",
            "end_date": "Дата окончания",
            "description": "Описание",
        },
    },
    "work_orders": {
        "columns": ["id", "order_no", "date", "product_id", "contract_id", "total_amount"],
        "headers": {
            "id": "Идентификатор",
            "order_no": "№ наряда",
            "date": "Дата",
            "product_id": "ID изделия",
            "contract_id": "ID контракта",
            "total_amount": "Итоговая сумма",
        },
    },
    "work_order_items": {
        "columns": ["id", "work_order_id", "job_type_id", "quantity", "unit_price", "line_amount"],
        "headers": {
            "id": "Идентификатор",
            "work_order_id": "ID наряда",
            "job_type_id": "ID вида работ",
            "quantity": "Кол-во",
            "unit_price": "Цена",
            "line_amount": "Сумма",
        },
    },
    "work_order_workers": {
        "columns": ["work_order_id", "worker_id"],
        "headers": {
            "work_order_id": "ID наряда",
            "worker_id": "ID работника",
        },
    },
}
# ------------------------
# Complex XLSX importer
# ------------------------

_RUBLE_DECIMAL_RE = re.compile(r"\s")


def _to_float_price(value: object) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    # Normalize Rus formatting: "2 500,00" -> "2500.00"
    s = s.replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def _norm_str(val: object) -> str:
    try:
        import pandas as _pd
        if val is None or _pd.isna(val):
            return ""
    except Exception:
        if val is None:
            return ""
    return str(val).strip()


def _open_workbook(file_path: str | Path) -> pd.ExcelFile:
    """Open workbook supporting both .xlsx/.xls and .ods (if odfpy is installed)."""
    file_path = str(file_path)
    try:
        # Let pandas auto-detect engine for Excel formats (.xlsx/.xls)
        return pd.ExcelFile(file_path)
    except Exception as exc:
        # Try ODS explicitly if extension suggests so
        if file_path.lower().endswith(".ods"):
            try:
                return pd.ExcelFile(file_path, engine="odf")
            except Exception as exc2:
                raise RuntimeError(
                    "Не удалось открыть .ods. Установите пакет 'odfpy' (pip install odfpy)."
                ) from exc2
        raise


def _parse_orders_sheet(df: pd.DataFrame) -> list[dict]:
    """
    Парсинг листа нарядов с группировкой по датам вида "16.06." и привязкой к ближайшему
    выше идущему заголовку "Изделие № ...". Возвращает список групп:
      { date: "ДД.ММ.ГГГГ", products: ["К01АТ0317/84", ...], items: [{job_name, unit, unit_price, qty, amount}], workers: [...] }
    """
    # 1) Стандартизируем заголовки столбцов для чтения строк таблицы
    rename = {}
    mapping = {
        "дата": "date",
        "наименование выполненых работ": "job_name",
        "наименование выполненных работ": "job_name",
        "ед. изм.": "unit",
        "ед. изм": "unit",
        "расценка  (руб.)": "unit_price",
        "расценка (руб.)": "unit_price",
        "расценка": "unit_price",
        "объем выполненных работ": "qty",
        "объем": "qty",
        "кол-во": "qty",
        "сумма  (руб)": "amount",
        "сумма (руб)": "amount",
        "сумма": "amount",
        "примечание": "note",
    }
    for c in df.columns:
        key = str(c).strip().lower()
        if key in mapping:
            rename[c] = mapping[key]
    if rename:
        df = df.rename(columns=rename)

    # 2) Соберем работников в верхней части листа
    workers: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()
    max_rows_scan = min(40, len(df))
    for i in range(max_rows_scan):
        row_vals = [ _norm_str(v) for v in df.iloc[i, :].tolist() ]
        # Ищем "ФИО сотрудника"
        name: str | None = None
        for j, s in enumerate(row_vals):
            s_low = s.casefold()
            if s_low.startswith("фио сотрудника"):
                if ":" in s:
                    name = s.split(":", 1)[1].strip(" ;")
                if not name:
                    for k in range(j + 1, min(j + 4, len(row_vals))):
                        if row_vals[k]:
                            name = row_vals[k]
                            break
                break
        if not name:
            continue
        pers: str | None = None
        for ii in range(i, min(i + 3, max_rows_scan)):
            vals = [ _norm_str(v) for v in df.iloc[ii, :].tolist() ]
            for j, s in enumerate(vals):
                s_low = s.casefold().replace(" ", "")
                if s_low.startswith("таб№") or s_low == "таб№" or s_low.startswith("таб#"):
                    for k in range(j + 1, min(j + 3, len(vals))):
                        v = _norm_str(vals[k])
                        if v:
                            pers = re.sub(r"[^0-9]", "", v)
                            break
                    if pers:
                        break
                m = re.search(r"таб\s*№\s*([0-9]+)", s_low)
                if m:
                    pers = m.group(1)
                    break
            if pers:
                break
        pair = (name, pers or "")
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            workers.append({"full_name": name, "personnel_no": pers or None})

    # 3) Год из шапки (например "2025г.")
    header_text = "\n".join([";".join([_norm_str(v) for v in df.iloc[i, :].tolist()[:8]]) for i in range(min(20, len(df)))])
    year = None
    m_year = re.search(r"(20\d{2})\s*г", header_text)
    if m_year:
        try:
            year = int(m_year.group(1))
        except Exception:
            year = None
    if year is None:
        from datetime import datetime as _dt
        year = _dt.now().year

    # 4) Идём по строкам ниже заголовка таблицы и группируем по датам вида "ДД.ММ."
    # Найти начало табличной части (строка с колонкой "Дата")
    header_idx = None
    for i, r in df.iterrows():
        row_lower = [ _norm_str(v).lower() for v in r.tolist()[:6] ]
        if "дата" in row_lower and any("наименование" in x for x in row_lower):
            header_idx = i
            break
    groups: list[dict] = []
    current_products: list[str] = []
    current_group: dict | None = None
    if header_idx is not None:
        data = df.iloc[header_idx + 1 :]
        for _, r in data.iterrows():
            cells = [ _norm_str(v) for v in r.tolist() ]
            first_cell = (cells[0] if cells else "").strip()
            low_first = first_cell.lower()
            if not first_cell and any("изделие №" in _norm_str(c).lower() for c in cells[:3]):
                # Иногда заголовок изделия лежит не в первом столбце
                low_first = next(( _norm_str(c).lower() for c in cells if "изделие №" in _norm_str(c).lower()), low_first)
                first_cell = next(( c for c in cells if "изделие №" in _norm_str(c).lower()), first_cell)
            # Обновление списка изделий
            if low_first.startswith("изделие №"):
                try:
                    prod_str = first_cell.split("№", 1)[1]
                except Exception:
                    prod_str = first_cell
                # удалить пометки типа "повтор" в любой позиции
                prod_str = re.sub(r"(?i)\bповтор\b", "", prod_str)
                prod_str = re.sub(r"\s{2,}", " ", prod_str)
                prods = [ p.strip() for p in prod_str.split(",") if p.strip() ]
                current_products = prods
                continue
            # Новая дата группы вида ДД.ММ. (может быть с годом)
            m = re.match(r"^(\d{1,2})[.\-/](\d{1,2})(?:[.\-/](\d{2,4}))?", first_cell)
            if m:
                d, mth, yr = m.groups()
                yy = int(year) if yr is None else int( ("20"+yr) if len(yr)==2 else yr )
                from datetime import datetime as _dt
                try:
                    date_str = _dt(int(yy), int(mth), int(d)).strftime(CONFIG.date_format)
                except Exception:
                    date_str = _dt(year, 1, 1).strftime(CONFIG.date_format)
                # Закрыть предыдущую группу
                if current_group and current_group.get("items"):
                    groups.append(current_group)
                current_group = {"date": date_str, "products": list(current_products), "items": [], "workers": workers}
                continue
            # Стоп-строка ИТОГО
            if low_first.startswith("итого"):
                if current_group:
                    groups.append(current_group)
                    current_group = None
                continue
            # Строка работы — парсим, если есть активная группа
            if current_group:
                job_name = _norm_str(r.get("job_name", r.iloc[1] if len(r) > 1 else ""))
                if not job_name:
                    continue
                unit = _norm_str(r.get("unit")) or "шт."
                unit_price = _to_float_price(r.get("unit_price"))
                qty = _to_float_price(r.get("qty")) or 1.0
                amount = _to_float_price(r.get("amount")) or (unit_price * qty)
                current_group["items"].append({
                    "job_name": job_name,
                    "unit": unit,
                    "unit_price": unit_price,
                    "qty": qty,
                    "amount": amount,
                })
        # финализировать последнюю группу
        if current_group and current_group.get("items"):
            groups.append(current_group)

    return groups


def _parse_jobtypes_sheet(df: pd.DataFrame) -> list[dict]:
    """Parse price list like samples 1-3 into job_types entries."""
    # Try to standardize header
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower()
        if "наименование" in key:
            rename[c] = "name"
        elif key.startswith("ед"):
            rename[c] = "unit"
        elif "цена" in key or "расценка" in key:
            rename[c] = "price"
        elif key.startswith("№") or "п/п" in key:
            rename[c] = "idx"
    if rename:
        df = df.rename(columns=rename)
    jobs: list[dict] = []
    for _, r in df.iterrows():
        name = _norm_str(r.get("name")) or _norm_str(r.iloc[1] if len(r) > 1 else "")
        if not name:
            continue
        unit = _norm_str(r.get("unit")) or "шт."
        price = _to_float_price(r.get("price"))
        jobs.append({"name": name, "unit": unit, "price": price if price > 0 else 0.0})
    return jobs


def import_xlsx_full(file_path: str | Path, progress_cb: callable | None = None) -> tuple[int, int, int]:
    """
    Import multi-sheet workbook:
    - detect and upsert job types
    - detect and create work orders with workers and items
    Returns: (num_jobtypes, num_products, num_orders)
    """
    import openpyxl  # ensure engine for .xlsx
    xls = _open_workbook(file_path)

    def report(step: int, total: int, note: str):
        if progress_cb:
            try:
                progress_cb(step, total, note)
            except Exception:
                pass

    total_steps = len(xls.sheet_names)
    jt_count = 0
    orders_count = 0
    products_count = 0

    with get_connection() as conn:
        step = 0
        for sheet in xls.sheet_names:
            step += 1
            report(step, total_steps, f"Лист: {sheet}")
            df = xls.parse(sheet)
            # Heuristic: if it has columns with 'Наименование' + 'Ед.' + 'Цена' -> job types sheet
            lower_cols = [str(c).strip().lower() for c in df.columns]
            is_jobtypes = any("наименование" in c for c in lower_cols) and any("ед" in c for c in lower_cols) and any("цена" in c or "расценка" in c for c in lower_cols)
            is_orders = any("фио" in _norm_str(v).lower() for v in df.head(5).iloc[:, 0].tolist()) or any("дата" in c for c in lower_cols)

            if is_jobtypes and not is_orders:
                jobs = _parse_jobtypes_sheet(df)
                for j in jobs:
                    if not j["name"]:
                        continue
                    q.upsert_job_type(conn, j["name"], j["unit"] or "шт.", float(j["price"]))
                    jt_count += 1
                continue

            if is_orders:
                groups = _parse_orders_sheet(df)
                for g in groups:
                    products: list[str] = g.get("products") or []
                    items = g.get("items") or []
                    workers = g.get("workers") or []
                    date_str = g.get("date") or datetime.now().strftime(CONFIG.date_format)
                    if not products:
                        products = [""]
                    # Подготовка job types
                    for it in items:
                        q.upsert_job_type(conn, it["job_name"], it["unit"], float(it["unit_price"]))
                    # Контракт из шапки или ИМПОРТ_ГОД
                    header_text = "\n".join([";".join([_norm_str(v) for v in df.iloc[i, :].tolist()[:8]]) for i in range(min(15, len(df)))])
                    mcode = re.search(r"(контракт|шифр)[:\s]*([\w\-/.]+)", header_text, flags=re.IGNORECASE)
                    if mcode:
                        code = _norm_str(mcode.group(2))
                    else:
                        code = f"ИМПОРТ_{datetime.now().year}"
                    q.upsert_contract(conn, code, None, None, "Импорт из XLSX")
                    c_row = conn.execute("SELECT id FROM contracts WHERE code=?", (code,)).fetchone()
                    contract_id = int(c_row[0]) if c_row else 1

                    # Шаблон работников
                    worker_inputs_template = []
                    manual_id_counter = -1
                    for w in (workers or []):
                        nm = _norm_str(w.get("full_name"))
                        pn = _norm_str(w.get("personnel_no"))
                        if not nm:
                            continue
                        roww = q.get_worker_by_personnel_no(conn, pn) if pn else None
                        if not roww:
                            roww = q.get_worker_by_full_name(conn, nm)
                        if roww:
                            worker_inputs_template.append({"worker_id": int(roww["id"]), "worker_name": nm, "amount": None})
                        else:
                            worker_inputs_template.append({"worker_id": manual_id_counter, "worker_name": nm, "amount": None})
                            manual_id_counter -= 1
                    if not worker_inputs_template:
                        nm = "Неизвестный работник"
                        pn = f"TEMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        wid = q.insert_worker(conn, nm, None, None, pn)
                        worker_inputs_template = [{"worker_id": int(wid), "worker_name": nm, "amount": None}]

                    # Создаём по наряду на каждое изделие, деля qty поровну по изделиям
                    k = max(1, len(products))
                    from services.work_orders import WorkOrderInput, WorkOrderItemInput, WorkOrderWorkerInput, create_work_order
                    for prod_no in products:
                        product_id = None
                        prod_no_clean = _norm_str(prod_no)
                        if prod_no_clean:
                            # name = "Изделие", product_no = код
                            q.upsert_product(conn, "Изделие", prod_no_clean)
                            products_count += 1
                            rowp = conn.execute("SELECT id FROM products WHERE product_no = ?", (prod_no_clean,)).fetchone()
                            if rowp:
                                product_id = int(rowp[0])
                        wo_items_inputs = []
                        for it in items:
                            jt = q.get_job_type_by_name(conn, it["job_name"]) or conn.execute("SELECT id FROM job_types WHERE name=?", (it["job_name"],)).fetchone()
                            if jt:
                                jt_id = int(jt[0] if not isinstance(jt, dict) else jt["id"])  # tolerate row/dict
                                # всем изделиям ставим по максимальному количеству работ (из условия)
                                max_qty = float(it.get("qty", 1.0) or 1.0)
                                wo_items_inputs.append(WorkOrderItemInput(job_type_id=jt_id, quantity=max_qty))
                        wo_workers = [WorkOrderWorkerInput(worker_id=w["worker_id"], worker_name=w["worker_name"], amount=w.get("amount")) for w in worker_inputs_template]
                        data = WorkOrderInput(date=date_str, product_id=product_id, contract_id=contract_id, items=wo_items_inputs, workers=wo_workers)
                        try:
                            create_work_order(conn, data)
                            orders_count += 1
                        except Exception as e:
                            logger.exception("Не удалось создать наряд с листа %s: %s", sheet, e)
                continue

            # Unknown sheet - skip
            report(step, total_steps, f"Пропущен: {sheet}")

    return jt_count, products_count, orders_count


# Importers

def import_workers_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    # Разрешаем русские заголовки колонок при импорте
    ru_to_en = {
        "фио": "full_name",
        "цех": "dept",
        "должность": "position",
        "таб. номер": "personnel_no",
        "табельный номер": "personnel_no",
    }
    # Построим карту переименования текущих колонок в ожидаемые внутренние имена
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = str(col).strip().lower()
        if key in ru_to_en:
            rename_map[col] = ru_to_en[key]
        # если уже внутренние имена — оставляем как есть
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # Дополнительно поддержим статус (необязателен): Работает / Уволен
    ru_to_en_status = {"статус": "status", "состояние": "status"}
    for col in list(df.columns):
        key = str(col).strip().lower()
        if key in ru_to_en_status:
            rename_map[col] = ru_to_en_status[key]
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    required = {"full_name", "dept", "position", "personnel_no"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(
            "Отсутствуют колонки: "
            + ", ".join(missing)
            + ". Ожидаются заголовки: ФИО, Цех, Должность, Таб. номер (или full_name, dept, position, personnel_no)."
        )

    count = 0
    for row in df.itertuples(index=False):
        status = getattr(row, "status", None)
        status_val = None
        if status is not None:
            s = str(status).strip()
            if s:
                status_val = s
        count += q.upsert_worker(conn, str(row.full_name), _opt_str(row.dept), _opt_str(row.position), str(row.personnel_no), status=status_val) or 0
    logger.info("Импортировано работников: %s", count)
    return count


def import_job_types_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    ru_to_en = {
        "вид работ": "name",
        "виды работ": "name",
        "наименование": "name",
        "ед. изм.": "unit",
        "единица измерения": "unit",
        "цена": "price",
    }
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = str(col).strip().lower()
        if key in ru_to_en:
            rename_map[col] = ru_to_en[key]
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    required = {"name", "unit", "price"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(
            "Отсутствуют колонки: "
            + ", ".join(missing)
            + ". Ожидаются заголовки: Вид работ, Ед. изм., Цена (или name, unit, price)."
        )

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_job_type(conn, str(row.name), str(row.unit), float(row.price)) or 0
    logger.info("Импортировано видов работ: %s", count)
    return count


def import_products_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    ru_to_en = {
        "наименование": "name",
        "изделие": "name",
        "№ изд.": "product_no",
        "номер изделия": "product_no",
    }
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = str(col).strip().lower()
        if key in ru_to_en:
            rename_map[col] = ru_to_en[key]
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    required = {"name", "product_no"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(
            "Отсутствуют колонки: "
            + ", ".join(missing)
            + ". Ожидаются заголовки: Наименование, № изд. (или name, product_no)."
        )

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_product(conn, str(row.name), str(row.product_no)) or 0
    logger.info("Импортировано изделий: %s", count)
    return count


def import_contracts_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    ru_to_en = {
        "шифр контракта": "code",
        "шифр": "code",
        "дата начала": "start_date",
        "дата окончания": "end_date",
        "описание": "description",
    }
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = str(col).strip().lower()
        if key in ru_to_en:
            rename_map[col] = ru_to_en[key]
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    required = {"code", "start_date", "end_date", "description"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(
            "Отсутствуют колонки: "
            + ", ".join(missing)
            + ". Ожидаются заголовки: Шифр контракта, Дата начала, Дата окончания, Описание (или code, start_date, end_date, description)."
        )

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_contract(conn, str(row.code), _opt_str(row.start_date), _opt_str(row.end_date), _opt_str(row.description)) or 0
    logger.info("Импортировано контрактов: %s", count)
    return count


# Exporters

def export_table_to_excel(conn: sqlite3.Connection, table: str, file_path: str | Path) -> Path:
    cfg = TABLE_EXPORT_CONFIG.get(table)
    if table == "workers":
        # Пользовательская сортировка: статус (Работает сначала), затем цех, должность (начальники первыми), ФИО
        sql = (
            "SELECT id, full_name, dept, position, personnel_no, COALESCE(status, 'Работает') AS status "
            "FROM workers"
        )
        df = pd.read_sql_query(sql, conn)
        # Ключи сортировки
        def status_key(s: str) -> int:
            return 0 if str(s).strip() == "Работает" else 1
        def position_key(p: str) -> tuple[int, str]:
            txt = (p or "").strip()
            is_head = 0 if "начальник" in txt.casefold() else 1
            return (is_head, txt.casefold())
        df["_status_key"] = df["status"].map(status_key)
        df["_dept_key"] = df["dept"].astype(str).str.casefold()
        df["_pos_key_tuple"] = df["position"].apply(position_key)
        # pandas не сортирует напрямую по tuple-колонке стабильно между версиями, развернем на два столбца
        df["_pos_is_head"] = df["_pos_key_tuple"].apply(lambda t: t[0])
        df["_pos_name"] = df["_pos_key_tuple"].apply(lambda t: t[1])
        df.sort_values(by=["_status_key", "_dept_key", "_pos_is_head", "_pos_name", "full_name"], inplace=True, kind="mergesort")
        df.drop(columns=["_status_key", "_dept_key", "_pos_key_tuple", "_pos_is_head", "_pos_name"], inplace=True)
        # Переименуем заголовки по конфигу
        headers = TABLE_EXPORT_CONFIG["workers"]["headers"]
        df.rename(columns=headers, inplace=True)
    else:
        if cfg and cfg.get("columns"):
            cols = ", ".join(cfg["columns"])
            df = pd.read_sql_query(f"SELECT {cols} FROM {table}", conn)
            df.rename(columns=cfg.get("headers", {}), inplace=True)
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def export_all_tables_to_excel(conn: sqlite3.Connection, dir_path: str | Path) -> list[Path]:
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for table in ("workers", "job_types", "products", "contracts", "work_orders", "work_order_items", "work_order_workers"):
        path = dir_path / f"{table}.xlsx"
        export_table_to_excel(conn, table, path)
        outputs.append(path)
    return outputs


def analyze_orders_workbook(file_path: str | Path) -> list[dict]:
    """
    Dry-run analyzer: parse workbook (xlsx/ods), detect order groups and return
    a summary list of dicts without writing to DB.
    Each entry: {sheet, date, products, workers, items}
    """
    xls = _open_workbook(file_path)
    summary: list[dict] = []
    for sheet in xls.sheet_names:
        try:
            df = xls.parse(sheet)
        except Exception:
            continue
        lower_cols = [str(c).strip().lower() for c in df.columns]
        is_jobtypes = any("наименование" in c for c in lower_cols) and any("ед" in c for c in lower_cols) and any("цена" in c or "расценка" in c for c in lower_cols)
        is_orders = any("фио" in _norm_str(v).lower() for v in df.head(5).iloc[:, 0].tolist()) or any("дата" in c for c in lower_cols)
        if is_orders:
            groups = _parse_orders_sheet(df)
            for g in groups:
                entry = {
                    "sheet": sheet,
                    "date": g.get("date"),
                    "products": list(g.get("products") or []),
                    "workers": [w.get("full_name") for w in (g.get("workers") or [])],
                    "items": [
                        {
                            "job_name": it.get("job_name"),
                            "qty": it.get("qty"),
                            "unit_price": it.get("unit_price"),
                        }
                        for it in (g.get("items") or [])
                    ],
                }
                summary.append(entry)
        elif is_jobtypes:
            # include short note for jobtypes sheet
            jobs = _parse_jobtypes_sheet(df)
            summary.append({"sheet": sheet, "jobtypes_count": len(jobs)})
        else:
            summary.append({"sheet": sheet, "note": "Пропущен"})
    return summary


# Templates

def generate_workers_template(file_path: str | Path) -> Path:
    # Генерируем шаблон с русскими заголовками для удобства ввода
    df = pd.DataFrame({"ФИО": [], "Цех": [], "Должность": [], "Таб. номер": []})
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def generate_job_types_template(file_path: str | Path) -> Path:
    df = pd.DataFrame({"Вид работ": [], "Ед. изм.": [], "Цена": []})
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def generate_products_template(file_path: str | Path) -> Path:
    df = pd.DataFrame({"Наименование": [], "№ изд.": []})
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def generate_contracts_template(file_path: str | Path) -> Path:
    df = pd.DataFrame({"Шифр контракта": [], "Дата начала": [], "Дата окончания": [], "Описание": []})
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def _opt_str(value: object | None) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str if value_str else None