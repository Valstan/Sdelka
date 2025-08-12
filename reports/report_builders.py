from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import pandas as pd


def work_orders_report_df(
    conn: sqlite3.Connection,
    date_from: str | None = None,
    date_to: str | None = None,
    worker_id: int | None = None,
    dept: str | None = None,
    job_type_id: int | None = None,
    product_id: int | None = None,
    contract_id: int | None = None,
) -> pd.DataFrame:
    where = []
    params: list[Any] = []

    if date_from:
        where.append("wo.date >= ?")
        params.append(date_from)
    if date_to:
        where.append("wo.date <= ?")
        params.append(date_to)
    if worker_id:
        where.append("wow.worker_id = ?")
        params.append(worker_id)
    if dept:
        where.append("w.dept = ?")
        params.append(dept)
    if job_type_id:
        where.append("woi.job_type_id = ?")
        params.append(job_type_id)
    if product_id:
        where.append("wo.product_id = ?")
        params.append(product_id)
    if contract_id:
        where.append("wo.contract_id = ?")
        params.append(contract_id)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT
        wo.order_no AS Номер,
        wo.date AS Дата,
        c.code AS Контракт,
        p.product_no AS Номер_изделия,
        p.name AS Изделие,
        jt.name AS Вид_работ,
        woi.quantity AS Количество,
        woi.unit_price AS Цена,
        woi.line_amount AS Сумма,
        w.full_name AS Работник,
        w.dept AS Цех
    FROM work_orders wo
    LEFT JOIN contracts c ON c.id = wo.contract_id
    LEFT JOIN products p ON p.id = wo.product_id
    JOIN work_order_items woi ON woi.work_order_id = wo.id
    JOIN job_types jt ON jt.id = woi.job_type_id
    JOIN work_order_workers wow ON wow.work_order_id = wo.id
    JOIN workers w ON w.id = wow.worker_id
    {where_sql}
    ORDER BY wo.date DESC, wo.order_no DESC
    """

    return pd.read_sql_query(sql, conn, params=params)