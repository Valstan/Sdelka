from __future__ import annotations

import sqlite3
from typing import Sequence

from config.settings import CONFIG
from db import queries as q


def suggest_workers(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[tuple[int, str]]:
    if prefix:
        rows = q.search_workers_by_substring(conn, prefix, limit or CONFIG.autocomplete_limit)
    else:
        rows = q.list_workers(conn, None, limit or CONFIG.autocomplete_limit)
    result: list[tuple[int, str]] = []
    for r in rows:
        label = r["full_name"]
        if (r["status"] if "status" in r.keys() else None) not in (None, "", "Работает"):
            label = f"{label} (Уволен)"
        result.append((r["id"], label))
    return result


def suggest_job_types(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[tuple[int, str]]:
    # Если пустой ввод — вернем самые популярные/последние по истории использования
    # (История используется на уровне формы; здесь при пустом запросе вернем первые N по алфавиту)
    if not prefix:
        rows = q.list_job_types(conn, None, limit or CONFIG.autocomplete_limit)
    else:
        # Поиск подстрокой по всей строке (name_norm LIKE %term%)
        rows = q.search_job_types_by_substring(conn, prefix, limit or CONFIG.autocomplete_limit)
    return [(r["id"], r["name"]) for r in rows]


def suggest_products(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[tuple[int, str]]:
    if prefix:
        rows = q.search_products_by_substring(conn, prefix, limit or CONFIG.autocomplete_limit)
    else:
        rows = q.list_products(conn, None, limit or CONFIG.autocomplete_limit)
    return [(r["id"], f"{r['product_no']} — {r['name']}") for r in rows]


def suggest_contracts(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[tuple[int, str]]:
    if prefix:
        rows = q.search_contracts_by_substring(conn, prefix, limit or CONFIG.autocomplete_limit)
    else:
        rows = q.list_contracts(conn, None, limit or CONFIG.autocomplete_limit)
    return [(r["id"], r["code"]) for r in rows]


def suggest_depts(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[str]:
    return q.distinct_depts_by_prefix(conn, prefix, limit or CONFIG.autocomplete_limit)


def suggest_positions(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[str]:
    return q.distinct_positions_by_prefix(conn, prefix, limit or CONFIG.autocomplete_limit)


def suggest_personnel_nos(conn: sqlite3.Connection, prefix: str, limit: int | None = None) -> list[str]:
    return q.personnel_numbers_by_prefix(conn, prefix, limit or CONFIG.autocomplete_limit)