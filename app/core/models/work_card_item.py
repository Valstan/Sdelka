"""
File: app/core/models/work_card_item.py
Модель элемента наряда (каждый вид работы).
"""

from typing import Any, Dict
from datetime import date, datetime
from app.core.models.base_model import BaseModel


class WorkCardItem(BaseModel):
    """
    Модель элемента наряда (каждый вид работы).

    Attributes:
        work_card_id: ID наряда
        work_type_id: ID вида работы
        quantity: Количество выполненных работ
        amount: Сумма для элемента
    """

    def __init__(
            self,
            id: int = None,
            work_card_id: int = None,
            work_type_id: int = None,
            quantity: int = 1,
            amount: float = 0.0,
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.work_card_id = work_card_id
        self.work_type_id = work_type_id
        self.quantity = quantity
        self.amount = amount
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Проверяет корректность элемента работы."""
        if self.quantity <= 0:
            raise ValueError("Количество должно быть положительным")

        if self.amount < 0:
            raise ValueError("Сумма не может быть отрицательной")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров WorkCardItem."""
        if not isinstance(other, WorkCardItem):
            return False

        return self.id == other.id if self.id else self is other

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.quantity} x {self.amount / self.quantity:.2f} руб. = {self.amount:.2f} руб."