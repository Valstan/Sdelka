from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.db.models import Contract, JobType, Product, Worker
from app.services.contracts_service import ContractsService
from app.services.job_types_service import JobTypesService
from app.services.products_service import ProductsService
from app.services.workers_service import WorkersService
from app.utils.validators import ensure_unique, parse_iso_date, require_non_negative


class ExcelImporter:
    """Import data from an Excel workbook with expected sheet names."""

    def __init__(self) -> None:
        self.workers_service = WorkersService()
        self.job_types_service = JobTypesService()
        self.products_service = ProductsService()
        self.contracts_service = ContractsService()

    def import_file(self, path: str) -> None:
        xls = pd.ExcelFile(path)
        if "workers" in xls.sheet_names:
            df = xls.parse("workers")
            ensure_unique(df["last_name"] + df["first_name"], "worker", "name")
            for _, row in df.iterrows():
                self.workers_service.create_worker(
                    last_name=str(row.get("last_name", "")).strip(),
                    first_name=str(row.get("first_name", "")).strip(),
                    middle_name=str(row.get("middle_name")) if pd.notna(row.get("middle_name")) else None,
                    position=str(row.get("position")) if pd.notna(row.get("position")) else None,
                    phone=str(row.get("phone")) if pd.notna(row.get("phone")) else None,
                    hire_date=str(row.get("hire_date")) if pd.notna(row.get("hire_date")) else None,
                )
        if "job_types" in xls.sheet_names:
            df = xls.parse("job_types")
            ensure_unique(df["name"], "job_type", "name")
            for _, row in df.iterrows():
                self.job_types_service.create_job_type(
                    name=str(row.get("name", "")).strip(),
                    unit=str(row.get("unit", "")).strip(),
                    base_rate=float(row.get("base_rate", 0) or 0.0),
                )
        if "products" in xls.sheet_names:
            df = xls.parse("products")
            ensure_unique(df["name"], "product", "name")
            for _, row in df.iterrows():
                self.products_service.create_product(
                    name=str(row.get("name", "")).strip(),
                    sku=str(row.get("sku")) if pd.notna(row.get("sku")) else None,
                    description=str(row.get("description")) if pd.notna(row.get("description")) else None,
                )
        if "contracts" in xls.sheet_names:
            df = xls.parse("contracts")
            ensure_unique(df["contract_number"], "contract", "contract_number")
            for _, row in df.iterrows():
                start_date = str(row.get("start_date", "")).strip()
                end_date = str(row.get("end_date")) if pd.notna(row.get("end_date")) else None
                parse_iso_date(start_date)
                if end_date:
                    parse_iso_date(end_date)
                self.contracts_service.create_contract(
                    contract_number=str(row.get("contract_number", "")).strip(),
                    customer=str(row.get("customer", "")).strip(),
                    start_date=start_date,
                    end_date=end_date,
                    status=str(row.get("status", "active")) or "active",
                )