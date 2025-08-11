from __future__ import annotations

from app.db.models import JobType
from app.services.common import BaseService
from app.utils.validators import require_non_negative


class JobTypesService(BaseService):
    def create_job_type(self, name: str, unit: str, base_rate: float) -> int:
        require_non_negative(base_rate, "base_rate")
        job_type = JobType(id=None, name=name.strip(), unit=unit.strip(), base_rate=base_rate)
        return self.repository.add_job_type(job_type)

    def list_job_types(self) -> list[dict]:
        return self.repository.list_job_types()