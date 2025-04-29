# File: app/models/work_card_item.py
"""
Модель для представления элементов карточки работы.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkCardItem:
    """
    Модель для представления элемента карточки работы.

    Attributes:
        id: Уникальный идентификатор элемента
        card_id: ID карточки работы
        work_type_id: ID вида работы
        quantity: Количество выполненных работ
        amount: Сумма
        created_at: Дата создания записи
    """

    id: Optional[int] = None
    card_id: int = 0
    work_type_id: int = 0
    quantity: int = 0
    amount: float = 0.0
    created_at: Optional[datetime] = None