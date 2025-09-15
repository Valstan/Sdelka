from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import sqlite3

from db import queries as q
from db.sqlite import get_connection
from utils.text import normalize_for_search


ProgressCb = Callable[[int, int, str], None]


@dataclass
class ParsedOrder:
    header_year: int | None
    workers: list[dict[str, str]]  # {full_name, personnel_no?}
    products: list[str]  # product numbers
    items: list[dict[str, Any]]  # {date,name,unit,price,qty,amount}


def _parse_price(value: str) -> float:
    v = (value or "").replace("\xa0", " ").replace(" ", "").replace(",", ".").strip()
    try:
        return float(v)
    except Exception:
        return 0.0


def _parse_int_or_float(value: str) -> float:
    v = (value or "").replace("\xa0", " ").replace(" ", "").replace(",", ".").strip()
    try:
        if v.count(".") == 1:
            return float(v)
        return float(int(v))
    except Exception:
        return 0.0


def detect_orders_csv(path: str | Path) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = "\n".join([next(f) for _ in range(8)])
        return "Наряд на сдельные работы" in head
    except Exception:
        return False


def parse_orders_csv(path: str | Path) -> ParsedOrder:
    p = Path(path)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.reader(f, delimiter=";"))

    header_year: int | None = None
    workers: list[dict[str, str]] = []
    products: list[str] = []
    items: list[dict[str, Any]] = []

    # Year from first line
    if rows:
        m = re.search(r"(20\d{2})", " ".join(rows[0]))
        if m:
            try:
                header_year = int(m.group(1))
            except Exception:
                header_year = None

    current_date_str: str | None = None
    # parse
    for r in rows:
        full_text = " ".join([c for c in r if c]).strip()
        if not full_text:
            continue

        if full_text.startswith("ФИО сотрудника"):
            # Extract name after ':'
            name_match = re.search(r"ФИО сотрудника\s*:([^;]+)", full_text)
            name = (
                name_match.group(1).strip()
                if name_match
                else full_text.replace("ФИО сотрудника", "").strip(": ")
            )
            # Remove extra notes like 'тоже'
            name = name.replace("тоже", "").strip()
            tab_match = re.search(r"Таб\s*№\s*([0-9A-Za-z\-]+)", full_text)
            personnel_no = (
                tab_match.group(1).strip()
                if tab_match
                else f"AUTO-{normalize_for_search(name)}"
            )
            if name:
                workers.append({"full_name": name, "personnel_no": personnel_no})
            continue

        if full_text.startswith("Изделие №"):
            # Extract multiple numbers separated by commas
            after = full_text.split("№", 1)[1]
            parts = [p.strip() for p in after.split(",")]
            for part in parts:
                part = re.sub(r"-\s*повтор.*$", "", part).strip()
                if part:
                    products.append(part)
            continue

        # Header line for items
        if full_text.lower().startswith("дата;"):
            continue

        # Item lines: date present or continued line
        if re.match(r"^\d{2}\.\d{2}\.?.*", r[0] if r else ""):
            current_date_str = (r[0] or "").strip()
        # If not an item row, skip
        # Heuristic: expecting columns like [date or blank, name, unit, price, qty, amount]
        # Guard on presence of price and qty
        cols = r + [""] * (6 - len(r))
        name = cols[1].strip()
        unit = cols[2].strip() or "шт."
        price = _parse_price(cols[3])
        qty = _parse_int_or_float(cols[4])
        amount = _parse_price(cols[5])
        if name and (price > 0 or qty > 0 or amount > 0):
            items.append(
                {
                    "date": current_date_str,
                    "name": name,
                    "unit": unit or "шт.",
                    "price": price,
                    "qty": qty if qty else (amount / price if price else 0),
                    "amount": amount if amount else (price * qty),
                }
            )

    return ParsedOrder(
        header_year=header_year, workers=workers, products=products, items=items
    )


def _resolve_date(d: str | None, fallback_year: int | None) -> str:
    if not d:
        return datetime.now().strftime("%Y-%m-%d")
    d = d.strip()
    # formats: dd.mm. or dd.mm.yyyy
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", d)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r"^(\d{2})\.(\d{2})\.$", d)
    if m:
        year = fallback_year or datetime.now().year
        return f"{year}-{m.group(2)}-{m.group(1)}"
    # fallback: today
    return datetime.now().strftime("%Y-%m-%d")


def import_orders_from_csv(
    path: str | Path, progress_cb: ProgressCb | None = None
) -> dict[str, int]:
    parsed = parse_orders_csv(path)
    if progress_cb:
        progress_cb(0, 1, "Подготовка к записи в БД...")
    with get_connection() as conn:
        return _commit_parsed_order(conn, parsed, progress_cb)


def _commit_parsed_order(
    conn: sqlite3.Connection, parsed: ParsedOrder, progress_cb: ProgressCb | None
) -> dict[str, int]:
    added_items = 0
    added_workers = 0
    added_products = 0
    # Contract: default
    contract_id = q.get_or_create_default_contract(conn)

    # Products
    product_ids: list[int] = []
    for pn in parsed.products:
        existing = q.get_product_by_no(conn, pn)
        if existing:
            pid = int(existing["id"])  # type: ignore[index]
        else:
            name = f"Изделие {pn}"
            pid = q.upsert_product(conn, name, pn, contract_id)
            added_products += 1
        product_ids.append(pid)

    # Date heuristics
    dates = [
        _resolve_date(it.get("date"), parsed.header_year)
        for it in parsed.items
        if it.get("date")
    ]
    order_date = max(dates) if dates else datetime.now().strftime("%Y-%m-%d")

    # Total amount
    total_amount = round(sum(float(it.get("amount") or 0) for it in parsed.items), 2)

    # Order header
    order_no = q.next_order_no(conn)
    first_product_id = product_ids[0] if product_ids else None
    wo_id = q.insert_work_order(
        conn,
        order_no=order_no,
        date=order_date,
        product_id=first_product_id,
        contract_id=contract_id,
        total_amount=total_amount,
    )

    # Link additional products
    if len(product_ids) > 1:
        q.set_work_order_products(conn, wo_id, product_ids)

    # Items
    for it in parsed.items:
        # Upsert job type (updates price if changed)
        jt_id = q.upsert_job_type(
            conn, it["name"], it.get("unit") or "шт.", float(it.get("price") or 0.0)
        )
        if isinstance(jt_id, int) and jt_id <= 0:
            row = q.get_job_type_by_name(conn, it["name"]) or {}
            jt_id = int(row.get("id")) if row else None  # type: ignore[arg-type]
        if jt_id is None:
            continue
        qty = float(it.get("qty") or 0.0)
        price = float(it.get("price") or 0.0)
        amount = float(it.get("amount") or (qty * price))
        q.insert_work_order_item(conn, wo_id, int(jt_id), qty, price, amount)
        added_items += 1

    # Workers: upsert and allocations
    worker_ids: list[int] = []
    for w in parsed.workers:
        full_name = w.get("full_name") or ""
        personnel_no = (
            w.get("personnel_no") or f"AUTO-{normalize_for_search(full_name)}"
        )
        if not full_name:
            continue
        q.upsert_worker(conn, full_name, None, None, personnel_no)
        row = q.get_worker_by_personnel_no(
            conn, personnel_no
        ) or q.get_worker_by_full_name(conn, full_name)
        if row:
            worker_ids.append(int(row["id"]))  # type: ignore[index]
            added_workers += 1

    # Equal allocation if any workers
    allocations: list[tuple[int, float]] = []
    if worker_ids:
        per = round(total_amount / len(worker_ids), 2)
        amounts = [per] * len(worker_ids)
        diff = round(total_amount - round(per * len(worker_ids), 2), 2)
        if len(worker_ids) > 0 and abs(diff) >= 0.01:
            amounts[-1] = round(amounts[-1] + diff, 2)
        allocations = [(wid, amounts[idx]) for idx, wid in enumerate(worker_ids)]
        q.set_work_order_workers_with_amounts(conn, wo_id, allocations)

    # Update total amount to ensure consistency
    q.update_work_order_total(conn, wo_id, total_amount)

    return {
        "orders": 1,
        "items": added_items,
        "workers": len(worker_ids),
        "products": added_products,
    }
