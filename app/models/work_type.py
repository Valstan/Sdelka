# File: app/models/work_type.py
"""
Модель для представления данных о виде работы.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class WorkType:
    """
    Модель для представления данных о виде работы.

    Attributes:
        id: Уникальный идентификатор вида работы
        name: Наименование работы
        unit: Единица измерения
        price: Цена за единицу
        valid_from: Дата начала действия цены
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    id: Optional[int] = None
    name: str = ""
    unit: str = ""
    price: float = 0.0
    valid_from: date = date.today()
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        """
        Возвращает отображаемое имя вида работы.

        Returns:
            Отображаемое имя вида работы
        """
        return f"{self.name} ({self.unit}, {self.price} руб.)"