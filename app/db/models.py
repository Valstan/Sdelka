from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class Worker:
    id: Optional[int]
    last_name: str
    first_name: str
    middle_name: Optional[str]
    position: Optional[str]
    phone: Optional[str]
    hire_date: Optional[str]
    is_active: int = 1


@dataclass(slots=True)
class JobType:
    id: Optional[int]
    name: str
    unit: str
    base_rate: float


@dataclass(slots=True)
class Product:
    id: Optional[int]
    name: str
    sku: Optional[str]
    description: Optional[str]


@dataclass(slots=True)
class Contract:
    id: Optional[int]
    contract_number: str
    customer: str
    start_date: str
    end_date: Optional[str]
    status: str = "active"


@dataclass(slots=True)
class WorkOrder:
    id: Optional[int]
    contract_id: int
    worker_id: int
    job_type_id: int
    product_id: Optional[int]
    date: str
    quantity: float
    unit_rate: float
    amount: float
    notes: Optional[str]