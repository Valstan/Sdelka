"""
File: app/core/models/work_card.py
Модель наряда работ с валидацией и бизнес-логикой.
"""

from typing import Any, Dict, List
from datetime import date, datetime
from app.core.models.base_model import BaseModel
from app.core.models.work_card_item import WorkCardItem
from app.core.models.work_card_worker import WorkCardWorker


class WorkCard(BaseModel):
    """
    Модель наряда работ.

    Attributes:
        id: Уникальный идентификатор наряда
        card_number: Номер наряда
        card_date: Дата наряда
        product_id: ID изделия (по справочнику)
        contract_id: ID контракта (по справочнику)
        workers: Список работников по наряду
        items: Список выполненных работ
        total_amount: Общая сумма по наряду
    """

    def __init__(
            self,
            id: int = None,
            card_number: str = "",
            card_date: date = None,
            product_id: int = None,
            contract_id: int = None,
            workers: List[WorkCardWorker] = None,
            items: List[WorkCardItem] = None,
            total_amount: float = 0.0,
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.card_number = card_number
        self.card_date = card_date or date.today()
        self.product_id = product_id
        self.contract_id = contract_id
        self.workers = workers or []
        self.items = items or []
        self.total_amount = total_amount
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Проверяет корректность данных наряда."""
        if not self.card_number.strip():
            raise ValueError("Номер наряда обязателен")

        if self.card_date > date.today():
            raise ValueError("Дата наряда не может быть в будущем")

        if self.product_id is None:
            raise ValueError("Не выбрано изделие")

        if self.contract_id is None:
            raise ValueError("Не выбран контракт")

        if not self.workers:
            raise ValueError("В наряде должен быть хотя бы один работник")

        if not self.items:
            raise ValueError("В наряде должна быть хотя бы одна работа")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров WorkCard."""
        if not isinstance(other, WorkCard):
            return False

        return self.card_number == other.card_number

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"Наряд {self.card_number} от {self.card_date.strftime('%d.%m.%Y')} - {self.total_amount:.2f} руб."

    def calculate_total_amount(self) -> float:
        """Рассчитывает общую сумму по наряду."""
        return sum(item.amount for item in self.items)

    def calculate_worker_amount(self) -> float:
        """Рассчитывает сумму каждому работнику."""
        if not self.items or not self.workers:
            return 0.0

        return self.total_amount / len(self.workers)

    def add_worker(self, worker: WorkCardWorker) -> None:
        """Добавляет работника в наряд."""
        if not any(w.worker_id == worker.worker_id for w in self.workers):
            self.workers.append(worker)
            self.update_worker_amounts()

    def remove_worker(self, worker_index: int) -> None:
        """Удаляет работника из наряда."""
        if 0 <= worker_index < len(self.workers):
            self.workers.pop(worker_index)
            self.update_worker_amounts()

    def add_work_item(self, item: WorkCardItem) -> None:
        """Добавляет элемент работы в наряд."""
        self.items.append(item)
        self.total_amount = self.calculate_total_amount()
        self.update_worker_amounts()

    def remove_work_item(self, item_index: int) -> None:
        """Удаляет элемент работы из наряда."""
        if 0 <= item_index < len(self.items):
            self.items.pop(item_index)
            self.total_amount = self.calculate_total_amount()
            self.update_worker_amounts()

    def update_worker_amounts(self) -> None:
        """Обновляет сумму для каждого работника в наряде."""
        if not self.items:
            worker_amount = 0.0
        else:
            worker_amount = self.calculate_worker_amount()

        for worker in self.workers:
            worker.amount = worker_amount

    def get_display_name(self) -> str:
        """Возвращает форматированное имя для отображения."""
        return f"{self.card_number} ({self.card_date.strftime('%d.%m.%Y')})"