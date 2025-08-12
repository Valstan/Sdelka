from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence

from config.settings import CONFIG
from db import queries as q
from services.validation import validate_date, validate_positive_quantity

logger = logging.getLogger(__name__)


@dataclass
class WorkOrderItemInput:
    job_type_id: int
    quantity: float


@dataclass
class WorkOrderInput:
    date: str
    product_id: int | None
    contract_id: int
    items: Sequence[WorkOrderItemInput]
    worker_ids: Sequence[int]


def _round_rub(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_work_order(conn: sqlite3.Connection, data: WorkOrderInput) -> int:
    validate_date(data.date)
    if not data.items:
        raise ValueError("Наряд должен содержать хотя бы одну строку работ")

    total = Decimal("0")
    line_values: list[tuple[int, float, float, float]] = []

    for item in data.items:
        validate_positive_quantity(item.quantity)
        jt = conn.execute("SELECT id, price FROM job_types WHERE id = ?", (item.job_type_id,)).fetchone()
        if not jt:
            raise ValueError(f"Вид работ id={item.job_type_id} не найден")
        unit_price = Decimal(str(jt["price"]))
        line_amount = _round_rub(unit_price * Decimal(str(item.quantity)))
        total += line_amount
        line_values.append((item.job_type_id, float(item.quantity), float(unit_price), float(line_amount)))

    total = _round_rub(total)

    order_no = q.next_order_no(conn)
    work_order_id = q.insert_work_order(conn, order_no, data.date, data.product_id, data.contract_id, float(total))

    for (job_type_id, quantity, unit_price, line_amount) in line_values:
        q.insert_work_order_item(conn, work_order_id, job_type_id, quantity, unit_price, line_amount)

    q.set_work_order_workers(conn, work_order_id, data.worker_ids)

    logger.info("Создан наряд #%s, сумма: %s", order_no, total)
    return work_order_id


@dataclass
class LoadedWorkOrder:
    id: int
    order_no: int
    date: str
    product_id: int | None
    contract_id: int
    items: list[tuple[int, str, float, float, float]]  # job_type_id, name, qty, unit_price, line_amount
    worker_ids: list[int]
    total_amount: float


def load_work_order(conn: sqlite3.Connection, work_order_id: int) -> LoadedWorkOrder:
    header = q.get_work_order_header(conn, work_order_id)
    if not header:
        raise ValueError("Наряд не найден")
    items_rows = q.get_work_order_items(conn, work_order_id)
    workers_rows = q.get_work_order_workers(conn, work_order_id)
    items = [
        (r["job_type_id"], r["job_name"], float(r["quantity"]), float(r["unit_price"]), float(r["line_amount"]))
        for r in items_rows
    ]
    worker_ids = [int(r["worker_id"]) for r in workers_rows]
    return LoadedWorkOrder(
        id=int(header["id"]),
        order_no=int(header["order_no"]),
        date=str(header["date"]),
        product_id=int(header["product_id"]) if header["product_id"] is not None else None,
        contract_id=int(header["contract_id"]),
        items=items,
        worker_ids=worker_ids,
        total_amount=float(header["total_amount"]),
    )


def update_work_order(conn: sqlite3.Connection, work_order_id: int, data: WorkOrderInput) -> None:
    validate_date(data.date)
    if not data.items:
        raise ValueError("Наряд должен содержать хотя бы одну строку работ")

    total = Decimal("0")
    line_values: list[tuple[int, float, float, float]] = []

    for item in data.items:
        validate_positive_quantity(item.quantity)
        jt = conn.execute("SELECT id, price FROM job_types WHERE id = ?", (item.job_type_id,)).fetchone()
        if not jt:
            raise ValueError(f"Вид работ id={item.job_type_id} не найден")
        unit_price = Decimal(str(jt["price"]))
        line_amount = _round_rub(unit_price * Decimal(str(item.quantity)))
        total += line_amount
        line_values.append((item.job_type_id, float(item.quantity), float(unit_price), float(line_amount)))

    total = _round_rub(total)

    q.update_work_order_header(conn, work_order_id, data.date, data.product_id, data.contract_id, float(total))

    q.delete_work_order_items(conn, work_order_id)
    for (job_type_id, quantity, unit_price, line_amount) in line_values:
        q.insert_work_order_item(conn, work_order_id, job_type_id, quantity, unit_price, line_amount)

    q.set_work_order_workers(conn, work_order_id, data.worker_ids)

    logger.info("Обновлен наряд id=%s, сумма: %s", work_order_id, total)


def delete_work_order(conn: sqlite3.Connection, work_order_id: int) -> None:
    q.delete_work_order(conn, work_order_id)
    logger.info("Удален наряд id=%s", work_order_id)