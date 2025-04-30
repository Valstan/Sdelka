"""
File: app/core/models/work_type.py
Модель вида работы с валидацией и бизнес-логикой.
"""

from typing import Any, Dict
from datetime import date, datetime
from app.core.models.base_model import BaseModel


class WorkType(BaseModel):
    """
    Модель вида работы.

    Attributes:
        id: Уникальный идентификатор вида работы
        name: Название вида работы
        unit: Единица измерения (штуки, комплекты)
        price: Цена за единицу
        valid_from: Дата начала действия цены
    """

    def __init__(
            self,
            id: int = None,
            name: str = "",
            unit: str = "штуки",
            price: float = 0.0,
            valid_from: date = None,
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.name = name
        self.unit = unit
        self.price = price
        self.valid_from = valid_from or date.today()
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Валидирует данные вида работы."""
        if not self.name.strip():
            raise ValueError("Название вида работы обязательно")

        if self.unit not in ("штуки", "комплекты"):
            raise ValueError("Недопустимая единица измерения")

        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")

        if self.valid_from < date(2000, 1, 1):
            raise ValueError("Дата начала действия слишком ранняя")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров WorkType."""
        if not isinstance(other, WorkType):
            return False

        return self.name == other.name and self.unit == other.unit

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.name} ({self.unit}, {self.price} руб.)"

    def get_display_name(self) -> str:
        """Возвращает форматированное имя для отображения."""
        return f"{self.name} ({self.unit}, {self.price:.2f} руб.)"