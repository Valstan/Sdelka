"""
Модель работника предприятия
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.core.models.base import BaseModel
from app.utils.validators.validators import WorkerValidator


@dataclass
class Worker(BaseModel):
    """
    Модель работника предприятия

    Attributes:
        last_name: Фамилия работника
        first_name: Имя работника
        middle_name: Отчество работника
        employee_id: Табельный номер
        workshop_number: Номер цеха
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    employee_id: int = 0
    workshop_number: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных работника

        Returns:
            tuple[bool, list[str]]: (успех, список ошибок)
        """
        validator = WorkerValidator()
        return validator.validate_worker(self)

    def get_full_name(self) -> str:
        """
        Возвращает полное имя работника

        Returns:
            str: Полное имя в формате "Фамилия И.О."
        """
        if self.middle_name:
            return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}."
        return f"{self.last_name} {self.first_name[0]}."

    def update_timestamp(self) -> None:
        """
        Обновляет метку времени при изменении данных
        """
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        """
        Возвращает строковое представление работника

        Returns:
            str: Полное имя работника
        """
        return self.get_full_name()

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра Worker

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекти равны
        """
        if not isinstance(other, Worker):
            return False

        return (
            self.employee_id == other.employee_id and
            self.last_name == other.last_name and
            self.first_name == other.first_name and
            self.middle_name == other.middle_name and
            self.workshop_number == other.workshop_number
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра Worker

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.employee_id,
            self.last_name,
            self.first_name,
            self.middle_name,
            self.workshop_number
        ))