from __future__ import annotations

import sqlite3
from typing import Iterable

from db import queries as q


# Workers

def add_or_update_worker(conn: sqlite3.Connection, full_name: str, dept: str | None, position: str | None, personnel_no: str, status: str | None = None) -> int:
    # create new as active by default
    return q.insert_worker(conn, full_name, dept, position, personnel_no)


def update_worker(conn: sqlite3.Connection, worker_id: int, full_name: str, dept: str | None, position: str | None, personnel_no: str, status: str | None = None) -> None:
    q.update_worker(conn, worker_id, full_name, dept, position, personnel_no, status)


def delete_worker(conn: sqlite3.Connection, worker_id: int) -> None:
    q.delete_worker(conn, worker_id)


def list_workers(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None):
    return q.list_workers(conn, prefix, limit)


# Job Types

def create_job_type(conn: sqlite3.Connection, name: str, unit: str, price: float) -> int:
    return q.insert_job_type(conn, name, unit, price)


def save_job_type(conn: sqlite3.Connection, job_type_id: int, name: str, unit: str, price: float) -> None:
    q.update_job_type(conn, job_type_id, name, unit, price)


def delete_job_type(conn: sqlite3.Connection, job_type_id: int) -> None:
    q.delete_job_type(conn, job_type_id)


def list_job_types(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None):
    return q.list_job_types(conn, prefix, limit)


# Products

def create_product(conn: sqlite3.Connection, name: str, product_no: str, contract_id: int | None = None) -> int:
    return q.insert_product(conn, name, product_no, contract_id)


def save_product(conn: sqlite3.Connection, product_id: int, name: str, product_no: str, contract_id: int | None = None) -> None:
    q.update_product(conn, product_id, name, product_no, contract_id)


def delete_product(conn: sqlite3.Connection, product_id: int) -> None:
    q.delete_product(conn, product_id)


def list_products(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None):
    return q.list_products(conn, prefix, limit)


# Contracts

def create_contract(conn: sqlite3.Connection, code: str, start_date: str | None, end_date: str | None, description: str | None,
                   name: str | None = None, contract_type: str | None = None, executor: str | None = None,
                   igk: str | None = None, contract_number: str | None = None, bank_account: str | None = None) -> int:
    return q.insert_contract(conn, code, start_date, end_date, description, name, contract_type, executor, igk, contract_number, bank_account)


def save_contract(conn: sqlite3.Connection, contract_id: int, code: str, start_date: str | None, end_date: str | None, description: str | None,
                 name: str | None = None, contract_type: str | None = None, executor: str | None = None,
                 igk: str | None = None, contract_number: str | None = None, bank_account: str | None = None) -> None:
    q.update_contract(conn, contract_id, code, start_date, end_date, description, name, contract_type, executor, igk, contract_number, bank_account)


def delete_contract(conn: sqlite3.Connection, contract_id: int) -> None:
    q.delete_contract(conn, contract_id)


def list_contracts(conn: sqlite3.Connection, prefix: str | None = None, limit: int | None = None):
    return q.list_contracts(conn, prefix, limit)