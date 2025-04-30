"""
File: app/core/models/base_model.py
Базовая модель с общими методами для всех моделей данных.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
import logging
import abc

logger = logging.getLogger(__name__)


class BaseModel(abc.ABC):
    """
    Абстрактный базовый класс для всех моделей.
    Содержит общую функциональность: валидацию, сериализацию, логирование.
    """

    def __init__(self):
        self._dirty_fields: Dict[str, Any] = {}
        self._created_at: Optional[datetime] = None
        self._updated_at: Optional[datetime] = None

    @property
    def created_at(self) -> Optional[datetime]:
        """Возвращает дату создания записи."""
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        """Возвращает дату последнего обновления."""
        return self._updated_at

    @abc.abstractmethod
    def validate(self) -> bool:
        """Проверяет корректность данных модели."""
        pass

    def mark_field_changed(self, field_name: str, value: Any) -> None:
        """Отмечает поле как измененное."""
        self._dirty_fields[field_name] = value

    def get_dirty_fields(self) -> Dict[str, Any]:
        """Возвращает измененные поля."""
        return self._dirty_fields

    def reset_dirty_fields(self) -> None:
        """Сбрасывает список измененных полей."""
        self._dirty_fields.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        result = {
            "created_at": self._created_at,
            "updated_at": self._updated_at
        }
        for k, v in self.__dict__.items():
            if not k.startswith('_'):
                result[k] = v
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Создает объект из словаря."""
        instance = cls()
        for k, v in data.items():
            setattr(instance, k, v)
        return instance

    def __str__(self) -> str:
        """Человеко-понятное представление модели."""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return f"<{self.__class__.__name__} {self.to_dict()}>"