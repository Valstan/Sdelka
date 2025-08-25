from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Sequence

from utils.text import normalize_for_search

# Workers


def insert_worker(conn: sqlite3.Connection, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> int:
    sql = """
    INSERT INTO workers(full_name, full_name_norm, dept, dept_norm, position, position_norm, personnel_no, personnel_no_norm)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.execute(sql, (
        full_name,
        normalize_for_search(full_name),
        dept,
        normalize_for_search(dept),
        position,
        normalize_for_search(position),
        personnel_no,
        normalize_for_search(personnel_no),
    ))
    return cur.lastrowid or cur.rowcount


def update_worker(conn: sqlite3.Connection, worker_id: int, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> None:
    conn.execute(
        "UPDATE workers SET full_name = ?, full_name_norm=?, dept = ?, dept_norm=?, position = ?, position_norm=?, personnel_no = ?, personnel_no_norm=? WHERE id = ?",
        (
            full_name,
            normalize_for_search(full_name),
            dept,
            normalize_for_search(dept),
            position,
            normalize_for_search(position),
            personnel_no,
            normalize_for_search(personnel_no),
            worker_id,
        ),
    )


def delete_worker(conn: sqlite3.Connection, worker_id: int) -> None:
    conn.execute("DELETE FROM workers WHERE id = ?", (worker_id,))


def get_worker_by_personnel_no(conn: sqlite3.Connection, personnel_no: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM workers WHERE personnel_no_norm = ?", (normalize_for_search(personnel_no),))
    return cur.fetchone()


def get_worker_by_full_name(conn: sqlite3.Connection, full_name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM workers WHERE full_name_norm = ?", (normalize_for_search(full_name),)).fetchone()


def get_worker_by_id(conn: sqlite3.Connection, worker_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM workers WHERE id = ?", (worker_id,)).fetchone()


def list_workers(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None) -> list[sqlite3.Row]:
    if prefix:
        like = f"{normalize_for_search(prefix)}%"
        sql = "SELECT * FROM workers WHERE full_name_norm LIKE ? ORDER BY full_name"
        params: Sequence[Any] = (like,)
    else:
        sql = "SELECT * FROM workers ORDER BY full_name"
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_workers_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    cur = conn.execute("SELECT * FROM workers WHERE full_name_norm LIKE ? ORDER BY full_name LIMIT ?", (like, limit))
    return cur.fetchall()


def distinct_depts_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute("SELECT DISTINCT dept FROM workers WHERE dept_norm LIKE ? ORDER BY dept LIMIT ?", (like, limit)).fetchall()
    return [r[0] for r in rows if r[0]]


def distinct_positions_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute("SELECT DISTINCT position FROM workers WHERE position_norm LIKE ? ORDER BY position LIMIT ?", (like, limit)).fetchall()
    return [r[0] for r in rows if r[0]]


def personnel_numbers_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute("SELECT personnel_no FROM workers WHERE personnel_no_norm LIKE ? ORDER BY personnel_no LIMIT ?", (like, limit)).fetchall()
    return [r[0] for r in rows if r[0]]


# Job Types

def insert_job_type(conn: sqlite3.Connection, name: str, unit: str, price: float) -> int:
    cur = conn.execute("INSERT INTO job_types(name, name_norm, unit, unit_norm, price) VALUES (?, ?, ?, ?, ?)", (name, normalize_for_search(name), unit, normalize_for_search(unit), price))
    return cur.lastrowid or cur.rowcount


def update_job_type(conn: sqlite3.Connection, job_type_id: int, name: str, unit: str, price: float) -> None:
    conn.execute("UPDATE job_types SET name = ?, name_norm=?, unit = ?, unit_norm=?, price = ? WHERE id = ?", (name, normalize_for_search(name), unit, normalize_for_search(unit), price, job_type_id))


def delete_job_type(conn: sqlite3.Connection, job_type_id: int) -> None:
    conn.execute("DELETE FROM job_types WHERE id = ?", (job_type_id,))


def upsert_job_type(conn: sqlite3.Connection, name: str, unit: str, price: float) -> int:
    sql = """
    INSERT INTO job_types(name, name_norm, unit, unit_norm, price) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET unit=excluded.unit, unit_norm=excluded.unit_norm, price=excluded.price
    """
    cur = conn.execute(sql, (name, normalize_for_search(name), unit, normalize_for_search(unit), price))
    return cur.lastrowid or cur.rowcount


def get_job_type_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM job_types WHERE name_norm = ?", (normalize_for_search(name),)).fetchone()


def list_job_types(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None) -> list[sqlite3.Row]:
    if prefix:
        like = f"{normalize_for_search(prefix)}%"
        sql = "SELECT * FROM job_types WHERE name_norm LIKE ? ORDER BY name"
        params: Sequence[Any] = (like,)
    else:
        sql = "SELECT * FROM job_types ORDER BY name"
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_job_types_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute("SELECT * FROM job_types WHERE name_norm LIKE ? ORDER BY name LIMIT ?", (like, limit)).fetchall()


def distinct_units_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute("SELECT DISTINCT unit FROM job_types WHERE unit_norm LIKE ? ORDER BY unit LIMIT ?", (like, limit)).fetchall()
    return [r[0] for r in rows if r[0]]


# Products

def insert_product(conn: sqlite3.Connection, name: str, product_no: str) -> int:
    cur = conn.execute("INSERT INTO products(name, name_norm, product_no, product_no_norm) VALUES (?, ?, ?, ?)", (name, normalize_for_search(name), product_no, normalize_for_search(product_no)))
    return cur.lastrowid or cur.rowcount


def update_product(conn: sqlite3.Connection, product_id: int, name: str, product_no: str) -> None:
    conn.execute("UPDATE products SET name = ?, name_norm=?, product_no = ?, product_no_norm=? WHERE id = ?", (name, normalize_for_search(name), product_no, normalize_for_search(product_no), product_id))


def delete_product(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def upsert_product(conn: sqlite3.Connection, name: str, product_no: str) -> int:
    sql = """
    INSERT INTO products(name, name_norm, product_no, product_no_norm) VALUES (?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET product_no=excluded.product_no, product_no_norm=excluded.product_no_norm
    """
    cur = conn.execute(sql, (name, normalize_for_search(name), product_no, normalize_for_search(product_no)))
    return cur.lastrowid or cur.rowcount


def get_product_by_no(conn: sqlite3.Connection, product_no: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM products WHERE product_no_norm = ?", (normalize_for_search(product_no),)).fetchone()


def get_product_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM products WHERE name_norm = ?", (normalize_for_search(name),)).fetchone()


def list_products(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None) -> list[sqlite3.Row]:
    if prefix:
        like = f"{normalize_for_search(prefix)}%"
        sql = "SELECT * FROM products WHERE name_norm LIKE ? OR product_no_norm LIKE ? ORDER BY name"
        params: Sequence[Any] = (like, like)
    else:
        sql = "SELECT * FROM products ORDER BY name"
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_products_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute(
        "SELECT * FROM products WHERE name_norm LIKE ? OR product_no_norm LIKE ? ORDER BY name LIMIT ?",
        (like, like, limit),
    ).fetchall()


# Contracts

def insert_contract(conn: sqlite3.Connection, code: str, start_date: str | None, end_date: str | None, description: str | None) -> int:
    cur = conn.execute("INSERT INTO contracts(code, code_norm, start_date, end_date, description) VALUES (?, ?, ?, ?, ?)", (code, normalize_for_search(code), start_date, end_date, description))
    return cur.lastrowid or cur.rowcount


def update_contract(conn: sqlite3.Connection, contract_id: int, code: str, start_date: str | None, end_date: str | None, description: str | None) -> None:
    conn.execute("UPDATE contracts SET code = ?, code_norm=?, start_date = ?, end_date = ?, description = ? WHERE id = ?", (code, normalize_for_search(code), start_date, end_date, description, contract_id))


def delete_contract(conn: sqlite3.Connection, contract_id: int) -> None:
    conn.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))


def upsert_contract(conn: sqlite3.Connection, code: str, start_date: str | None, end_date: str | None, description: str | None) -> int:
    sql = """
    INSERT INTO contracts(code, code_norm, start_date, end_date, description) VALUES(?, ?, ?, ?, ?)
    ON CONFLICT(code) DO UPDATE SET start_date=excluded.start_date, end_date=excluded.end_date, description=excluded.description
    """
    cur = conn.execute(sql, (code, normalize_for_search(code), start_date, end_date, description))
    return cur.lastrowid or cur.rowcount


def get_contract_by_code(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM contracts WHERE code_norm = ?", (normalize_for_search(code),)).fetchone()


def list_contracts(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None) -> list[sqlite3.Row]:
    if prefix:
        like = f"{normalize_for_search(prefix)}%"
        sql = "SELECT * FROM contracts WHERE code_norm LIKE ? ORDER BY code"
        params: Sequence[Any] = (like,)
    else:
        sql = "SELECT * FROM contracts ORDER BY code"
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_contracts_by_prefix(conn: sqlite3.Connection, prefix: str, limit: int) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute("SELECT * FROM contracts WHERE code_norm LIKE ? ORDER BY code LIMIT ?", (like, limit)).fetchall()


# Work Orders

def insert_work_order(conn: sqlite3.Connection, order_no: int, date: str, product_id: int | None, contract_id: int, total_amount: float) -> int:
    cur = conn.execute(
        "INSERT INTO work_orders(order_no, date, product_id, contract_id, total_amount) VALUES (?, ?, ?, ?, ?)",
        (order_no, date, product_id, contract_id, total_amount),
    )
    return cur.lastrowid


def update_work_order_header(conn: sqlite3.Connection, work_order_id: int, date: str, product_id: int | None, contract_id: int, total_amount: float) -> None:
    conn.execute(
        "UPDATE work_orders SET date=?, product_id=?, contract_id=?, total_amount=? WHERE id=?",
        (date, product_id, contract_id, total_amount, work_order_id),
    )


def delete_work_order_items(conn: sqlite3.Connection, work_order_id: int) -> None:
    conn.execute("DELETE FROM work_order_items WHERE work_order_id = ?", (work_order_id,))


def delete_work_order(conn: sqlite3.Connection, work_order_id: int) -> None:
    conn.execute("DELETE FROM work_orders WHERE id = ?", (work_order_id,))


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
    """Backward-compatible setter without amounts: inserts with amount=0.

    Use set_work_order_workers_with_amounts for precise allocation.
    """
    conn.execute("DELETE FROM work_order_workers WHERE work_order_id = ?", (work_order_id,))
    conn.executemany(
        "INSERT INTO work_order_workers(work_order_id, worker_id, amount) VALUES (?, ?, 0)",
        [(work_order_id, wid) for wid in worker_ids],
    )


def set_work_order_workers_with_amounts(conn: sqlite3.Connection, work_order_id: int, allocations: Sequence[tuple[int, float]]) -> None:
    """Set workers with their allocated amounts.

    allocations: sequence of (worker_id, amount)
    """
    conn.execute("DELETE FROM work_order_workers WHERE work_order_id = ?", (work_order_id,))
    conn.executemany(
        "INSERT INTO work_order_workers(work_order_id, worker_id, amount) VALUES (?, ?, ?)",
        [(work_order_id, wid, float(amount)) for (wid, amount) in allocations],
    )


def next_order_no(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(order_no), 0) + 1 AS next_no FROM work_orders").fetchone()
    return int(row["next_no"]) if row else 1


def fetch_work_orders(conn: sqlite3.Connection, where_sql: str = "", params: Sequence[Any] | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM work_orders " + (f"WHERE {where_sql} " if where_sql else "") + "ORDER BY date DESC, order_no DESC"
    return conn.execute(sql, params or []).fetchall()


def get_work_order_header(conn: sqlite3.Connection, work_order_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT wo.*, c.code AS contract_code, p.name AS product_name, p.product_no AS product_no
        FROM work_orders wo
        LEFT JOIN contracts c ON c.id = wo.contract_id
        LEFT JOIN products p ON p.id = wo.product_id
        WHERE wo.id = ?
        """,
        (work_order_id,),
    ).fetchone()


def get_work_order_items(conn: sqlite3.Connection, work_order_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT woi.*, jt.name AS job_name
        FROM work_order_items woi
        JOIN job_types jt ON jt.id = woi.job_type_id
        WHERE woi.work_order_id = ?
        ORDER BY woi.id
        """,
        (work_order_id,),
    ).fetchall()


def get_work_order_workers(conn: sqlite3.Connection, work_order_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT wow.worker_id, w.full_name, COALESCE(wow.amount, 0) AS amount
        FROM work_order_workers wow
        JOIN workers w ON w.id = wow.worker_id
        WHERE wow.work_order_id = ?
        ORDER BY w.full_name
        """,
        (work_order_id,),
    ).fetchall()