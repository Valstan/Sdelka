from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)


SCHEMA_SQL = r"""
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

CREATE INDEX IF NOT EXISTS idx_workers_full_name ON workers(full_name);
CREATE INDEX IF NOT EXISTS idx_job_types_name ON job_types(name);
CREATE INDEX IF NOT EXISTS idx_products_name_no ON products(name, product_no);
CREATE INDEX IF NOT EXISTS idx_contracts_code ON contracts(code);
CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date);
"""


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    logger.info("Схема БД инициализирована")