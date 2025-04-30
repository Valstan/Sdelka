"""
File: app/core/models/product.py
Модель изделия с валидацией и бизнес-логикой.
"""

from typing import Any, Dict
from datetime import datetime
from app.core.models.base_model import BaseModel


class Product(BaseModel):
    """
    Модель изделия.

    Attributes:
        id: Уникальный идентификатор изделия
        product_code: Шифр изделия
        name: Наименование изделия
    """

    def __init__(
            self,
            id: int = None,
            product_code: str = "",
            name: str = "",
            created_at: datetime = None,
            updated_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.product_code = product_code
        self.name = name
        self._created_at = created_at
        self._updated_at = updated_at

    def validate(self) -> bool:
        """Валидирует данные изделия."""
        if not self.product_code.strip():
            raise ValueError("Шифр изделия обязателен")

        if not self.name.strip():
            raise ValueError("Наименование изделия обязательно")

        return True

    def set_updated(self) -> None:
        """Обновляет метку времени при изменении."""
        self._updated_at = datetime.now()

    def __eq__(self, other: Any) -> bool:
        """Сравнение двух экземпляров Product."""
        if not isinstance(other, Product):
            return False

        return self.product_code == other.product_code

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.product_code} - {self.name}"

    def get_display_name(self) -> str:
        """Возвращает форматированное имя для отображения."""
        return f"{self.product_code} - {self.name[:30]}..."