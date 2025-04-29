# File: app/models/work_card.py
"""
Модель для представления данных о карточке работы.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List


@dataclass
class WorkCard:
    """
    Модель для представления данных о карточке работы.

    Attributes:
        id: Уникальный идентификатор карточки
        card_number: Номер карточки
        card_date: Дата карточки
        product_id: ID изделия
        contract_id: ID контракта
        total_amount: Общая сумма
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
        items: Элементы карточки работы
        workers: Работники, участвующие в работе
    """

    id: Optional[int] = None
    card_number: str = ""
    card_date: date = date.today()
    product_id: int = 0
    contract_id: int = 0
    total_amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List['WorkCardItem'] = None
    workers: List['WorkerAssignment'] = None

    def calculate_total_amount(self) -> float:
        """
        Рассчитывает общую сумму карточки на основе элементов работы.

        Returns:
            Общая сумма
        """
        if not self.items:
            return 0.0

        self.total_amount = sum(item.amount for item in self.items)
        return self.total_amount

    def calculate_worker_amount(self) -> float:
        """
        Рассчитывает сумму для каждого работника.

        Returns:
            Сумма для каждого работника
        """
        if not self.workers or self.total_amount <= 0:
            return 0.0

        return round(self.total_amount / len(self.workers), 2)