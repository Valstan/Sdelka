from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Sequence

# Workers


def insert_worker(conn: sqlite3.Connection, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> int:
    sql = """
    INSERT INTO workers(full_name, dept, position, personnel_no)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(full_name) DO UPDATE SET dept=excluded.dept, position=excluded.position
    """
    cur = conn.execute(sql, (full_name, dept, position, personnel_no))
    return cur.lastrowid or cur.rowcount


def update_worker(conn: sqlite3.Connection, worker_id: int, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> None:
    conn.execute(
        "UPDATE workers SET full_name = ?, dept = ?, position = ?, personnel_no = ? WHERE id = ?",
        (full_name, dept, position, personnel_no, worker_id),
    )


def delete_worker(conn: sqlite3.Connection, worker_id: int) -> None:
    conn.execute("DELETE FROM workers WHERE id = ?", (worker_id,))


def get_worker_by_personnel_no(conn: sqlite3.Connection, personnel_no: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM workers WHERE personnel_no = ?", (personnel_no,))
    return cur.fetchone()


def get_worker_by_id(conn: sqlite3.Connection, worker_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM workers WHERE id = ?", (worker_id,)).fetchone()


def list_workers(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None) -> list[sqlite3.Row]:
    if prefix:
        like = f"{prefix}%"
        sql = "SELECT * FROM workers WHERE full_name LIKE ? ORDER BY full_name"
        params: Sequence[Any] = (like,)
    else:
        sql = "SELECT * FROM workers ORDER BY full_name"
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_workers_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{prefix}%"
    cur = conn.execute("SELECT * FROM workers WHERE full_name LIKE ? ORDER BY full_name LIMIT ?", (like, limit))
    return cur.fetchall()


# Job Types

def upsert_job_type(conn: sqlite3.Connection, name: str, unit: str, price: float) -> int:
    sql = """
    INSERT INTO job_types(name, unit, price) VALUES (?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET unit=excluded.unit, price=excluded.price
    """
    cur = conn.execute(sql, (name, unit, price))
    return cur.lastrowid or cur.rowcount


def get_job_type_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM job_types WHERE name = ?", (name,)).fetchone()


def search_job_types_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{prefix}%"
    return conn.execute("SELECT * FROM job_types WHERE name LIKE ? ORDER BY name LIMIT ?", (like, limit)).fetchall()


# Products

def upsert_product(conn: sqlite3.Connection, name: str, product_no: str) -> int:
    sql = """
    INSERT INTO products(name, product_no) VALUES (?, ?)
    ON CONFLICT(name) DO UPDATE SET product_no=excluded.product_no
    """
    cur = conn.execute(sql, (name, product_no))
    return cur.lastrowid or cur.rowcount


def get_product_by_no(conn: sqlite3.Connection, product_no: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM products WHERE product_no = ?", (product_no,)).fetchone()


def search_products_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{prefix}%"
    return conn.execute(
        "SELECT * FROM products WHERE name LIKE ? OR product_no LIKE ? ORDER BY name LIMIT ?",
        (like, like, limit),
    ).fetchall()


# Contracts

def upsert_contract(conn: sqlite3.Connection, code: str, start_date: str | None, end_date: str | None, description: str | None) -> int:
    sql = """
    INSERT INTO contracts(code, start_date, end_date, description) VALUES(?, ?, ?, ?)
    ON CONFLICT(code) DO UPDATE SET start_date=excluded.start_date, end_date=excluded.end_date, description=excluded.description
    """
    cur = conn.execute(sql, (code, start_date, end_date, description))
    return cur.lastrowid or cur.rowcount


def get_contract_by_code(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM contracts WHERE code = ?", (code,)).fetchone()


def search_contracts_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{prefix}%"
    return conn.execute("SELECT * FROM contracts WHERE code LIKE ? ORDER BY code LIMIT ?", (like, limit)).fetchall()


# Work Orders

def insert_work_order(conn: sqlite3.Connection, order_no: int, date: str, product_id: int | None, contract_id: int, total_amount: float) -> int:
    cur = conn.execute(
        "INSERT INTO work_orders(order_no, date, product_id, contract_id, total_amount) VALUES (?, ?, ?, ?, ?)",
        (order_no, date, product_id, contract_id, total_amount),
    )
    return cur.lastrowid


def update_work_order_total(conn: sqlite3.Connection, work_order_id: int, total_amount: float) -> None:
    conn.execute("UPDATE work_orders SET total_amount = ? WHERE id = ?", (total_amount, work_order_id))


def insert_work_order_item(conn: sqlite3.Connection, work_order_id: int, job_type_id: int, quantity: float, unit_price: float, line_amount: float) -> int:
    cur = conn.execute(
        """
        INSERT INTO work_order_items(work_order_id, job_type_id, quantity, unit_price, line_amount)
        VALUES (?, ?, ?, ?, ?)
        """,
        (work_order_id, job_type_id, quantity, unit_price, line_amount),
    )
    return cur.lastrowid


def set_work_order_workers(conn: sqlite3.Connection, work_order_id: int, worker_ids: Sequence[int]) -> None:
    conn.execute("DELETE FROM work_order_workers WHERE work_order_id = ?", (work_order_id,))
    conn.executemany(
        "INSERT INTO work_order_workers(work_order_id, worker_id) VALUES (?, ?)",
        [(work_order_id, wid) for wid in worker_ids],
    )


def next_order_no(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(order_no), 0) + 1 AS next_no FROM work_orders").fetchone()
    return int(row["next_no"]) if row else 1


def fetch_work_orders(conn: sqlite3.Connection, where_sql: str = "", params: Sequence[Any] | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM work_orders " + (f"WHERE {where_sql} " if where_sql else "") + "ORDER BY date DESC, order_no DESC"
    return conn.execute(sql, params or []).fetchall()