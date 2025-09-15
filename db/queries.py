from __future__ import annotations

import sqlite3
from typing import Any, Sequence

from utils.text import normalize_for_search

import logging

# --- Helpers for contracts/products linkage ---


def get_or_create_contract_by_code(conn: sqlite3.Connection, code: str) -> int:
    row = get_contract_by_code(conn, code)
    if row:
        return int(row["id"])  # type: ignore[index]
    upsert_contract(conn, code, None, None, None)
    row2 = get_contract_by_code(conn, code)
    if not row2:
        raise sqlite3.IntegrityError("Не удалось создать контракт: " + code)
    return int(row2["id"])  # type: ignore[index]


def get_or_create_default_contract(conn: sqlite3.Connection) -> int:
    return get_or_create_contract_by_code(conn, "Без контракта")


def set_product_contract(
    conn: sqlite3.Connection, product_id: int, contract_id: int
) -> None:
    conn.execute(
        "UPDATE products SET contract_id=? WHERE id=?", (contract_id, product_id)
    )


# Workers


def insert_worker(
    conn: sqlite3.Connection,
    full_name: str,
    dept: str | None,
    position: str | None,
    personnel_no: str,
    status: str | None = None,
) -> int:
    status_val = status or "Работает"
    sql = """
    INSERT INTO workers(full_name, full_name_norm, dept, dept_norm, position, position_norm, personnel_no, personnel_no_norm, status, status_norm)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.execute(
        sql,
        (
            full_name,
            normalize_for_search(full_name),
            dept,
            normalize_for_search(dept),
            position,
            normalize_for_search(position),
            personnel_no,
            normalize_for_search(personnel_no),
            status_val,
            normalize_for_search(status_val),
        ),
    )
    return cur.lastrowid or cur.rowcount


def upsert_worker(
    conn: sqlite3.Connection,
    full_name: str,
    dept: str | None,
    position: str | None,
    personnel_no: str,
    status: str | None = None,
) -> int:
    """Insert worker or update existing one to avoid import crashes.

    Prefers matching by personnel number. If insert conflicts, updates the existing row.
    Tries to update full_name as well; on unique-name conflict, falls back to keeping old name.
    Returns 1 on insert/update success, 0 otherwise.
    """
    try:
        return insert_worker(conn, full_name, dept, position, personnel_no, status) or 0
    except sqlite3.IntegrityError:
        # Try by personnel_no first
        existing = get_worker_by_personnel_no(conn, personnel_no)
        if existing:
            try:
                update_worker(
                    conn,
                    existing["id"],
                    full_name,
                    dept,
                    position,
                    personnel_no,
                    status,
                )
            except sqlite3.IntegrityError:
                # Keep existing name if new name collides
                update_worker(
                    conn,
                    existing["id"],
                    existing["full_name"],
                    dept,
                    position,
                    personnel_no,
                    status,
                )
            return 1
        # Fallback: match by full_name
        existing = get_worker_by_full_name(conn, full_name)
        if existing:
            try:
                update_worker(
                    conn,
                    existing["id"],
                    full_name,
                    dept,
                    position,
                    personnel_no,
                    status,
                )
            except sqlite3.IntegrityError:
                # Keep existing personnel_no if new one collides
                update_worker(conn, existing["id"], full_name, dept, position, existing["personnel_no"], status)  # type: ignore[index]
            return 1
        return 0


def update_worker(
    conn: sqlite3.Connection,
    worker_id: int,
    full_name: str,
    dept: str | None,
    position: str | None,
    personnel_no: str,
    status: str | None = None,
) -> None:
    if status is None:
        row = conn.execute(
            "SELECT status FROM workers WHERE id=?", (worker_id,)
        ).fetchone()
        status = (
            (row["status"] if row and row["status"] else "Работает")
            if row is not None
            else "Работает"
        )
    conn.execute(
        "UPDATE workers SET full_name = ?, full_name_norm=?, dept = ?, dept_norm=?, position = ?, position_norm=?, personnel_no = ?, personnel_no_norm=?, status = ?, status_norm=? WHERE id = ?",
        (
            full_name,
            normalize_for_search(full_name),
            dept,
            normalize_for_search(dept),
            position,
            normalize_for_search(position),
            personnel_no,
            normalize_for_search(personnel_no),
            status,
            normalize_for_search(status),
            worker_id,
        ),
    )


def delete_worker(conn: sqlite3.Connection, worker_id: int) -> None:
    # Проверяем, используется ли работник в других таблицах
    # Пока что в схеме нет связи работников с нарядами, поэтому просто удаляем
    conn.execute("DELETE FROM workers WHERE id = ?", (worker_id,))


def get_worker_by_personnel_no(
    conn: sqlite3.Connection, personnel_no: str
) -> sqlite3.Row | None:
    cur = conn.execute(
        "SELECT * FROM workers WHERE personnel_no_norm = ?",
        (normalize_for_search(personnel_no),),
    )
    return cur.fetchone()


def get_worker_by_full_name(
    conn: sqlite3.Connection, full_name: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM workers WHERE full_name_norm = ?",
        (normalize_for_search(full_name),),
    ).fetchone()


def get_worker_by_id(conn: sqlite3.Connection, worker_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM workers WHERE id = ?", (worker_id,)).fetchone()


def list_workers(
    conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None
) -> list[sqlite3.Row]:
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


def search_workers_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    cur = conn.execute(
        "SELECT * FROM workers WHERE full_name_norm LIKE ? ORDER BY full_name LIMIT ?",
        (like, limit),
    )
    return cur.fetchall()


def search_workers_by_substring(
    conn: sqlite3.Connection, term: str, limit: int
) -> list[sqlite3.Row]:
    like = f"%{normalize_for_search(term)}%"
    return conn.execute(
        "SELECT * FROM workers WHERE full_name_norm LIKE ? ORDER BY full_name LIMIT ?",
        (like, limit),
    ).fetchall()


def distinct_depts_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute(
        "SELECT DISTINCT dept FROM workers WHERE dept_norm LIKE ? ORDER BY dept LIMIT ?",
        (like, limit),
    ).fetchall()
    return [r[0] for r in rows if r[0]]


def distinct_positions_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute(
        "SELECT DISTINCT position FROM workers WHERE position_norm LIKE ? ORDER BY position LIMIT ?",
        (like, limit),
    ).fetchall()
    return [r[0] for r in rows if r[0]]


def personnel_numbers_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute(
        "SELECT personnel_no FROM workers WHERE personnel_no_norm LIKE ? ORDER BY personnel_no LIMIT ?",
        (like, limit),
    ).fetchall()
    return [r[0] for r in rows if r[0]]


# Job Types


def insert_job_type(
    conn: sqlite3.Connection, name: str, unit: str, price: float
) -> int:
    cur = conn.execute(
        "INSERT INTO job_types(name, name_norm, unit, unit_norm, price) VALUES (?, ?, ?, ?, ?)",
        (name, normalize_for_search(name), unit, normalize_for_search(unit), price),
    )
    return cur.lastrowid or cur.rowcount


def update_job_type(
    conn: sqlite3.Connection, job_type_id: int, name: str, unit: str, price: float
) -> None:
    conn.execute(
        "UPDATE job_types SET name = ?, name_norm=?, unit = ?, unit_norm=?, price = ? WHERE id = ?",
        (
            name,
            normalize_for_search(name),
            unit,
            normalize_for_search(unit),
            price,
            job_type_id,
        ),
    )


def delete_job_type(conn: sqlite3.Connection, job_type_id: int) -> None:
    # Проверяем, используется ли тип работ в других таблицах
    cur = conn.execute(
        """
        SELECT COUNT(*) FROM work_order_items 
        WHERE job_type_id = ?
    """,
        (job_type_id,),
    )
    count = cur.fetchone()[0]
    if count > 0:
        raise ValueError(
            f"Нельзя удалить тип работ: он используется в {count} позициях нарядов"
        )

    conn.execute("DELETE FROM job_types WHERE id = ?", (job_type_id,))


def upsert_job_type(
    conn: sqlite3.Connection, name: str, unit: str, price: float
) -> int:
    sql = """
    INSERT INTO job_types(name, name_norm, unit, unit_norm, price) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET unit=excluded.unit, unit_norm=excluded.unit_norm, price=excluded.price
    """
    cur = conn.execute(
        sql, (name, normalize_for_search(name), unit, normalize_for_search(unit), price)
    )
    return cur.lastrowid or cur.rowcount


def get_job_type_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM job_types WHERE name_norm = ?", (normalize_for_search(name),)
    ).fetchone()


def list_job_types(
    conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None
) -> list[sqlite3.Row]:
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


def search_job_types_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute(
        "SELECT * FROM job_types WHERE name_norm LIKE ? ORDER BY name LIMIT ?",
        (like, limit),
    ).fetchall()


def search_job_types_by_substring(
    conn: sqlite3.Connection, term: str, limit: int
) -> list[sqlite3.Row]:
    """Search job types by substring (anywhere in the name, case-insensitive)."""
    like = f"%{normalize_for_search(term)}%"
    return conn.execute(
        "SELECT * FROM job_types WHERE name_norm LIKE ? ORDER BY name LIMIT ?",
        (like, limit),
    ).fetchall()


def distinct_units_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[str]:
    like = f"{normalize_for_search(prefix)}%"
    rows = conn.execute(
        "SELECT DISTINCT unit FROM job_types WHERE unit_norm LIKE ? ORDER BY unit LIMIT ?",
        (like, limit),
    ).fetchall()
    return [r[0] for r in rows if r[0]]


# Products


def insert_product(
    conn: sqlite3.Connection, name: str, product_no: str, contract_id: int | None = None
) -> int:
    cur = conn.execute(
        "INSERT INTO products(name, name_norm, product_no, product_no_norm, contract_id) VALUES (?, ?, ?, ?, ?)",
        (
            name,
            normalize_for_search(name),
            product_no,
            normalize_for_search(product_no),
            contract_id,
        ),
    )
    return cur.lastrowid or cur.rowcount


def update_product(
    conn: sqlite3.Connection,
    product_id: int,
    name: str,
    product_no: str,
    contract_id: int | None = None,
) -> None:
    conn.execute(
        "UPDATE products SET name = ?, name_norm=?, product_no = ?, product_no_norm=?, contract_id=? WHERE id = ?",
        (
            name,
            normalize_for_search(name),
            product_no,
            normalize_for_search(product_no),
            contract_id,
            product_id,
        ),
    )


def delete_product(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def upsert_product(
    conn: sqlite3.Connection, name: str, product_no: str, contract_id: int | None = None
) -> int:
    sql = """
    INSERT INTO products(name, name_norm, product_no, product_no_norm, contract_id) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(product_no) DO UPDATE SET name=excluded.name, name_norm=excluded.name_norm, contract_id=COALESCE(excluded.contract_id, products.contract_id)
    """
    cur = conn.execute(
        sql,
        (
            name,
            normalize_for_search(name),
            product_no,
            normalize_for_search(product_no),
            contract_id,
        ),
    )
    return cur.lastrowid or cur.rowcount


def get_product(conn: sqlite3.Connection, product_id: int) -> sqlite3.Row | None:
    """Получает изделие по ID"""
    return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def get_product_by_no(conn: sqlite3.Connection, product_no: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM products WHERE product_no_norm = ?",
        (normalize_for_search(product_no),),
    ).fetchone()


def get_product_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM products WHERE name_norm = ?", (normalize_for_search(name),)
    ).fetchone()


def list_products(
    conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None
) -> list[sqlite3.Row]:
    if prefix:
        like = f"{normalize_for_search(prefix)}%"
        sql = (
            "SELECT p.*, c.code AS contract_code FROM products p "
            "LEFT JOIN contracts c ON c.id = p.contract_id "
            "WHERE p.name_norm LIKE ? OR p.product_no_norm LIKE ? ORDER BY p.name"
        )
        params: Sequence[Any] = (like, like)
    else:
        sql = (
            "SELECT p.*, c.code AS contract_code FROM products p "
            "LEFT JOIN contracts c ON c.id = p.contract_id "
            "ORDER BY p.name"
        )
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def search_products_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute(
        "SELECT p.*, c.code AS contract_code FROM products p LEFT JOIN contracts c ON c.id = p.contract_id WHERE p.name_norm LIKE ? OR p.product_no_norm LIKE ? ORDER BY p.name LIMIT ?",
        (like, like, limit),
    ).fetchall()


def search_products_by_substring(
    conn: sqlite3.Connection, term: str, limit: int
) -> list[sqlite3.Row]:
    like = f"%{normalize_for_search(term)}%"
    return conn.execute(
        "SELECT p.*, c.code AS contract_code FROM products p LEFT JOIN contracts c ON c.id = p.contract_id WHERE p.name_norm LIKE ? OR p.product_no_norm LIKE ? ORDER BY p.name LIMIT ?",
        (like, like, limit),
    ).fetchall()


# Contracts


def insert_contract(
    conn: sqlite3.Connection,
    code: str,
    start_date: str | None,
    end_date: str | None,
    description: str | None,
    name: str | None = None,
    contract_type: str | None = None,
    executor: str | None = None,
    igk: str | None = None,
    contract_number: str | None = None,
    bank_account: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO contracts(code, code_norm, name, name_norm, contract_type, contract_type_norm, executor, executor_norm, igk, contract_number, bank_account, start_date, end_date, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            code,
            normalize_for_search(code),
            name,
            normalize_for_search(name) if name else None,
            contract_type,
            normalize_for_search(contract_type) if contract_type else None,
            executor,
            normalize_for_search(executor) if executor else None,
            igk,
            contract_number,
            bank_account,
            start_date,
            end_date,
            description,
        ),
    )
    return cur.lastrowid or cur.rowcount


def update_contract(
    conn: sqlite3.Connection,
    contract_id: int,
    code: str,
    start_date: str | None,
    end_date: str | None,
    description: str | None,
    name: str | None = None,
    contract_type: str | None = None,
    executor: str | None = None,
    igk: str | None = None,
    contract_number: str | None = None,
    bank_account: str | None = None,
) -> None:
    conn.execute(
        "UPDATE contracts SET code = ?, code_norm=?, name = ?, name_norm=?, contract_type = ?, contract_type_norm=?, executor = ?, executor_norm=?, igk = ?, contract_number = ?, bank_account = ?, start_date = ?, end_date = ?, description = ? WHERE id = ?",
        (
            code,
            normalize_for_search(code),
            name,
            normalize_for_search(name) if name else None,
            contract_type,
            normalize_for_search(contract_type) if contract_type else None,
            executor,
            normalize_for_search(executor) if executor else None,
            igk,
            contract_number,
            bank_account,
            start_date,
            end_date,
            description,
            contract_id,
        ),
    )


def delete_contract(conn: sqlite3.Connection, contract_id: int) -> None:
    conn.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))


def upsert_contract(
    conn: sqlite3.Connection,
    code: str,
    start_date: str | None,
    end_date: str | None,
    description: str | None,
    name: str | None = None,
    contract_type: str | None = None,
    executor: str | None = None,
    igk: str | None = None,
    contract_number: str | None = None,
    bank_account: str | None = None,
) -> int:
    # Save history snapshot when updating existing contract
    existing = get_contract_by_code(conn, code)
    sql = """
    INSERT INTO contracts(code, code_norm, name, name_norm, contract_type, contract_type_norm, executor, executor_norm, igk, contract_number, bank_account, start_date, end_date, description) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(code) DO UPDATE SET 
        name=excluded.name, name_norm=excluded.name_norm,
        contract_type=excluded.contract_type, contract_type_norm=excluded.contract_type_norm,
        executor=excluded.executor, executor_norm=excluded.executor_norm,
        igk=excluded.igk, contract_number=excluded.contract_number, bank_account=excluded.bank_account,
        start_date=excluded.start_date, end_date=excluded.end_date, description=excluded.description
    """
    # If will update existing, snapshot the previous state BEFORE update
    if existing:
        prev = existing
        if prev:
            conn.execute(
                """
                INSERT INTO contract_history(contract_id, code, name, contract_type, executor, igk, contract_number, bank_account, start_date, end_date, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(prev["id"]),  # type: ignore[index]
                    prev["code"],
                    prev["name"],
                    prev["contract_type"],
                    prev["executor"],
                    prev["igk"],
                    prev["contract_number"],
                    prev["bank_account"],
                    prev["start_date"],
                    prev["end_date"],
                    prev["description"],
                ),
            )
    cur = conn.execute(
        sql,
        (
            code,
            normalize_for_search(code),
            name,
            normalize_for_search(name) if name else None,
            contract_type,
            normalize_for_search(contract_type) if contract_type else None,
            executor,
            normalize_for_search(executor) if executor else None,
            igk,
            contract_number,
            bank_account,
            start_date,
            end_date,
            description,
        ),
    )
    return cur.lastrowid or cur.rowcount


def get_contract_by_code(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM contracts WHERE code_norm = ?", (normalize_for_search(code),)
    ).fetchone()


def get_contract_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM contracts WHERE name_norm = ?", (normalize_for_search(name),)
    ).fetchone()


def list_contracts(
    conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None
) -> list[sqlite3.Row]:
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


def search_contracts_by_prefix(
    conn: sqlite3.Connection, prefix: str, limit: int
) -> list[sqlite3.Row]:
    like = f"{normalize_for_search(prefix)}%"
    return conn.execute(
        "SELECT * FROM contracts WHERE code_norm LIKE ? ORDER BY code LIMIT ?",
        (like, limit),
    ).fetchall()


def search_contracts_by_substring(
    conn: sqlite3.Connection, term: str, limit: int
) -> list[sqlite3.Row]:
    like = f"%{normalize_for_search(term)}%"
    return conn.execute(
        "SELECT * FROM contracts WHERE code_norm LIKE ? OR name_norm LIKE ? OR contract_type_norm LIKE ? OR executor_norm LIKE ? ORDER BY code LIMIT ?",
        (like, like, like, like, limit),
    ).fetchall()


# Work Orders


def insert_work_order(
    conn: sqlite3.Connection,
    order_no: int,
    date: str,
    contract_id: int | None,
    total_amount: float,
) -> int:
    cur = conn.execute(
        "INSERT INTO work_orders(order_no, date, contract_id, total_amount) VALUES (?, ?, ?, ?)",
        (order_no, date, contract_id, total_amount),
    )
    return cur.lastrowid


def update_work_order_header(
    conn: sqlite3.Connection,
    work_order_id: int,
    order_no: int,
    date: str,
    contract_id: int | None,
    total_amount: float,
) -> None:
    conn.execute(
        "UPDATE work_orders SET order_no=?, date=?, contract_id=?, total_amount=? WHERE id=?",
        (order_no, date, contract_id, total_amount, work_order_id),
    )


def delete_work_order_items(conn: sqlite3.Connection, work_order_id: int) -> None:
    conn.execute(
        "DELETE FROM work_order_items WHERE work_order_id = ?", (work_order_id,)
    )


def delete_work_order(conn: sqlite3.Connection, work_order_id: int) -> None:
    conn.execute("DELETE FROM work_orders WHERE id = ?", (work_order_id,))


def update_work_order_total(
    conn: sqlite3.Connection, work_order_id: int, total_amount: float
) -> None:
    conn.execute(
        "UPDATE work_orders SET total_amount = ? WHERE id = ?",
        (total_amount, work_order_id),
    )


def insert_work_order_item(
    conn: sqlite3.Connection,
    work_order_id: int,
    job_type_id: int,
    quantity: float,
    unit_price: float,
    line_amount: float,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO work_order_items(work_order_id, job_type_id, quantity, unit_price, line_amount)
        VALUES (?, ?, ?, ?, ?)
        """,
        (work_order_id, job_type_id, quantity, unit_price, line_amount),
    )
    return cur.lastrowid


def set_work_order_workers(
    conn: sqlite3.Connection, work_order_id: int, worker_ids: Sequence[int]
) -> None:
    """Backward-compatible setter without amounts: inserts with amount=0.

    Use set_work_order_workers_with_amounts for precise allocation.
    """
    conn.execute(
        "DELETE FROM work_order_workers WHERE work_order_id = ?", (work_order_id,)
    )
    conn.executemany(
        "INSERT INTO work_order_workers(work_order_id, worker_id, amount) VALUES (?, ?, 0)",
        [(work_order_id, wid) for wid in worker_ids],
    )


def set_work_order_workers_with_amounts(
    conn: sqlite3.Connection,
    work_order_id: int,
    allocations: Sequence[tuple[int, float]],
) -> None:
    """Set workers with their allocated amounts.

    allocations: sequence of (worker_id, amount)
    """
    conn.execute(
        "DELETE FROM work_order_workers WHERE work_order_id = ?", (work_order_id,)
    )
    conn.executemany(
        "INSERT INTO work_order_workers(work_order_id, worker_id, amount) VALUES (?, ?, ?)",
        [(work_order_id, wid, float(amount)) for (wid, amount) in allocations],
    )


def next_order_no(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(order_no), 0) + 1 AS next_no FROM work_orders"
    ).fetchone()
    return int(row["next_no"]) if row else 1


def order_no_in_use(
    conn: sqlite3.Connection, order_no: int, exclude_id: int | None = None
) -> bool:
    if exclude_id is not None:
        row = conn.execute(
            "SELECT 1 FROM work_orders WHERE order_no=? AND id<>?",
            (order_no, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM work_orders WHERE order_no=?", (order_no,)
        ).fetchone()
    return bool(row)


def fetch_work_orders(
    conn: sqlite3.Connection, where_sql: str = "", params: Sequence[Any] | None = None
) -> list[sqlite3.Row]:
    sql = (
        "SELECT * FROM work_orders "
        + (f"WHERE {where_sql} " if where_sql else "")
        + "ORDER BY date DESC, order_no DESC"
    )
    return conn.execute(sql, params or []).fetchall()


def get_work_order_header(
    conn: sqlite3.Connection, work_order_id: int
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT wo.*, c.code AS contract_code, c.name AS contract_name
        FROM work_orders wo
        LEFT JOIN contracts c ON c.id = wo.contract_id
        WHERE wo.id = ?
        """,
        (work_order_id,),
    ).fetchone()


def get_work_order_items(
    conn: sqlite3.Connection, work_order_id: int
) -> list[sqlite3.Row]:
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


def get_work_order_workers(
    conn: sqlite3.Connection, work_order_id: int
) -> list[sqlite3.Row]:
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


# --- Work order contracts/products (many-to-one helpers) ---


def set_work_order_products(
    conn: sqlite3.Connection, work_order_id: int, product_ids: Sequence[int]
) -> None:
    conn.execute(
        "DELETE FROM work_order_products WHERE work_order_id = ?", (work_order_id,)
    )
    unique: list[int] = []
    for pid in product_ids:
        try:
            pid_int = int(pid)
        except Exception:
            continue
        if pid_int not in unique:
            unique.append(pid_int)
    if unique:
        conn.executemany(
            "INSERT INTO work_order_products(work_order_id, product_id) VALUES (?, ?)",
            [(work_order_id, pid) for pid in unique],
        )


def get_work_order_product_ids(
    conn: sqlite3.Connection, work_order_id: int
) -> list[int]:
    rows = conn.execute(
        "SELECT product_id FROM work_order_products WHERE work_order_id = ? ORDER BY product_id",
        (work_order_id,),
    ).fetchall()
    result: list[int] = []
    for r in rows:
        try:
            result.append(int(r["product_id"]))
        except Exception:
            try:
                result.append(int(r[0]))
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
    return result


def get_work_order_products(
    conn: sqlite3.Connection, work_order_id: int
) -> list[sqlite3.Row]:
    """Получает изделия наряда с информацией о контрактах"""
    return conn.execute(
        """
        SELECT p.id, p.name, p.product_no, p.contract_id, c.code AS contract_code, c.name AS contract_name
        FROM work_order_products wop
        JOIN products p ON p.id = wop.product_id
        LEFT JOIN contracts c ON c.id = p.contract_id
        WHERE wop.work_order_id = ?
        ORDER BY p.name
        """,
        (work_order_id,),
    ).fetchall()


def get_contract_from_products(
    conn: sqlite3.Connection, product_ids: list[int]
) -> int | None:
    """Получает контракт, который связан со всеми указанными изделиями"""
    if not product_ids:
        return None

    # Проверяем, есть ли общий контракт для всех изделий
    placeholders = ",".join("?" * len(product_ids))
    rows = conn.execute(
        f"""
        SELECT contract_id, COUNT(*) as count
        FROM products 
        WHERE id IN ({placeholders}) AND contract_id IS NOT NULL
        GROUP BY contract_id
        HAVING count = ?
        """,
        product_ids + [len(product_ids)],
    ).fetchall()

    if rows and len(rows) == 1:
        return rows[0]["contract_id"]

    return None
