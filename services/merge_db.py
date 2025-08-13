from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from config.settings import CONFIG
from db.sqlite import get_connection
from db import queries as q


def _row_factory(cursor, row):
    return {d[0]: row[idx] for idx, d in enumerate(cursor.description)}


def merge_from_file(target_db_path: Path | str, source_db_path: Path | str) -> tuple[int, int]:
    """Merge source DB into target DB.

    Returns tuple: (num_reference_upserts, num_orders_merged)
    """
    target_db_path = Path(target_db_path)
    source_db_path = Path(source_db_path)
    if not source_db_path.exists():
        raise FileNotFoundError(f"Файл БД не найден: {source_db_path}")

    refs_upserts = 0
    orders_merged = 0

    with get_connection(str(target_db_path)) as tgt_conn:
        src_conn = sqlite3.connect(str(source_db_path))
        src_conn.row_factory = _row_factory
        try:
            # --- 1) Reference tables ---
            # Workers
            for r in src_conn.execute("SELECT full_name, dept, position, personnel_no FROM workers").fetchall():
                if q.get_worker_by_personnel_no(tgt_conn, r["personnel_no"]) or q.get_worker_by_full_name(tgt_conn, r["full_name"]):
                    continue
                try:
                    q.insert_worker(tgt_conn, r["full_name"], r.get("dept"), r.get("position"), r["personnel_no"])
                    refs_upserts += 1
                except sqlite3.IntegrityError:
                    pass

            # Job types
            for r in src_conn.execute("SELECT name, unit, price FROM job_types").fetchall():
                q.upsert_job_type(tgt_conn, r["name"], r["unit"], float(r["price"]))
                refs_upserts += 1

            # Products
            for r in src_conn.execute("SELECT name, product_no FROM products").fetchall():
                q.upsert_product(tgt_conn, r["name"], r["product_no"])
                refs_upserts += 1

            # Contracts
            for r in src_conn.execute("SELECT code, start_date, end_date, description FROM contracts").fetchall():
                q.upsert_contract(tgt_conn, r["code"], r.get("start_date"), r.get("end_date"), r.get("description"))
                refs_upserts += 1

            # --- 2) Work orders ---
            # Read orders from source and import to target
            src_orders = src_conn.execute(
                """
                SELECT id, order_no, date, product_id, contract_id, total_amount
                FROM work_orders
                ORDER BY date, order_no
                """
            ).fetchall()

            # Helpers to map FK ids using natural keys
            def _map_contract_id(src_contract_id: int | None) -> int | None:
                if not src_contract_id:
                    return None
                row = src_conn.execute("SELECT code FROM contracts WHERE id=?", (src_contract_id,)).fetchone()
                if not row:
                    return None
                tgt = q.get_contract_by_code(tgt_conn, row["code"])  # by code_norm
                return int(tgt["id"]) if tgt else None

            def _map_product_id(src_product_id: int | None) -> int | None:
                if not src_product_id:
                    return None
                row = src_conn.execute("SELECT product_no, name FROM products WHERE id=?", (src_product_id,)).fetchone()
                if not row:
                    return None
                # Prefer product_no for lookup; fallback by name
                tgt = q.get_product_by_no(tgt_conn, row["product_no"]) or q.get_product_by_name(tgt_conn, row["name"])
                return int(tgt["id"]) if tgt else None

            def _map_job_type_id(src_job_type_id: int) -> Optional[int]:
                r = src_conn.execute("SELECT name FROM job_types WHERE id=?", (src_job_type_id,)).fetchone()
                if not r:
                    return None
                jt = q.get_job_type_by_name(tgt_conn, r["name"])
                return int(jt["id"]) if jt else None

            def _map_worker_id(src_worker_id: int) -> Optional[int]:
                r = src_conn.execute("SELECT full_name, personnel_no FROM workers WHERE id=?", (src_worker_id,)).fetchone()
                if not r:
                    return None
                w = q.get_worker_by_personnel_no(tgt_conn, r["personnel_no"]) or q.get_worker_by_full_name(tgt_conn, r["full_name"]) 
                return int(w["id"]) if w else None

            for o in src_orders:
                tgt_contract_id = _map_contract_id(o["contract_id"])
                tgt_product_id = _map_product_id(o["product_id"]) if o["product_id"] else None
                if not tgt_contract_id:
                    # Cannot import order without contract mapping
                    continue

                # Choose order_no: keep if free, else allocate new
                desired_no = int(o["order_no"]) if o["order_no"] is not None else None
                use_order_no = desired_no
                if desired_no is not None:
                    row = tgt_conn.execute("SELECT 1 FROM work_orders WHERE order_no=?", (desired_no,)).fetchone()
                    if row:
                        use_order_no = q.next_order_no(tgt_conn)
                else:
                    use_order_no = q.next_order_no(tgt_conn)

                # Insert header (total will be recomputed by sum of items below)
                new_wo_id = q.insert_work_order(
                    tgt_conn,
                    order_no=use_order_no,
                    date=o["date"],
                    product_id=tgt_product_id,
                    contract_id=tgt_contract_id,
                    total_amount=float(o.get("total_amount") or 0.0),
                )

                # Items
                items = src_conn.execute(
                    "SELECT job_type_id, quantity, unit_price, line_amount FROM work_order_items WHERE work_order_id=?",
                    (o["id"],),
                ).fetchall()
                total = 0.0
                for it in items:
                    jt_id = _map_job_type_id(it["job_type_id"])
                    if not jt_id:
                        continue
                    qty = float(it["quantity"]) if it["quantity"] is not None else 0.0
                    unit_price = float(it["unit_price"]) if it["unit_price"] is not None else 0.0
                    line_amount = float(it["line_amount"]) if it["line_amount"] is not None else qty * unit_price
                    q.insert_work_order_item(tgt_conn, new_wo_id, jt_id, qty, unit_price, line_amount)
                    total += line_amount
                q.update_work_order_total(tgt_conn, new_wo_id, total)

                # Workers
                wrows = src_conn.execute(
                    "SELECT worker_id FROM work_order_workers WHERE work_order_id=?",
                    (o["id"],),
                ).fetchall()
                mapped_ids = []
                for wr in wrows:
                    wid = _map_worker_id(wr["worker_id"])
                    if wid:
                        mapped_ids.append(wid)
                if mapped_ids:
                    q.set_work_order_workers(tgt_conn, new_wo_id, mapped_ids)

                orders_merged += 1
        finally:
            src_conn.close()

    return refs_upserts, orders_merged