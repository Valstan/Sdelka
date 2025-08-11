from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from app.db.connection import Database
from app.db.models import Contract, JobType, Product, WorkOrder, Worker
from app.utils.paths import get_paths

_QUERY_NAME_RE = re.compile(r"^-- \[(?P<name>[^\]]+)\]")


class QueryStore:
    """Load and cache named SQL queries from queries.sql."""

    def __init__(self) -> None:
        self._queries: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        paths = get_paths()
        sql_path = paths.root / "app" / "db" / "queries.sql"
        text = sql_path.read_text(encoding="utf-8")
        current: str | None = None
        buffer: list[str] = []
        for line in text.splitlines():
            if m := _QUERY_NAME_RE.match(line.strip()):
                if current and buffer:
                    self._queries[current] = "\n".join(buffer).strip()
                    buffer.clear()
                current = m.group("name")
                continue
            if current:
                buffer.append(line)
        if current and buffer:
            self._queries[current] = "\n".join(buffer).strip()

    def get(self, name: str) -> str:
        sql = self._queries.get(name)
        if not sql:
            raise KeyError(f"Query not found: {name}")
        return sql


_QUERIES = QueryStore()


class Repository:
    """High-level repository API wrapping low-level DB operations."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database.instance()

    # Workers
    def add_worker(self, worker: Worker) -> int:
        sql = _QUERIES.get("workers.insert")
        cur = self.db.execute(
            sql,
            [
                worker.last_name,
                worker.first_name,
                worker.middle_name,
                worker.position,
                worker.phone,
                worker.hire_date,
                worker.is_active,
            ],
        )
        return int(cur.lastrowid)

    def list_workers(self, active_only: bool = False) -> list[dict[str, Any]]:
        sql = _QUERIES.get("workers.select_active" if active_only else "workers.select_all")
        return [dict(r) for r in self.db.query_all(sql)]

    # Job Types
    def add_job_type(self, job_type: JobType) -> int:
        sql = _QUERIES.get("job_types.insert")
        cur = self.db.execute(sql, [job_type.name, job_type.unit, job_type.base_rate])
        return int(cur.lastrowid)

    def list_job_types(self) -> list[dict[str, Any]]:
        sql = _QUERIES.get("job_types.select_all")
        return [dict(r) for r in self.db.query_all(sql)]

    # Products
    def add_product(self, product: Product) -> int:
        sql = _QUERIES.get("products.insert")
        cur = self.db.execute(sql, [product.name, product.sku, product.description])
        return int(cur.lastrowid)

    def list_products(self) -> list[dict[str, Any]]:
        sql = _QUERIES.get("products.select_all")
        return [dict(r) for r in self.db.query_all(sql)]

    # Contracts
    def add_contract(self, contract: Contract) -> int:
        sql = _QUERIES.get("contracts.insert")
        cur = self.db.execute(
            sql,
            [
                contract.contract_number,
                contract.customer,
                contract.start_date,
                contract.end_date,
                contract.status,
            ],
        )
        return int(cur.lastrowid)

    def list_contracts(self) -> list[dict[str, Any]]:
        sql = _QUERIES.get("contracts.select_all")
        return [dict(r) for r in self.db.query_all(sql)]

    # Work Orders
    def add_work_order(self, work_order: WorkOrder) -> int:
        sql = _QUERIES.get("work_orders.insert")
        cur = self.db.execute(
            sql,
            [
                work_order.contract_id,
                work_order.worker_id,
                work_order.job_type_id,
                work_order.product_id,
                work_order.date,
                work_order.quantity,
                work_order.unit_rate,
                work_order.amount,
                work_order.notes,
            ],
        )
        return int(cur.lastrowid)

    def list_work_orders(self) -> list[dict[str, Any]]:
        sql = _QUERIES.get("work_orders.select_all")
        return [dict(r) for r in self.db.query_all(sql)]

    def filter_work_orders(
        self,
        start_date: str,
        end_date: str,
        worker_id: int | None = None,
        contract_id: int | None = None,
    ) -> list[dict[str, Any]]:
        sql = _QUERIES.get("work_orders.select_filtered")
        params = [start_date, end_date, worker_id, worker_id, contract_id, contract_id]
        return [dict(r) for r in self.db.query_all(sql, params)]