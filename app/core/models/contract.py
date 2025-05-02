"""
File: app/core/models/contract.py
Модель данных для контрактов.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional
from app.core.models.base_model import BaseModel

class Contract(BaseModel):
    """Модель данных для контрактов."""

    def __init__(
        self,
        contract_number: str,
        start_date: date,
        end_date: date,
        description: str = "",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Инициализация модели контракта.

        Args:
            contract_number: Шифр контракта
            start_date: Дата начала
            end_date: Дата окончания
            description: Описание контракта
            id: Идентификатор контракта
            created_at: Дата создания
            updated_at: Дата последнего обновления
        """
        super().__init__(id)
        self.contract_number = contract_number
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Валидирует данные контракта."""
        if not self.contract_number.strip():
            raise ValueError("Шифр контракта обязателен")

        if self.start_date > self.end_date:
            raise ValueError("Дата начала не может быть позже даты окончания")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            "id": self.id,
            "contract_number": self.contract_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "created_at": self._created_at.isoformat() if self._created_at else None,
            "updated_at": self._updated_at.isoformat() if self._updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contract':
        """Создает модель из словаря."""
        return cls(
            id=data.get("id"),
            contract_number=data["contract_number"],
            start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )

    def __str__(self) -> str:
        """Возвращает строковое представление контракта."""
        return f"{self.contract_number} ({self.start_date.year}-{self.end_date.year})"

    @property
    def duration_days(self) -> int:
        """Возвращает длительность контракта в днях."""
        return (self.end_date - self.start_date).days

    @property
    def is_active(self) -> bool:
        """Проверяет, активен ли контракт."""
        today = date.today()
        return self.start_date <= today <= self.end_date