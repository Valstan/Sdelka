from __future__ import annotations

import logging
import sqlite3
from typing import Iterable

logger = logging.getLogger(__name__)


DDL_TABLES_SQL = r"""
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    dept TEXT,
    position TEXT,
    personnel_no TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS job_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    product_no TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    start_date TEXT,
    end_date TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no INTEGER NOT NULL UNIQUE,
    date TEXT NOT NULL,
    product_id INTEGER,
    contract_id INTEGER NOT NULL,
    total_amount NUMERIC NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS work_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL,
    job_type_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),
    line_amount NUMERIC NOT NULL CHECK (line_amount >= 0),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (job_type_id) REFERENCES job_types(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS work_order_workers (
    work_order_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    PRIMARY KEY (work_order_id, worker_id),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
"""

DDL_INDEXES = (
    ("idx_workers_full_name", "workers", ("full_name",), "CREATE INDEX IF NOT EXISTS idx_workers_full_name ON workers(full_name)"),
    ("idx_job_types_name", "job_types", ("name",), "CREATE INDEX IF NOT EXISTS idx_job_types_name ON job_types(name)"),
    ("idx_products_name_no", "products", ("name", "product_no"), "CREATE INDEX IF NOT EXISTS idx_products_name_no ON products(name, product_no)"),
    ("idx_contracts_code", "contracts", ("code",), "CREATE INDEX IF NOT EXISTS idx_contracts_code ON contracts(code)"),
    ("idx_work_orders_date", "work_orders", ("date",), "CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date)"),
)


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create or migrate schema safely.

    - Создает таблицы, если отсутствуют
    - Мигрирует legacy-версии (workers без full_name -> с full_name)
    - Создает индексы только если существуют нужные колонки
    """
    conn.executescript(DDL_TABLES_SQL)

    migrate_workers_if_needed(conn)

    create_indexes_if_possible(conn)

    logger.info("Схема БД инициализирована")


# --- migrations & helpers ---

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def get_table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]  # name in 2nd column


def migrate_workers_if_needed(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "workers"):
        return
    cols = set(get_table_columns(conn, "workers"))
    if "full_name" in cols and "personnel_no" in cols:
        return  # up-to-date

    # Try to detect legacy columns
    legacy_name_col = None
    for candidate in ("name", "fio"):
        if candidate in cols:
            legacy_name_col = candidate
            break

    # Recreate table with new schema and move data
    conn.execute("ALTER TABLE workers RENAME TO workers_old")
    conn.executescript(
        """
        CREATE TABLE workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE,
            dept TEXT,
            position TEXT,
            personnel_no TEXT NOT NULL UNIQUE
        );
        """
    )

    if legacy_name_col:
        # copy with mapping
        conn.execute(
            f"""
            INSERT INTO workers(full_name, dept, position, personnel_no)
            SELECT TRIM(COALESCE({legacy_name_col}, '')) AS full_name,
                   dept,
                   position,
                   personnel_no
            FROM workers_old
            WHERE {legacy_name_col} IS NOT NULL AND TRIM({legacy_name_col}) <> ''
            """
        )
    else:
        # If no legacy name, try to build from available fields (may insert none)
        pass

    conn.execute("DROP TABLE workers_old")


def create_indexes_if_possible(conn: sqlite3.Connection) -> None:
    for idx_name, table, required_cols, create_sql in DDL_INDEXES:
        if not table_exists(conn, table):
            continue
        cols = set(get_table_columns(conn, table))
        if not set(required_cols).issubset(cols):
            logger.warning("Пропуск создания индекса %s: нет колонок %s в %s", idx_name, required_cols, table)
            continue
        try:
            conn.execute(create_sql)
        except sqlite3.OperationalError as exc:  # noqa: TRY003
            logger.warning("Не удалось создать индекс %s: %s", idx_name, exc)