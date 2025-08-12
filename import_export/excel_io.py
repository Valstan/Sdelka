from __future__ import annotations

from pathlib import Path
import logging
import sqlite3
from typing import Iterable

import pandas as pd

from db import queries as q

logger = logging.getLogger(__name__)


# Importers

def import_workers_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    required = {"full_name", "dept", "position", "personnel_no"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

    count = 0
    for row in df.itertuples(index=False):
        count += q.insert_worker(conn, str(row.full_name), _opt_str(row.dept), _opt_str(row.position), str(row.personnel_no)) or 0
    logger.info("Импортировано работников: %s", count)
    return count


def import_job_types_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    required = {"name", "unit", "price"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_job_type(conn, str(row.name), str(row.unit), float(row.price)) or 0
    logger.info("Импортировано видов работ: %s", count)
    return count


def import_products_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    required = {"name", "product_no"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_product(conn, str(row.name), str(row.product_no)) or 0
    logger.info("Импортировано изделий: %s", count)
    return count


def import_contracts_from_excel(conn: sqlite3.Connection, file_path: str | Path) -> int:
    df = pd.read_excel(file_path)
    required = {"code", "start_date", "end_date", "description"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

    count = 0
    for row in df.itertuples(index=False):
        count += q.upsert_contract(conn, str(row.code), _opt_str(row.start_date), _opt_str(row.end_date), _opt_str(row.description)) or 0
    logger.info("Импортировано контрактов: %s", count)
    return count


# Exporters

def export_table_to_excel(conn: sqlite3.Connection, table: str, file_path: str | Path) -> Path:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    file_path = Path(file_path)
    df.to_excel(file_path, index=False)
    return file_path


def _opt_str(value: object | None) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str if value_str else None