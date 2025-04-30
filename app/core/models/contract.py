"""
File: app/core/models/contract.py
Модель контракта с валидацией и бизнес-логикой.
"""

from typing import Any, Dict
from datetime import date, datetime
from app.core.models.base_model import BaseModel


class Contract(BaseModel):
    """
    Модель контракта.

    Attributes:
        id: Уникальный идентификатор контракта
        contract_number: Шифр контракта
        start_date: Дата начала действия
        end_date: Дата окончания действия
        description: Описание контракта
    """

    def __init__(
            self,
            id: int = None,
            contract_number: str = "",
            start_date: date = None,
            end_date: date = None,
            description: str = "",
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.contract_number = contract_number
        self.start_date = start_date or date.today()
        self.end_date = end_date or date(date.today().year, 12, 31)
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

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров Contract."""
        if not isinstance(other, Contract):
            return False

        return self.contract_number == other.contract_number

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.contract_number} ({self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')})"

    def get_display_name(self) -> str:
        """Возвращает форматированное имя для отображения."""
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