from __future__ import annotations

import sqlite3
from typing import Iterable

from db import queries as q


# Workers

def add_or_update_worker(conn: sqlite3.Connection, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> int:
    return q.insert_worker(conn, full_name, dept, position, personnel_no)


def update_worker(conn: sqlite3.Connection, worker_id: int, full_name: str, dept: str | None, position: str | None, personnel_no: str) -> None:
    q.update_worker(conn, worker_id, full_name, dept, position, personnel_no)


def delete_worker(conn: sqlite3.Connection, worker_id: int) -> None:
    q.delete_worker(conn, worker_id)


def list_workers(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None):
    return q.list_workers(conn, prefix, limit)


# Job Types

def add_or_update_job_type(conn: sqlite3.Connection, name: str, unit: str, price: float) -> int:
    return q.upsert_job_type(conn, name, unit, price)


# Products

def add_or_update_product(conn: sqlite3.Connection, name: str, product_no: str) -> int:
    return q.upsert_product(conn, name, product_no)


# Contracts

def add_or_update_contract(conn: sqlite3.Connection, code: str, start_date: str | None, end_date: str | None, description: str | None) -> int:
    return q.upsert_contract(conn, code, start_date, end_date, description)