"""
File: app/core/models/worker.py
Модель работника предприятия.
"""

from typing import Any, Dict
from datetime import datetime
from app.core.models.base_model import BaseModel


class Worker(BaseModel):
    """
    Модель работника предприятия.

    Attributes:
        id: Уникальный идентификатор работника
        last_name: Фамилия
        first_name: Имя
        middle_name: Отчество
        workshop_number: Номер цеха
        position: Должность
        employee_id: Табельный номер
    """

    def __init__(
            self,
            id: int = None,
            last_name: str = "",
            first_name: str = "",
            middle_name: str = "",
            workshop_number: int = 1,
            position: str = "",
            employee_id: str = "",
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.workshop_number = workshop_number
        self.position = position
        self.employee_id = employee_id
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Валидирует данные работника."""
        if not self.last_name.strip():
            raise ValueError("Фамилия работника обязательна")

        if not self.first_name.strip():
            raise ValueError("Имя работника обязательно")

        if not self.employee_id.strip():
            raise ValueError("Табельный номер обязателен")

        if self.workshop_number < 1:
            raise ValueError("Номер цеха должен быть положительным числом")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров Worker."""
        if not isinstance(other, Worker):
            return False

        return self.employee_id == other.employee_id

    def full_name(self) -> str:
        """Возвращает полное имя работника."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(f"{self.middle_name[0]}.")
        return " ".join(parts)

    def short_name(self) -> str:
        """Краткое имя для отображения в списках."""
        return f"{self.last_name} {self.first_name[0]}."