from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from xml.etree.ElementTree import Element, SubElement, ElementTree
import json

from db.sqlite import get_connection
from utils.text import normalize_for_search


def _fmt_date_iso_to_ru(s: str | None) -> str:
    if not s:
        return ""
    # assume YYYY-MM-DD
    try:
        y, m, d = s.split("-")
        return f"{d}.{m}.{y}"
    except Exception:
        return s


def build_orders_1c_df(
    conn,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    product_id: int | None = None,
    contract_id: int | None = None,
    worker_id: int | None = None,
    worker_name: str | None = None,
    dept: str | None = None,
    job_type_id: int | None = None,
) -> pd.DataFrame:
    where: list[str] = []
    params: list[Any] = []
    if date_from:
        where.append("wo.date >= ?")
        params.append(date_from)
    if date_to:
        where.append("wo.date <= ?")
        params.append(date_to)
    if product_id:
        where.append("wo.product_id = ?")
        params.append(product_id)
    if contract_id:
        where.append("wo.contract_id = ?")
        params.append(contract_id)

    # Фильтры по работнику/цеху/виду работ: используем присоединения
    joins = [
        "LEFT JOIN contracts c ON c.id = wo.contract_id",
        "LEFT JOIN products p ON p.id = wo.product_id",
        "JOIN work_order_items woi ON woi.work_order_id = wo.id",
        "JOIN job_types jt ON jt.id = woi.job_type_id",
    ]
    if worker_id or worker_name or dept:
        joins.append("LEFT JOIN work_order_workers wow ON wow.work_order_id = wo.id")
        joins.append("LEFT JOIN workers w ON w.id = wow.worker_id")
        if worker_id:
            where.append("w.id = ?")
            params.append(worker_id)
        if worker_name:
            where.append("w.full_name_norm LIKE ?")
            params.append(f"%{worker_name.casefold()}%")
        if dept:
            where.append("w.dept_norm LIKE ?")
            params.append(f"%{dept.casefold()}%")
    if job_type_id:
        where.append("jt.id = ?")
        params.append(job_type_id)

    sql = (
        "SELECT "
        "wo.order_no AS order_no, wo.date AS date, "
        "c.code AS contract_code, c.name AS contract_name, c.igk AS contract_igk, c.contract_number AS contract_number, "
        "p.product_no AS product_no, p.name AS product_name, "
        "jt.name AS job_name, jt.unit AS unit, woi.quantity AS qty, woi.unit_price AS price, woi.line_amount AS amount "
        "FROM work_orders wo "
        + " " .join(joins) + " "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY wo.date, wo.order_no, p.product_no, jt.name"

    rows = conn.execute(sql, params).fetchall()
    data = []
    for r in rows:
        try:
            o = dict(r)
        except Exception:
            # tuple-like
            (order_no, date, contract_code, product_no, product_name, job_name, unit, qty, price, amount) = r
            o = {
                "order_no": order_no,
                "date": date,
                "contract_code": contract_code,
                "product_no": product_no,
                "product_name": product_name,
                "job_name": job_name,
                "unit": unit,
                "qty": qty,
                "price": price,
                "amount": amount,
            }
        data.append(o)

    df = pd.DataFrame(data)
    if df.empty:
        return df
    # Приведём формат даты к ДД.ММ.ГГГГ
    df["date"] = df["date"].map(_fmt_date_iso_to_ru)
    # Упорядочим и локализуем названия колонок для 1С
    columns = [
        ("date", "Дата"),
        ("order_no", "№ наряда"),
        ("contract_code", "Контракт"),
        ("contract_name", "Наименование контракта"),
        ("contract_igk", "ИГК"),
        ("contract_number", "Номер контракта"),
        ("product_no", "№ изделия"),
        ("product_name", "Наименование изделия"),
        ("job_name", "Вид работ"),
        ("unit", "Ед."),
        ("qty", "Кол-во"),
        ("price", "Цена"),
        ("amount", "Сумма"),
    ]
    out = df[[src for (src, _dst) in columns]].copy()
    out.columns = [dst for (_src, dst) in columns]
    # Добавим пустые служебные поля на будущее: Цех изделия, Примечание
    if "Цех изделия" not in out.columns:
        out["Цех изделия"] = ""
    if "Примечание" not in out.columns:
        out["Примечание"] = ""
    # Переупорядочим, чтобы доп. поля были в конце
    desired_order = [c for (_s, c) in columns] + ["Цех изделия", "Примечание"]
    out = out[[c for c in desired_order if c in out.columns]]
    return out


def build_workers_1c_df(
    conn,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    product_id: int | None = None,
    contract_id: int | None = None,
    worker_id: int | None = None,
    worker_name: str | None = None,
    dept: str | None = None,
    job_type_id: int | None = None,
) -> pd.DataFrame:
    where: list[str] = []
    params: list[Any] = []
    if date_from:
        where.append("wo.date >= ?")
        params.append(date_from)
    if date_to:
        where.append("wo.date <= ?")
        params.append(date_to)
    if product_id:
        where.append("wo.product_id = ?")
        params.append(product_id)
    if contract_id:
        where.append("wo.contract_id = ?")
        params.append(contract_id)
    joins = [
        "LEFT JOIN contracts c ON c.id = wo.contract_id",
        "LEFT JOIN products p ON p.id = wo.product_id",
        "JOIN work_order_workers wow ON wow.work_order_id = wo.id",
        "JOIN workers w ON w.id = wow.worker_id",
    ]
    if job_type_id:
        # Ограничим рабочие наряды наличием выбранного вида работ
        joins.append("JOIN work_order_items woi ON woi.work_order_id = wo.id")
        joins.append("JOIN job_types jt ON jt.id = woi.job_type_id")
        where.append("jt.id = ?")
        params.append(job_type_id)
    if worker_id:
        where.append("w.id = ?")
        params.append(worker_id)
    if worker_name:
        where.append("w.full_name_norm LIKE ?")
        params.append(f"%{worker_name.casefold()}%")
    if dept:
        where.append("w.dept_norm LIKE ?")
        params.append(f"%{dept.casefold()}%")

    sql = (
        "SELECT DISTINCT "
        "wo.order_no AS order_no, wo.date AS date, "
        "c.code AS contract_code, c.name AS contract_name, p.product_no AS product_no, p.name AS product_name, "
        "w.full_name AS worker_name, w.dept AS worker_dept, COALESCE(wow.amount, 0) AS worker_amount "
        "FROM work_orders wo "
        + " ".join(joins) + " "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY wo.date, wo.order_no, w.full_name"

    rows = conn.execute(sql, params).fetchall()
    data = []
    for r in rows:
        try:
            o = dict(r)
        except Exception:
            (order_no, date, contract_code, contract_name, product_no, product_name, worker_name2, worker_dept, worker_amount) = r
            o = {
                "order_no": order_no,
                "date": date,
                "contract_code": contract_code,
                "contract_name": contract_name,
                "product_no": product_no,
                "product_name": product_name,
                "worker_name": worker_name2,
                "worker_dept": worker_dept,
                "worker_amount": worker_amount,
            }
        data.append(o)
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["date"] = df["date"].map(_fmt_date_iso_to_ru)
    columns = [
        ("date", "Дата"),
        ("order_no", "№ наряда"),
        ("contract_code", "Контракт"),
        ("contract_name", "Наименование контракта"),
        ("product_no", "№ изделия"),
        ("product_name", "Наименование изделия"),
        ("worker_name", "Работник"),
        ("worker_dept", "Цех"),
        ("worker_amount", "Сумма работнику"),
    ]
    out = df[[src for (src, _dst) in columns]].copy()
    out.columns = [dst for (_src, dst) in columns]
    return out


def save_1c_json(
    *,
    path: str | Path,
    df_lines: pd.DataFrame | None = None,
    df_workers: pd.DataFrame | None = None,
    orders: list[dict] | None = None,
    meta: dict | None = None,
    encoding: str = "utf-8",
) -> Path:
    path = Path(path)
    payload: dict[str, Any] = {
        "format": "1C-export",
        "version": "1.0",
    }
    from datetime import datetime as _dt
    payload["exported_at"] = _dt.now().isoformat(timespec="seconds")
    if meta:
        payload["filters"] = meta
    def df_to_records(df: pd.DataFrame | None) -> list[dict]:
        if df is None or df.empty:
            return []
        # Преобразуем в список словарей
        recs = df.fillna("").to_dict(orient="records")
        # Обеспечим строковые значения числовых колонок, если нужно — но 1С JSON обычно понимает числа
        return list(recs)
    if orders is not None:
        payload["orders"] = orders
    else:
        payload["lines"] = df_to_records(df_lines)
        payload["workers"] = df_to_records(df_workers)

    txt = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(txt, encoding=encoding)
    return path


def build_orders_unified(
    conn,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    product_id: int | None = None,
    contract_id: int | None = None,
    worker_id: int | None = None,
    worker_name: str | None = None,
    dept: str | None = None,
    job_type_id: int | None = None,
) -> list[dict]:
    # Список заказов по фильтрам
    where: list[str] = []
    params: list[Any] = []
    joins: list[str] = [
        "LEFT JOIN contracts c ON c.id = wo.contract_id",
        "LEFT JOIN products p ON p.id = wo.product_id",
        "LEFT JOIN work_order_products wop ON wop.work_order_id = wo.id",
    ]
    if date_from:
        where.append("wo.date >= ?"); params.append(date_from)
    if date_to:
        where.append("wo.date <= ?"); params.append(date_to)
    if contract_id:
        where.append("wo.contract_id = ?"); params.append(contract_id)
    if product_id:
        where.append("(wo.product_id = ? OR wop.product_id = ?)")
        params.extend([product_id, product_id])
    if worker_id or worker_name or dept:
        joins.append("LEFT JOIN work_order_workers wow ON wow.work_order_id = wo.id")
        joins.append("LEFT JOIN workers w ON w.id = wow.worker_id")
        if worker_id:
            where.append("w.id = ?"); params.append(worker_id)
        if worker_name:
            where.append("w.full_name_norm LIKE ?"); params.append(f"%{normalize_for_search(worker_name)}%")
        if dept:
            where.append("w.dept_norm LIKE ?"); params.append(f"%{normalize_for_search(dept)}%")
    if job_type_id:
        joins.append("LEFT JOIN work_order_items woi ON woi.work_order_id = wo.id")
        joins.append("LEFT JOIN job_types jt ON jt.id = woi.job_type_id")
        where.append("jt.id = ?"); params.append(job_type_id)

    sql = (
        "SELECT DISTINCT wo.id, wo.order_no, wo.date, wo.total_amount, "
        "c.code, c.name, c.igk, c.contract_number "
        "FROM work_orders wo " + " ".join(joins) + " "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY wo.date, wo.order_no"
    order_rows = conn.execute(sql, params).fetchall()
    orders: list[dict] = []
    for r in order_rows:
        try:
            rid = int(r["id"])  # type: ignore[index]
            order_no = int(r["order_no"])  # type: ignore[index]
            date_iso = str(r["date"])  # type: ignore[index]
            total = float(r["total_amount"])  # type: ignore[index]
            c_code = r["code"]; c_name = r["name"]; c_igk = r["igk"]; c_num = r["contract_number"]
        except Exception:
            (rid, order_no, date_iso, total, c_code, c_name, c_igk, c_num) = r
        # Дата в ДД.ММ.ГГГГ
        date_ru = _fmt_date_iso_to_ru(date_iso)
        # Продукты всех связей
        prod_ids = conn.execute("SELECT DISTINCT COALESCE(wo.product_id, wop.product_id) FROM work_orders wo LEFT JOIN work_order_products wop ON wop.work_order_id = wo.id WHERE wo.id=?", (rid,)).fetchall()
        products: list[dict] = []
        for pr in prod_ids:
            try:
                pid = int(pr[0])
            except Exception:
                continue
            prow = conn.execute("SELECT id, product_no, name FROM products WHERE id=?", (pid,)).fetchone()
            if prow:
                try:
                    pid2 = int(prow["id"])  # type: ignore[index]
                    pno = prow["product_no"]; pname = prow["name"]
                except Exception:
                    (pid2, pno, pname) = prow
                products.append({"id": pid2, "no": pno or "", "name": pname or ""})
        # Позиции работ с единицами
        items_rows = conn.execute(
            "SELECT jt.name, jt.unit, woi.quantity, woi.unit_price, woi.line_amount FROM work_order_items woi JOIN job_types jt ON jt.id = woi.job_type_id WHERE woi.work_order_id = ? ORDER BY woi.id",
            (rid,),
        ).fetchall()
        items: list[dict] = []
        for ir in items_rows:
            try:
                jn, un, q, prc, amt = ir
            except Exception:
                jn = ir["name"]; un = ir["unit"]; q = ir["quantity"]; prc = ir["unit_price"]; amt = ir["line_amount"]
            items.append({"job_name": jn, "unit": un, "qty": float(q or 0), "price": float(prc or 0), "amount": float(amt or 0)})
        # Работники с суммами
        workers_rows = conn.execute(
            "SELECT w.id, w.full_name, w.dept, COALESCE(wow.amount, 0) FROM work_order_workers wow JOIN workers w ON w.id = wow.worker_id WHERE wow.work_order_id = ? ORDER BY w.full_name",
            (rid,),
        ).fetchall()
        workers: list[dict] = []
        for wr in workers_rows:
            try:
                wid, wname, wdept, wamt = wr
            except Exception:
                wid = wr["id"]; wname = wr["full_name"]; wdept = wr["dept"]; wamt = wr[3] if 3 in wr else wr["amount"]
            workers.append({"id": int(wid), "full_name": wname or "", "dept": wdept or "", "amount": float(wamt or 0)})
        order = {
            "order_no": order_no,
            "date": date_ru,
            "total_amount": total,
            "contract": {
                "code": c_code or "",
                "name": c_name or "",
                "igk": c_igk or "",
                "number": c_num or "",
            },
            "products": products,
            "items": items,
            "workers": workers,
        }
        orders.append(order)
    return orders


