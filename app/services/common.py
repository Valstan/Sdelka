from __future__ import annotations

from app.db.repository import Repository
from app.utils.validators import ValidationError


class ServiceError(Exception):
    """Raised for service-layer errors."""


class BaseService:
    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def _raise(self, message: str) -> None:
        raise ServiceError(message)