from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import pandas as pd
from utils.text import short_fio, normalize_for_search


def work_orders_report_df(
    conn: sqlite3.Connection,
    date_from: str | None = None,
    date_to: str | None = None,
    worker_id: int | None = None,
    worker_name: str | None = None,
    dept: str | None = None,
    job_type_id: int | None = None,
    product_id: int | None = None,
    contract_id: int | None = None,
) -> pd.DataFrame:
    """Отчет по начислениям работникам с детализацией по строкам наряда (видам работ).

    Каждая строка — работник в рамках конкретной строки работ наряда. Сумма "Начислено" распределяется
    пропорционально сумме строки работ от общего начисления работнику в наряде.
    """
    where: list[str] = []
    params_where: list[Any] = []
    params_join: list[Any] = []

    if date_from:
        where.append("wo.date >= ?")
        params_where.append(date_from)
    if date_to:
        where.append("wo.date <= ?")
        params_where.append(date_to)
    # Фильтр по работнику: либо по id через сравнение нормализованного ФИО, либо по тексту
    if worker_id and worker_name:
        where.append("(w.full_name_norm = (SELECT full_name_norm FROM workers WHERE id = ?) OR w.full_name_norm = ?)")
        params_where.append(worker_id)
        params_where.append(normalize_for_search(worker_name) or "")
    elif worker_id:
        where.append("w.full_name_norm = (SELECT full_name_norm FROM workers WHERE id = ?)")
        params_where.append(worker_id)
    elif worker_name:
        where.append("w.full_name_norm = ?")
        params_where.append(normalize_for_search(worker_name) or "")
    if dept:
        where.append("w.dept = ?")
        params_where.append(dept)
    if product_id:
        where.append("wo.product_id = ?")
        params_where.append(product_id)
    if contract_id:
        where.append("wo.contract_id = ?")
        params_where.append(contract_id)

    exists_job_filter = ""
    if job_type_id:
        exists_job_filter = " AND EXISTS (SELECT 1 FROM work_order_items i WHERE i.work_order_id = wo.id AND i.job_type_id = ?)"
        params_where.append(job_type_id)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT
        wo.order_no AS Номер,
        wo.date AS Дата,
        c.code AS Контракт,
        p.product_no AS Номер_изделия,
        p.name AS Изделие,
        agg.job_types AS Вид_работ,
        w.full_name AS Работник,
        w.dept AS Цех,
        ROUND(COALESCE(wow.amount, 0), 2) AS Начислено
    FROM work_orders wo
    LEFT JOIN contracts c ON c.id = wo.contract_id
    LEFT JOIN products p ON p.id = wo.product_id
    LEFT JOIN (
        SELECT woi.work_order_id AS work_order_id, GROUP_CONCAT(jt.name, ', ') AS job_types
        FROM work_order_items woi
        JOIN job_types jt ON jt.id = woi.job_type_id
        GROUP BY woi.work_order_id
    ) agg ON agg.work_order_id = wo.id
    JOIN work_order_workers wow ON wow.work_order_id = wo.id
    JOIN workers w ON w.id = wow.worker_id
    {where_sql}{exists_job_filter}
    ORDER BY wo.date DESC, wo.order_no DESC, w.full_name
    """

    return pd.read_sql_query(sql, conn, params=params_where)


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
        for cand in ("Начислено", "Сумма", "line_amount", "Итог", "total", "Итого"):
            if cand in df.columns:
                try:
                    total_amount = float(pd.to_numeric(df[cand], errors="coerce").fillna(0).sum())
                    break
                except Exception:
                    pass

    # Соберем уникальные работники и превратим в короткий формат
    worker_signatures: list[str] = []
    worker_full: list[str] = []
    worker_dept: str | None = None
    for cand in ("Работник", "ФИО", "full_name"):
        if cand in df.columns:
            raw = df[cand].dropna().unique().tolist()
            worker_full = [str(x) for x in raw]
            worker_signatures = sorted([short_fio(str(x)) for x in raw], key=lambda s: s.casefold())
            break
    if dept:
        worker_dept = dept
    else:
        if "Цех" in df.columns and not df.empty:
            try:
                worker_dept = str(df["Цех"].dropna().iloc[0]) if not df["Цех"].dropna().empty else None
            except Exception:
                worker_dept = None

    # Руководители
    dept_head = None
    hr_head = None
    # Определяем цех: либо из фильтра, либо из данных (если один работник выбран)
    effective_dept = dept_name or context_like_dept(df)
    if effective_dept:
        try:
            row = conn.execute("SELECT head_full_name FROM departments WHERE name = ?", (effective_dept,)).fetchone()
            if row and row[0]:
                dept_head = short_fio(str(row[0]))
        except Exception:
            dept_head = None
    # HR head из таблицы settings или persons (если есть). Падаем в тихий режим если нет.
    try:
        row = conn.execute("SELECT value FROM app_settings WHERE key='hr_head' ").fetchone()
        if row and row[0]:
            hr_head = short_fio(str(row[0]))
    except Exception:
        hr_head = None

    return {
        "title": title,
        "period": period,
        "dept_name": dept_name,
        "created_at": created_at,
        "total_amount": round(float(total_amount), 2),
        "worker_signatures": worker_signatures,
        "dept_head": dept_head,
        "hr_head": hr_head,
        "single_worker_full": worker_full[0] if len(set(worker_full)) == 1 and worker_full else None,
        "single_worker_dept": worker_dept,
    }


def context_like_dept(df: pd.DataFrame) -> str | None:
    try:
        if "Цех" in df.columns and not df.empty:
            vals = [str(x) for x in df["Цех"].dropna().unique().tolist()]
            if len(vals) == 1:
                return vals[0]
    except Exception:
        pass
    return None