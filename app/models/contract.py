# File: app/models/contract.py
"""
Модель для представления данных о контракте.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Contract:
    """
    Модель для представления данных о контракте.

    Attributes:
        id: Уникальный идентификатор контракта
        contract_number: Шифр контракта
        start_date: Дата начала
        end_date: Дата окончания
        description: Описание контракта
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    id: Optional[int] = None
    contract_number: str = ""
    start_date: date = date.today()
    end_date: date = date.today()
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def duration_days(self) -> int:
        """
        Возвращает длительность контракта в днях.

        Returns:
            Длительность в днях
        """
        return (self.end_date - self.start_date).days

    @property
    def is_active(self) -> bool:
        """
        Проверяет, активен ли контракт.

        Returns:
            True, если контракт активен
        """
        today = date.today()
        return self.start_date <= today <= self.end_date