"""
Модель элемента наряда работы
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.core.models.base import BaseModel


@dataclass
class WorkCardItem(BaseModel):
    """
    Модель элемента наряда работы

    Attributes:
        work_card_id: ID наряда
        work_type_id: ID вида работы
        quantity: Количество выполненных работ
        amount: Сумма в рублях
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    work_card_id: int = 0
    work_type_id: int = 0
    quantity: int = 0
    amount: float = 0.0
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        if not self.created_at:
            self.created_at = date.today()
        self.updated_at = date.today()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных элемента наряда

        Returns:
            tuple[bool, list[str]]: (успех, список ошибок)
        """
        pass

    def update_timestamp(self) -> None:
        """
        Обновляет метку времени при изменении данных
        """
        self.updated_at = date.today()

    def calculate_amount(self, work_type_price: float) -> float:
        """
        Рассчитывает сумму для элемента наряда

        Args:
            work_type_price: Цена вида работы

        Returns:
            float: Рассчитанная сумма
        """
        if self.quantity <= 0:
            raise ValueError("Количество должно быть положительным числом")

        if work_type_price <= 0:
            raise ValueError("Цена вида работы должна быть положительной")

        self.amount = self.quantity * work_type_price
        return self.amount

    def __str__(self) -> str:
        """
        Возвращает строковое представление элемента наряда

        Returns:
            str: Описание элемента наряда
        """
        return f"{self.quantity} x {self.amount / self.quantity if self.quantity > 0 else 0} руб. = {self.amount} руб."

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра WorkCardItem

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекты равны
        """
        if not isinstance(other, WorkCardItem):
            return False

        return (
            self.work_card_id == other.work_card_id and
            self.work_type_id == other.work_type_id and
            self.quantity == other.quantity and
            self.amount == other.amount
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра WorkCardItem

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.work_card_id,
            self.work_type_id,
            self.quantity,
            self.amount
        ))