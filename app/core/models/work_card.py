"""
Модель наряда работы
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List
from app.core.models.base import BaseModel
from app.core.models.work_card_item import WorkCardItem


@dataclass
class WorkCard(BaseModel):
    """
    Модель наряда работы

    Attributes:
        card_number: Номер наряда
        card_date: Дата наряда
        product_id: ID изделия
        contract_id: ID контракта
        total_amount: Итоговая сумма карточки в рублях
        items: Список элементов наряда (работ)
        worker_ids: Список ID работников бригады
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    card_number: str = ""
    card_date: Optional[date] = None
    product_id: int = 0
    contract_id: int = 0
    total_amount: float = 0.0
    items: List[WorkCardItem] = None
    worker_ids: List[int] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        super().__post_init__()

        if self.items is None:
            self.items = []

        if self.worker_ids is None:
            self.worker_ids = []

        if not self.card_date:
            self.card_date = date.today()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных наряда

        Returns:
            tuple[bool, list[str]]: (успех, список ошибок)
        """
        pass

    def update_timestamp(self) -> None:
        """
        Обновляет метку времени при изменении данных
        """
        self.updated_at = date.today()

    def calculate_worker_amounts(self) -> dict[int, float]:
        """
        Рассчитывает сумму для каждого работника бригады

        Returns:
            dict[int, float]: Словарь с ID работника и суммой
        """
        worker_amounts = {}

        if not self.worker_ids:
            return worker_amounts

        worker_count = len(self.worker_ids)
        if worker_count == 0:
            return worker_amounts

        amount_per_worker = self.total_amount / worker_count

        for worker_id in self.worker_ids:
            worker_amounts[worker_id] = amount_per_worker

        return worker_amounts

    def add_item(self, item: WorkCardItem) -> None:
        """
        Добавляет элемент наряда

        Args:
            item: Элемент наряда
        """
        if item.work_card_id and item.work_card_id != self.id:
            raise ValueError("Элемент принадлежит другому наряду")

        item.work_card_id = self.id
        self.items.append(item)
        self._recalculate_total()

    def remove_item(self, item: WorkCardItem) -> None:
        """
        Удаляет элемент наряда

        Args:
            item: Элемент наряда
        """
        if item in self.items:
            self.items.remove(item)
            self._recalculate_total()

    def _recalculate_total(self) -> None:
        """
        Пересчитывает общую сумму наряда
        """
        self.total_amount = sum(item.amount for item in self.items)

    def __str__(self) -> str:
        """
        Возвращает строковое представление наряда

        Returns:
            str: Номер наряда и дата
        """
        return f"{self.card_number} ({self.card_date})"

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра WorkCard

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекты равны
        """
        if not isinstance(other, WorkCard):
            return False

        return (
            self.card_number == other.card_number and
            self.card_date == other.card_date and
            self.product_id == other.product_id and
            self.contract_id == other.contract_id
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра WorkCard

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.card_number,
            self.card_date,
            self.product_id,
            self.contract_id
        ))