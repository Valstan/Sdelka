"""
Модель вида работы
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.core.models.base import BaseModel


@dataclass
class WorkType(BaseModel):
    """
    Модель вида работы

    Attributes:
        name: Наименование работы
        unit: Единица измерения ('штуки', 'комплекты')
        price: Цена (в рублях)
        valid_from: Дата начала действия цены
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    name: str = ""
    unit: str = "штуки"
    price: float = 0.0
    valid_from: Optional[date] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __post_init__(self):
        """Инициализация при создании объекта"""
        if not self.created_at:
            self.created_at = date.today()
        self.updated_at = date.today()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Проверяет валидность данных вида работы

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
        Возвращает строковое представление вида работы

        Returns:
            str: Наименование работы и цена
        """
        return f"{self.name} ({self.unit}, {self.price} руб.)"

    def __eq__(self, other: object) -> bool:
        """
        Сравнивает два экземпляра WorkType

        Args:
            other: Объект для сравнения

        Returns:
            bool: True, если объекты равны
        """
        if not isinstance(other, WorkType):
            return False

        return (
            self.name == other.name and
            self.unit == other.unit and
            self.price == other.price and
            self.valid_from == other.valid_from
        )

    def __hash__(self) -> int:
        """
        Возвращает хэш-значение для экземпляра WorkType

        Returns:
            int: Хэш-значение
        """
        return hash((
            self.name,
            self.unit,
            self.price,
            self.valid_from
        ))