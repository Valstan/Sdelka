"""
Модель изделия
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.core.models.base import BaseModel


@dataclass
class Product(BaseModel):
    """
    Модель изделия

    Attributes:
        name: Наименование изделия
        code: Номер изделия (уникальный)
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    name: str = ""
    code: str = ""
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        if not self.created_at:
            self.created_at = date.today()
        self.updated_at = date.today()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных изделия

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
        Возвращает строковое представление изделия

        Returns:
            str: Наименование изделия и его код
        """
        return f"{self.name} ({self.code})"

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра Product

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекты равны
        """
        if not isinstance(other, Product):
            return False

        return (
            self.code == other.code and
            self.name == other.name
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра Product

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.code,
            self.name
        ))