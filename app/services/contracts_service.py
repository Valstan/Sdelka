from __future__ import annotations

from app.db.models import Contract
from app.services.common import BaseService
from app.utils.validators import parse_iso_date


class ContractsService(BaseService):
    def create_contract(
        self,
        contract_number: str,
        customer: str,
        start_date: str,
        end_date: str | None = None,
        status: str = "active",
    ) -> int:
        parse_iso_date(start_date)
        if end_date:
            parse_iso_date(end_date)
        contract = Contract(
            id=None,
            contract_number=contract_number.strip(),
            customer=customer.strip(),
            start_date=start_date,
            end_date=end_date,
            status=status,
        )
        return self.repository.add_contract(contract)

    def list_contracts(self) -> list[dict]:
        return self.repository.list_contracts()