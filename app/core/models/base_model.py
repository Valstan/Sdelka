"""
File: app/core/models/base_model.py
Базовый класс для всех моделей данных.
"""

from abc import ABC
from typing import Any, Dict, Optional
from datetime import date, datetime

class BaseModel(ABC):
    """Абстрактный базовый класс для всех моделей данных."""

    def __init__(self, id: Optional[int] = None):
        """
        Инициализация базовой модели.

        Args:
            id: Идентификатор записи в БД
        """
        self.id = id
        self._created_at = None
        self._updated_at = None

    @property
    def created_at(self) -> Optional[datetime]:
        """Возвращает дату создания записи."""
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        """Возвращает дату последнего обновления записи."""
        return self._updated_at

    def validate(self) -> bool:
        """Валидирует данные модели."""
        raise NotImplementedError("Метод validate должен быть реализован в подклассе")

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        raise NotImplementedError("Метод to_dict должен быть реализован в подклассе")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Создает модель из словаря."""
        raise NotImplementedError("Метод from_dict должен быть реализован в подклассе")

    def __eq__(self, other: Any) -> bool:
        """Сравнивает две модели."""
        if not isinstance(other, self.__class__):
            return False

        if self.id is None or other.id is None:
            return self is other

        return self.id == other.id

    def __hash__(self) -> int:
        """Возвращает хэш модели."""
        if self.id is not None:
            return hash((self.__class__, self.id))
        return hash(self)