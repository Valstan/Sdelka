"""
Модель контракта
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.core.models.base import BaseModel


@dataclass
class Contract(BaseModel):
    """
    Модель контракта

    Attributes:
        contract_number: Шифр контракта
        start_date: Дата начала
        end_date: Дата окончания
        description: Описание контракта
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    contract_number: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: str = ""
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        if not self.created_at:
            self.created_at = date.today()
        self.updated_at = date.today()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных контракта

        Returns:
            tuple[bool, list[str]]: (успех, список ошибок)
        """
        pass

    def update_timestamp(self) -> None:
        """
        Обновляет метку времени при изменении данных
        """
        self.updated_at = date.today()

    def __str__(self) -> str:
        """
        Возвращает строковое представление контракта

        Returns:
            str: Шифр контракта и период действия
        """
        if self.start_date and self.end_date:
            return f"{self.contract_number} ({self.start_date.year}-{self.end_date.year})"
        return self.contract_number

    @property
    def duration_days(self) -> int:
        """
        Возвращает длительность контракта в днях

        Returns:
            int: Количество дней действия контракта
        """
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    @property
    def is_active(self) -> bool:
        """
        Проверяет, активен ли контракт

        Returns:
            bool: True, если контракт активен
        """
        today = date.today()
        if not self.start_date or not self.end_date:
            return False
        return self.start_date <= today <= self.end_date

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра Contract

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекты равны
        """
        if not isinstance(other, Contract):
            return False

        return (
                self.contract_number == other.contract_number and
                self.start_date == other.start_date and
                self.end_date == other.end_date
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра Contract

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.contract_number,
            self.start_date,
            self.end_date
        ))