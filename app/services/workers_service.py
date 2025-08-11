from __future__ import annotations

from app.db.models import Worker
from app.services.common import BaseService
from app.utils.validators import ValidationError, ensure_unique, parse_iso_date


class WorkersService(BaseService):
    def create_worker(
        self,
        last_name: str,
        first_name: str,
        middle_name: str | None = None,
        position: str | None = None,
        phone: str | None = None,
        hire_date: str | None = None,
    ) -> int:
        if hire_date:
            parse_iso_date(hire_date)
        worker = Worker(
            id=None,
            last_name=last_name.strip(),
            first_name=first_name.strip(),
            middle_name=middle_name.strip() if middle_name else None,
            position=position.strip() if position else None,
            phone=phone.strip() if phone else None,
            hire_date=hire_date,
            is_active=1,
        )
        return self.repository.add_worker(worker)

    def list_workers(self, active_only: bool = False) -> list[dict]:
        return self.repository.list_workers(active_only=active_only)