from __future__ import annotations

from pathlib import Path
import logging
import sqlite3
from typing import Iterable, Sequence

import pandas as pd

from db import queries as q

logger = logging.getLogger(__name__)


# Настройки экспорта человеческих заголовков и набора колонок
TABLE_EXPORT_CONFIG: dict[str, dict] = {
    "workers": {
        "columns": ["id", "full_name", "dept", "position", "personnel_no"],
        "headers": {
            "id": "Идентификатор",
            "full_name": "ФИО",
            "dept": "Цех",
            "position": "Должность",
            "personnel_no": "Таб. номер",
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
        count += q.insert_worker(conn, str(row.full_name), _opt_str(row.dept), _opt_str(row.position), str(row.personnel_no)) or 0
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