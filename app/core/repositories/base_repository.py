"""
Базовый класс репозитория
"""

from typing import Optional, List, TypeVar, Generic, Type, Tuple
from dataclasses import dataclass
from app.core.models.base import BaseModel
from app.utils.exceptions import DatabaseError
from app.utils.validators.common_validators import common_validators

T = TypeVar('T', bound=BaseModel)


@dataclass
class BaseRepository(Generic[T]):
    """
    Базовый класс репозитория для всех сущностей
    """

    model_class: Type[T]

    def create(self, model: T) -> Tuple[bool, Optional[T], List[str]]:
        """
        Создает новую запись в БД

        Args:
            model: Модель данных

        Returns:
            Tuple[bool, Optional[T], List[str]]: (успех, созданная модель, список ошибок)
        """
        raise NotImplementedError("Метод create должен быть реализован в подклассе")

    def update(self, model: T) -> Tuple[bool, Optional[T], List[str]]:
        """
        Обновляет существующую запись в БД

        Args:
            model: Модель данных

        Returns:
            Tuple[bool, Optional[T], List[str]]: (успех, обновленная модель, список ошибок)
        """
        raise NotImplementedError("Метод update должен быть реализован в подклассе")

    def delete(self, model_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет запись из БД

        Args:
            model_id: ID записи

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        raise NotImplementedError("Метод delete должен быть реализован в подклассе")

    def get_by_id(self, model_id: int) -> Optional[T]:
        """
        Получает запись из БД по ID

        Args:
            model_id: ID записи

        Returns:
            Optional[T]: Модель данных или None
        """
        raise NotImplementedError("Метод get_by_id должен быть реализован в подклассе")

    def get_all(self) -> List[T]:
        """
        Получает все записи из БД

        Returns:
            List[T]: Список моделей данных
        """
        raise NotImplementedError("Метод get_all должен быть реализован в подклассе")

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование записи по ID

        Args:
            model_id: ID записи

        Returns:
            bool: True, если запись существует
        """
        raise NotImplementedError("Метод exists должен быть реализован в подклассе")

    def search(self, **kwargs) -> List[T]:
        """
        Выполняет поиск записей по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            List[T]: Список найденных моделей
        """
        raise NotImplementedError("Метод search должен быть реализован в подклассе")

    def validate_model(self, model: T) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность модели

        Args:
            model: Модель данных

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        return model.validate()