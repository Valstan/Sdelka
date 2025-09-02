from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from db import queries as q
from utils.text import normalize_for_search


def upsert_job_types(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    added = 0
    updated = 0
    for r in rows:
        name = (r.get("name") or "").strip()
        unit = (r.get("unit") or "шт.").strip() or "шт."
        price = float(r.get("price") or 0.0)
        if not name:
            continue
        res_id = q.upsert_job_type(conn, name, unit, price)
        if isinstance(res_id, int) and res_id > 0:
            added += 1
        else:
            updated += 1
    return added, updated


def upsert_products(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    added = 0
    updated = 0
    for r in rows:
        name = (r.get("name") or "").strip()
        product_no = (r.get("product_no") or "").strip()
        if not (name and product_no):
            continue
        contract_code = (r.get("contract_code") or "").strip()
        contract_id = None
        if contract_code:
            try:
                contract_id = q.get_or_create_contract_by_code(conn, contract_code)
            except Exception:
                contract_id = q.get_or_create_default_contract(conn)
        else:
            contract_id = q.get_or_create_default_contract(conn)
        res_id = q.upsert_product(conn, name, product_no, contract_id)
        if isinstance(res_id, int) and res_id > 0:
            added += 1
        else:
            updated += 1
    return added, updated


def upsert_contracts(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    added = 0
    updated = 0
    for r in rows:
        code = (r.get("code") or "").strip()
        if not code:
            continue
        res_id = q.upsert_contract(
            conn,
            code,
            r.get("start_date"),
            r.get("end_date"),
            r.get("description"),
            name=r.get("name"),
            contract_type=r.get("contract_type"),
            executor=r.get("executor"),
            igk=r.get("igk"),
            contract_number=r.get("contract_number"),
            bank_account=r.get("bank_account"),
        )
        if isinstance(res_id, int) and res_id > 0:
            added += 1
        else:
            updated += 1
    return added, updated


def upsert_workers(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    added = 0
    updated = 0
    for r in rows:
        fio = (r.get("full_name") or "").strip()
        if not fio:
            continue
        personnel_no = (r.get("personnel_no") or f"AUTO-{normalize_for_search(fio)}").strip()
        dept = (r.get("dept") or None)
        # Нормализация цеха: сохраняем цифру. Поддержка значений вида "1", 1, 1.0, "цех № 1" и т.п.
        try:
            if dept is not None:
                s = str(dept).strip()
                if s.isdigit():
                    dept = s
                else:
                    try:
                        val = float(s.replace(",", "."))
                        if val.is_integer():
                            dept = str(int(val))
                        else:
                            import re as _re
                            m = _re.search(r"(\d+)", s)
                            dept = m.group(1) if m else None
                    except Exception:
                        import re as _re
                        m = _re.search(r"(\d+)", s)
                        dept = m.group(1) if m else None
        except Exception:
            try:
                dept = None
            except Exception:
                pass
        position = (r.get("position") or None)
        status = (r.get("status") or None)
        res = q.upsert_worker(conn, fio, dept, position, personnel_no, status)
        if res:
            added += 1
        else:
            updated += 0
    return added, updated



