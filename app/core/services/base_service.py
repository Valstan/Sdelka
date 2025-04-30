"""
File: app/core/services/base_service.py
Базовый сервис с общими операциями для всех сервисов.
"""

from typing import Any, Dict, List, Optional, Tuple, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from sqlite3 import Connection, Row
from app.core.database.connections import DatabaseManager
from app.core.models.base_model import BaseModel

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Базовый класс для всех сервисов.
    Реализует общие методы работы с базой данных.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    @abstractmethod
    def model_class(self) -> type:
        """Возвращает класс модели, с которой работает сервис."""
        pass

    def _execute_query(
            self,
            query: str,
            params: tuple = (),
            fetch_one: bool = False,
            commit: bool = False
    ) -> Optional[Any]:
        """
        Выполняет SQL-запрос.

        Args:
            query: SQL-запрос
            params: Параметры запроса
            fetch_one: Вернуть одну запись?
            commit: Выполнить коммит после выполнения?

        Returns:
            Результат выполнения запроса или None
        """
        try:
            with self.db_manager.connect() as conn:
                conn.row_factory = Row
                cursor = conn.cursor()
                cursor.execute(query, params)

                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()

                if commit:
                    conn.commit()

                return result

        except Exception as e:
            logger.error(f"Ошибка выполнения SQL-запроса: {e}", exc_info=True)
            raise

    def _map_to_model(self, row: Dict[str, Any]) -> T:
        """
        Преобразует строку базы данных в модель.

        Args:
            row: Строка результата запроса

        Returns:
            Экземпляр модели
        """
        model_data = dict(row)

        # Преобразование временных меток
        for field in ['created_at', 'updated_at']:
            if field in model_data and isinstance(model_data[field], str):
                try:
                    model_data[field] = datetime.fromisoformat(model_data[field])
                except ValueError:
                    model_data[field] = datetime.strptime(model_data[field], "%Y-%m-%d %H:%M:%S")

        return self.model_class()(**model_data)

    def get_all(self) -> List[T]:
        """Возвращает все записи из таблицы."""
        query = f"SELECT * FROM {self.table_name}"
        rows = self._execute_query(query)
        return [self._map_to_model(row) for row in rows]

    def get_by_id(self, item_id: int) -> Optional[T]:
        """Возвращает запись по ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id=?"
        row = self._execute_query(query, (item_id,), fetch_one=True)
        return self._map_to_model(row) if row else None

    def delete(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет запись по ID.

        Args:
            item_id: ID записи

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id=?"
            self._execute_query(query, (item_id,), commit=True)
            return True, None
        except Exception as e:
            return False, str(e)

    def save(self, model: T) -> Tuple[bool, Optional[int]]:
        """
        Сохраняет модель в базе данных.

        Args:
            model: Экземпляр модели

        Returns:
            Кортеж (успех, ID новой записи)
        """
        if not model.validate():
            return False, None

        try:
            if model.id:
                success, message = self.update(model)
                return success, model.id
            else:
                return self.create(model)
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}", exc_info=True)
            return False, None

    def create(self, model: T) -> Tuple[bool, Optional[int]]:
        """
        Создает новую запись.

        Args:
            model: Экземпляр модели

        Returns:
            Кортеж (успех, ID новой записи)
        """
        raise NotImplementedError("Метод create должен быть реализован в подклассе")

    def update(self, model: T) -> Tuple[bool, Optional[str]]:
        """
        Обновляет существующую запись.

        Args:
            model: Экземпляр модели

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        raise NotImplementedError("Метод update должен быть реализован в подклассе")

    def search(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Поиск записей по критериям.

        Args:
            criteria: Словарь с условиями поиска

        Returns:
            Список подходящих записей
        """
        conditions = []
        params = []

        for field, value in criteria.items():
            if value is not None:
                if isinstance(value, str):
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
                else:
                    conditions.append(f"{field} = ?")
                    params.append(value)

        where_clause = " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM {self.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        rows = self._execute_query(query, tuple(params))
        return [self._map_to_model(row) for row in rows]