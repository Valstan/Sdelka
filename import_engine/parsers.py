from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from utils.text import normalize_for_search
from .normalize import normalize_date_text


import logging


@dataclass
class ParsedBlock:
    kind: str
    rows: list[dict[str, Any]]


def parse_job_types(df: pd.DataFrame) -> list[dict[str, Any]]:
    # Попробуем определить строку заголовков в первых строках, если текущие колонки не текстовые
    try:
        import pandas as pd  # noqa

        def _looks_like_header_row(vals: list[str]) -> bool:
            s = " ".join(v.lower() for v in vals)
            return (
                ("вид" in s or "наимен" in s)
                and ("ед" in s or "изм" in s or "unit" in s)
                and ("цена" in s or "тариф" in s or "расцен" in s or "стоим" in s)
            )

        if all((str(c).isdigit() or str(c).strip() == "") for c in df.columns):
            for i in range(min(8, len(df))):
                vals = [str(x).strip() for x in df.iloc[i].tolist()]
                if _looks_like_header_row(vals):
                    df = df.copy()
                    df.columns = vals
                    df = df.iloc[i + 1 :].reset_index(drop=True)
                    break
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
    [str(c).strip().lower() for c in df.columns]
    name_col = next(
        (
            c
            for c in df.columns
            if "вид" in str(c).lower() or "наимен" in str(c).lower()
        ),
        None,
    )
    unit_col = next(
        (
            c
            for c in df.columns
            if any(k in str(c).lower() for k in ("ед", "unit", "изм"))
        ),
        None,
    )
    price_col = next(
        (
            c
            for c in df.columns
            if any(k in str(c).lower() for k in ("цена", "тариф", "расцен", "стоим"))
        ),
        None,
    )
    code_col = next((c for c in df.columns if "код" in str(c).lower()), None)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        name = str(r.get(name_col, "")).strip()
        unit = str(r.get(unit_col, "шт.")).strip() or "шт."
        # Нормализуем цену: допускаем пустые/None/NaN/текст — считаем их нулевыми
        price: float = 0.0
        if price_col is not None:
            raw_val = r.get(price_col, None)
            try:
                import pandas as pd  # local import safe

                if pd.isna(raw_val):
                    price = 0.0
                else:
                    s = str(raw_val)
                    s = s.replace(" ", "").replace("\xa0", "").replace(",", ".")
                    try:
                        v = float(s)
                    except Exception:
                        v = 0.0
                    # Защитимся от нечисловых значений (NaN, inf)
                    try:
                        import math

                        price = v if math.isfinite(v) else 0.0
                    except Exception:
                        price = v
            except Exception:
                price = 0.0
        if not name:
            continue
        out.append(
            {
                "name": name,
                "unit": unit,
                "price": price,
                "code": str(r.get(code_col, "")).strip(),
            }
        )
    return out


def parse_products(df: pd.DataFrame) -> list[dict[str, Any]]:
    name_col = next(
        (
            c
            for c in df.columns
            if "издел" in str(c).lower() or "наимен" in str(c).lower()
        ),
        None,
    )
    no_col = next(
        (
            c
            for c in df.columns
            if "зав" in str(c).lower()
            or "номер" in str(c).lower()
            or "№" in str(c).lower()
        ),
        None,
    )
    contract_col = next(
        (
            c
            for c in df.columns
            if "контракт" in str(c).lower()
            or "договор" in str(c).lower()
            or "шифр" in str(c).lower()
        ),
        None,
    )
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        name = str(r.get(name_col, "")).strip()
        prod_no = str(r.get(no_col, "")).strip()
        contract_code = str(r.get(contract_col, "")).strip()
        if not (name and prod_no):
            continue
        out.append(
            {"name": name, "product_no": prod_no, "contract_code": contract_code}
        )
    return out


def parse_contracts(df: pd.DataFrame) -> list[dict[str, Any]]:
    [str(c).strip().lower() for c in df.columns]
    # Базовые колонки
    code_col = next(
        (
            c
            for c in df.columns
            if "шифр" in str(c).lower() or "номер" in str(c).lower()
        ),
        None,
    )
    name_col = next((c for c in df.columns if "наимен" in str(c).lower()), None)
    type_col = next(
        (
            c
            for c in df.columns
            if "вид контракт" in str(c).lower()
            or ("вид" in str(c).lower() and "контракт" in str(c).lower())
        ),
        None,
    )
    exec_col = next((c for c in df.columns if "исполнител" in str(c).lower()), None)
    if exec_col is None:
        exec_col = next(
            (
                c
                for c in df.columns
                if "исполн" in str(c).lower() and "дата" not in str(c).lower()
            ),
            None,
        )
    igk_col = next((c for c in df.columns if "игк" in str(c).lower()), None)
    cn_col = next(
        (
            c
            for c in df.columns
            if "номер контракт" in str(c).lower()
            or ("номер" in str(c).lower() and "контракт" in str(c).lower())
        ),
        None,
    )
    acc_col = next(
        (c for c in df.columns if "счет" in str(c).lower() or "р/с" in str(c).lower()),
        None,
    )
    # Даты: стараемся различать начало и окончание, избегая путаницы с "исполнитель"
    start_col = next(
        (
            c
            for c in df.columns
            if any(k in str(c).lower() for k in ("начал", "заключ"))
            or (
                "срок" in str(c).lower()
                and "с" in str(c).lower()
                and "по" not in str(c).lower()
                and "до" not in str(c).lower()
            )
        ),
        None,
    )
    # Для окончания используем более специфичные признаки: 'оконч', 'действует до', 'срок ... до', 'по'/'до' рядом с срок/действ
    end_col = None
    for c in df.columns:
        s = str(c).lower()
        if (
            "оконч" in s
            or "действует до" in s
            or ("срок" in s and ("до" in s or "по" in s))
            or ("действ" in s and ("до" in s or "по" in s))
        ):
            end_col = c
            break
    # Явное правило под подсказанный столбец: "Плановая дата исполнения контракта"
    if end_col is None:
        for c in df.columns:
            s = str(c).lower()
            if (
                ("планов" in s or "плановая" in s)
                and "дата" in s
                and "исполн" in s
                and "контракт" in s
            ):
                end_col = c
                break
    # если так и не нашли, попробуем англ
    if end_col is None:
        end_col = next(
            (
                c
                for c in df.columns
                if any(
                    k in str(c).lower()
                    for k in ("end", "finish", "valid to", "valid until")
                )
            ),
            None,
        )
    desc_col = next(
        (
            c
            for c in df.columns
            if "коммент" in str(c).lower()
            or "опис" in str(c).lower()
            or "примеч" in str(c).lower()
        ),
        None,
    )
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        code = str(r.get(code_col, "")).strip()
        if not code:
            continue
        start_val = r.get(start_col, None)
        end_val = r.get(end_col, None)
        out.append(
            {
                "code": code,
                "name": str(r.get(name_col, "")).strip() or None,
                "contract_type": str(r.get(type_col, "")).strip() or None,
                "executor": str(r.get(exec_col, "")).strip() or None,
                "igk": str(r.get(igk_col, "")).strip() or None,
                "contract_number": str(r.get(cn_col, "")).strip() or None,
                "bank_account": str(r.get(acc_col, "")).strip() or None,
                "start_date": normalize_date_text(
                    None if start_val is None else str(start_val).strip() or None
                ),
                "end_date": normalize_date_text(
                    None if end_val is None else str(end_val).strip() or None
                ),
                "description": str(r.get(desc_col, "")).strip() or None,
            }
        )
    return out


def parse_workers(df: pd.DataFrame) -> list[dict[str, Any]]:
    # Попробуем извлечь номер цеха из шапки документа (первые строки листа)
    dept_from_header: str | None = None
    try:
        scan_rows = min(12, len(df))
        for i in range(scan_rows):
            try:
                row_vals = [str(x).strip() for x in df.iloc[i].tolist()]
            except Exception:
                row_vals = []
            line = " ".join(row_vals)
            low = line.lower()
            # Ищем шаблоны вида: "Список работников цеха № 1", "Дизельный цех № 2", "Цех № 3"
            import re as _re

            m = _re.search(r"(?i)цех[ау]?\s*№\s*(\d+)", low)
            if m:
                dept_from_header = m.group(1)
                break
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    # Нормализуем заголовки. Для XLSX бывает, что заголовки на строке > 0.
    # Ищем строку, содержащую "ФИО" и/или явные заголовки работника.
    try:
        import pandas as pd  # noqa

        df = df.copy()
        # 1) Попытка: явная колонка "ФИО"
        header_row_index = None
        scan_limit = min(6, len(df))
        for i in range(scan_limit):
            row_low = [str(x).strip().lower() for x in df.iloc[i].tolist()]
            row_text = " ".join(row_low)
            if "фио" in row_text:
                header_row_index = i
                break
        # 2) Если не нашли — эвристика по наибольшему числу ключевых слов заголовков в первых 20 строках
        if header_row_index is None:
            best_idx = None
            best_score = -1
            keys_main = ("фио", "фамил", "имя", "отче", "сотрудник", "работник")
            keys_extra = (
                "таб",
                "табел",
                "табель",
                "персонал",
                "tn",
                "personnel",
                "должн",
                "разряд",
                "цех",
                "отдел",
                "подраздел",
                "участок",
                "бригада",
            )
            for i in range(min(20, len(df))):
                row_low = [str(x).strip().lower() for x in df.iloc[i].tolist()]
                s = " ".join(row_low)
                score = sum(1 for k in keys_main if k in s) * 2 + sum(
                    1 for k in keys_extra if k in s
                )
                if score > best_score:
                    best_score = score
                    best_idx = i
            if best_idx is not None and best_score >= 2:
                header_row_index = best_idx
        # 3) Применяем найденную строку заголовков
        if header_row_index is not None:
            df.columns = [str(x).strip() for x in df.iloc[header_row_index].tolist()]
            df = df.iloc[header_row_index + 1 :].reset_index(drop=True)
        else:
            # 4) Если колонок почти нет или они числовые/пустые — пробуем взять первую осмысленную строку
            try:
                if all(
                    (str(c).strip() == "" or str(c).strip().isdigit())
                    for c in df.columns
                ):
                    for i in range(min(20, len(df))):
                        vals = [str(x).strip() for x in df.iloc[i].tolist()]
                        line = " ".join(vals).lower()
                        if any(k in line for k in keys_main) or any(
                            k in line for k in keys_extra
                        ):
                            df.columns = [str(x).strip() for x in df.iloc[i].tolist()]
                            df = df.iloc[i + 1 :].reset_index(drop=True)
                            break
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    # Определяем возможные колонки
    fio_col = next(
        (
            c
            for c in df.columns
            if "фио" in str(c).lower()
            or "сотрудник" in str(c).lower()
            or "работник" in str(c).lower()
        ),
        None,
    )
    fam_col = next((c for c in df.columns if "фамил" in str(c).lower()), None)
    im_col = next(
        (c for c in df.columns if str(c) and "имя" == str(c).strip().lower()), None
    )
    otch_col = next((c for c in df.columns if "отче" in str(c).lower()), None)
    tab_col = next(
        (
            c
            for c in df.columns
            if any(
                k in str(c).lower()
                for k in (
                    "таб",
                    "табел",
                    "табель",
                    "персонал",
                    "tn",
                    "personnel",
                    "таб.№",
                    "таб. №",
                    "таб.н",
                )
            )
        ),
        None,
    )
    pos_col = next(
        (
            c
            for c in df.columns
            if any(k in str(c).lower() for k in ("должн", "разряд", "роль", "позиция"))
        ),
        None,
    )
    dept_col = next(
        (
            c
            for c in df.columns
            if any(
                k in str(c).lower()
                for k in (
                    "цех",
                    "цех№",
                    "цех №",
                    "отдел",
                    "подраздел",
                    "участок",
                    "бригада",
                    "dept",
                    "department",
                )
            )
        ),
        None,
    )
    status_col = next(
        (
            c
            for c in df.columns
            if any(k in str(c).lower() for k in ("статус", "уволен", "работает"))
        ),
        None,
    )

    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        fio_val = None
        if fio_col is not None:
            fio_val = str(r.get(fio_col, "")).strip()
        else:
            # Попробуем собрать ФИО из отдельных колонок
            parts: list[str] = []
            if fam_col is not None:
                parts.append(str(r.get(fam_col, "")).strip())
            if im_col is not None:
                parts.append(str(r.get(im_col, "")).strip())
            if otch_col is not None:
                parts.append(str(r.get(otch_col, "")).strip())
            fio_val = " ".join([p for p in parts if p])
        fio = (fio_val or "").strip()
        if not fio:
            continue
        personnel_no = str(r.get(tab_col, "")).strip() if tab_col is not None else ""
        # Если в файле табельный в третьем столбце без заголовка — fallback на эвристику по позициям
        if not personnel_no and tab_col is None:
            try:
                third_val = r.iloc[2] if len(r) > 2 else None
                personnel_no = str(third_val).strip() if third_val is not None else ""
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        if not personnel_no:
            personnel_no = f"AUTO-{normalize_for_search(fio)}"
        position = (
            str(r.get(pos_col, "")).strip() or None if pos_col is not None else None
        )
        dept_raw = None
        if dept_col is not None:
            try:
                dept_raw = r.get(dept_col, "")
            except Exception:
                dept_raw = ""
        dept = None
        if dept_raw is not None:
            s = str(dept_raw).strip()
            if s:
                # Вырезаем цифры, поддержка форматов "2", 2, 2.0, "Цех № 2"
                try:
                    if s.isdigit():
                        dept = s
                    else:
                        try:
                            val = float(s.replace(",", "."))
                            if val.is_integer():
                                dept = str(int(val))
                        except Exception as exc:
                            logging.getLogger(__name__).exception(
                                "Ignored unexpected error: %s", exc
                            )
                        if dept is None:
                            import re as _re

                            m = _re.search(r"(\d+)", s)
                            dept = m.group(1) if m else None
                except Exception:
                    dept = None
        if (dept is None or dept == "") and dept_from_header:
            # Пользователь просил сохранить именно цифру номера цеха
            dept = dept_from_header
        status_raw = (
            str(r.get(status_col, "")).strip().lower() if status_col is not None else ""
        )
        status: str | None = None
        if status_raw:
            if any(k in status_raw for k in ("уволен", "не работает", "fired")):
                status = "Уволен"
            elif any(k in status_raw for k in ("работ", "active", "актив")):
                status = "Работает"
        out.append(
            {
                "full_name": fio,
                "personnel_no": personnel_no,
                "position": position,
                "dept": dept,
                "status": status,
            }
        )
    return out
