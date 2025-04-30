"""
File: app/core/models/work_card_worker.py
Модель работника по наряду.
"""

from typing import Any, Dict
from datetime import date, datetime
from app.core.models.base_model import BaseModel


class WorkCardWorker(BaseModel):
    """
    Модель работника по наряду.

    Attributes:
        work_card_id: ID наряда
        worker_id: ID работника
        amount: Сумма для работника
        last_name: Фамилия работника
        first_name: Имя работника
        middle_name: Отчество работника
    """

    def __init__(
            self,
            id: int = None,
            work_card_id: int = None,
            worker_id: int = None,
            amount: float = 0.0,
            last_name: str = "",
            first_name: str = "",
            middle_name: str = "",
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.work_card_id = work_card_id
        self.worker_id = worker_id
        self.amount = amount
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Проверяет корректность данных работника."""
        if self.amount < 0:
            raise ValueError("Сумма не может быть отрицательной")

        if self.worker_id is None:
            raise ValueError("Работник не выбран")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров WorkCardWorker."""
        if not isinstance(other, WorkCardWorker):
            return False

        return self.worker_id == other.worker_id

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.last_name} {self.first_name} - {self.amount:.2f} руб."

    def full_name(self) -> str:
        """Полное имя работника."""
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    def short_name(self) -> str:
        """Краткое имя для отображения."""
        return f"{self.last_name} {self.first_name[0]}."