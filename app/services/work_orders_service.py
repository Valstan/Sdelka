from __future__ import annotations

from app.db.models import WorkOrder
from app.services.common import BaseService
from app.utils.validators import parse_iso_date, require_non_negative, require_positive


class WorkOrdersService(BaseService):
    def create_work_order(
        self,
        contract_id: int,
        worker_id: int,
        job_type_id: int,
        product_id: int | None,
        date: str,
        quantity: float,
        unit_rate: float,
        notes: str | None = None,
    ) -> int:
        parse_iso_date(date)
        require_positive(quantity, "quantity")
        require_non_negative(unit_rate, "unit_rate")
        amount = round(quantity * unit_rate, 2)
        work_order = WorkOrder(
            id=None,
            contract_id=contract_id,
            worker_id=worker_id,
            job_type_id=job_type_id,
            product_id=product_id,
            date=date,
            quantity=quantity,
            unit_rate=unit_rate,
            amount=amount,
            notes=notes,
        )
        return self.repository.add_work_order(work_order)

    def list_work_orders(self) -> list[dict]:
        return self.repository.list_work_orders()

    def filter_work_orders(self, start_date: str, end_date: str, worker_id: int | None = None, contract_id: int | None = None) -> list[dict]:
        return self.repository.filter_work_orders(start_date, end_date, worker_id, contract_id)