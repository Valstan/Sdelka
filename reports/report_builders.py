from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import pandas as pd
from utils.text import short_fio


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


def work_orders_report_context(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    date_from: str | None = None,
    date_to: str | None = None,
    dept: str | None = None,
) -> dict[str, Any]:
    """Compute header and footer info for the report.

    Returns keys: title, period, dept_name, created_at, total_amount, worker_signatures, dept_head, hr_head
    """
    from datetime import datetime
    title = "Отчет по нарядам"
    created_at = datetime.now().strftime("%d.%m.%Y")
    period = None
    if date_from or date_to:
        period = f"Период: {date_from or '...'} — {date_to or '...'}"
    dept_name = dept or None

    total_amount = 0.0
    if not df.empty:
        # Пытаемся найти колонку суммы по названиям
        for cand in ("Сумма", "line_amount", "Итог", "total", "Итого"):
            if cand in df.columns:
                try:
                    total_amount = float(pd.to_numeric(df[cand], errors="coerce").fillna(0).sum())
                    break
                except Exception:
                    pass

    # Соберем уникальные работники и превратим в короткий формат
    worker_signatures: list[str] = []
    for cand in ("Работник", "ФИО", "full_name"):
        if cand in df.columns:
            names = [short_fio(str(x)) for x in df[cand].dropna().unique().tolist()]
            worker_signatures = sorted(names, key=lambda s: s.casefold())
            break

    # Руководители — пока заглушки, можно позже брать из настроек/БД
    dept_head = None
    hr_head = None
    if dept_name:
        # Попытка найти начальника цеха по совпадению dept (требует отдельной таблицы в будущем)
        # Пока оставим пустым
        pass

    return {
        "title": title,
        "period": period,
        "dept_name": dept_name,
        "created_at": created_at,
        "total_amount": round(float(total_amount), 2),
        "worker_signatures": worker_signatures,
        "dept_head": dept_head,
        "hr_head": hr_head,
    }