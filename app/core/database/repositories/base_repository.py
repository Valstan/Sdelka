# app/core/database/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple
from dataclasses import asdict
from datetime import datetime, date
import logging

from app.core.models.base_model import BaseModel
from app.core.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseRepository(ABC):
    """
    Базовый класс репозитория для работы с сущностями в БД.

    Attributes:
        db_manager: Менеджер базы данных
        model_class: Класс модели
        table_name: Название таблицы в БД
    """

    def __init__(self, db_manager: DatabaseManager, model_class: Type[T], table_name: str):
        """
        Инициализирует репозиторий.

        Args:
            db_manager: Менеджер базы данных
            model_class: Класс модели
            table_name: Название таблицы в БД
        """
        self.db_manager = db_manager
        self.model_class = model_class
        self.table_name = table_name

    def create(self, model: T) -> Tuple[bool, Optional[int]]:
        """
        Создает новую запись в БД.

        Args:
            model: Модель данных

        Returns:
            Tuple[bool, Optional[int]]: (успех, ID новой записи)
        """
        try:
            # Валидация данных
            is_valid, errors = model.validate()
            if not is_valid:
                logger.error(f"Ошибка валидации при создании {self.model_class.__name__}: {errors}")
                return False, None

            # Подготовка данных для вставки
            data = self._prepare_data_for_insert(model)

            # Формирование запроса
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

            # Выполнение запроса
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, list(data.values()))
                conn.commit()
                model_id = cursor.lastrowid

                # Обновляем модель с ID
                model.id = model_id
                model.created_at = datetime.now()
                model.updated_at = model.created_at

                return True, model_id

        except Exception as e:
            logger.error(f"Ошибка создания {self.model_class.__name__}: {e}", exc_info=True)
            return False, None

    def get_by_id(self, model_id: int) -> Optional[T]:
        """
        Получает запись по ID.

        Args:
            model_id: ID записи

        Returns:
            Optional[T]: Модель данных или None
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = ?"
            result = self.db_manager.execute_query_fetch_one(query, (model_id,))

            if result:
                return self._create_model_from_db(result)
            return None

        except Exception as e:
            logger.error(f"Ошибка получения {self.model_class.__name__} по ID: {e}", exc_info=True)
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Получает все записи.

        Args:
            limit: Количество записей для получения
            offset: Смещение

        Returns:
            List[T]: Список моделей
        """
        try:
            query = f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?"
            results = self.db_manager.execute_query(query, (limit, offset))

            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            logger.error(f"Ошибка получения всех {self.model_class.__name__}: {e}", exc_info=True)
            return []

    def update(self, model: T) -> Tuple[bool, Optional[str]]:
        """
        Обновляет запись.

        Args:
            model: Модель данных

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            # Проверка наличия ID
            if model.id is None:
                error_msg = "Невозможно обновить запись без ID"
                logger.error(error_msg)
                return False, error_msg

            # Валидация данных
            is_valid, errors = model.validate()
            if not is_valid:
                error_msg = f"Ошибка валидации при обновлении {self.model_class.__name__}: {errors}"
                logger.error(error_msg)
                return False, error_msg

            # Подготовка данных для обновления
            data = self._prepare_data_for_update(model)

            # Формирование запроса
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            params = list(data.values()) + [model.id]

            # Выполнение запроса
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                # Обновляем время обновления
                model.updated_at = datetime.now()

                return True, None

        except Exception as e:
            logger.error(f"Ошибка обновления {self.model_class.__name__}: {e}", exc_info=True)
            return False, str(e)

    def delete(self, model_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет запись.

        Args:
            model_id: ID записи

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (model_id,))
                conn.commit()
                return True, None

        except Exception as e:
            logger.error(f"Ошибка удаления {self.model_class.__name__}: {e}", exc_info=True)
            return False, str(e)

    def search(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Выполняет поиск записей по критериям.

        Args:
            criteria: Словарь с условиями поиска

        Returns:
            List[T]: Список подходящих записей
        """
        try:
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

            results = self.db_manager.execute_query(query, tuple(params))
            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            logger.error(f"Ошибка поиска {self.model_class.__name__}: {e}", exc_info=True)
            return []

    def _create_model_from_db(self, row: Dict[str, Any]) -> T:
        """
        Создает модель из строки БД.

        Args:
            row: Строка БД

        Returns:
            T: Модель данных
        """
        try:
            data = dict(row)

            # Преобразуем даты
            for field_name, field_type in self.model_class.__annotations__.items():
                if field_name in data and data[field_name] is not None:
                    if field_type == datetime and not isinstance(data[field_name], datetime):
                        try:
                            data[field_name] = datetime.fromisoformat(data[field_name])
                        except ValueError:
                            pass
                    elif field_type == data and not isinstance(data[field_name], date):
                        try:
                            data[field_name] = data.fromisoformat(data[field_name])
                        except ValueError:
                            pass

            return self.model_class.from_dict(data)

        except Exception as e:
            logger.error(f"Ошибка создания модели {self.model_class.__name__} из БД: {e}", exc_info=True)
            raise

    def _prepare_data_for_insert(self, model: T) -> Dict[str, Any]:
        """
        Подготавливает данные для вставки.

        Args:
            model: Модель данных

        Returns:
            Dict[str, Any]: Подготовленные данные
        """
        data = {}
        for field_name, field_type in model.__annotations__.items():
            value = getattr(model, field_name)

            # Пропускаем None для автоинкрементных полей
            if field_name == "id" and value is None:
                continue

            # Преобразуем даты в строку
            if isinstance(value, (datetime, data)):
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value

        return data

    def _prepare_data_for_update(self, model: T) -> Dict[str, Any]:
        """
        Подготавливает данные для обновления.

        Args:
            model: Модель данных

        Returns:
            Dict[str, Any]: Подготовленные данные
        """
        data = {}
        for field_name, field_type in model.__annotations__.items():
            value = getattr(model, field_name)

            # Пропускаем None и ID
            if field_name == "id" or value is None:
                continue

            # Преобразуем даты в строку
            if isinstance(value, (datetime, data)):
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value

        return data

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование записи.

        Args:
            model_id: ID записи

        Returns:
            bool: True, если запись существует
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE id = ?"
            result = self.db_manager.execute_query_fetch_one(query, (model_id,))
            return result[0] > 0

        except Exception as e:
            logger.error(f"Ошибка проверки существования {self.model_class.__name__}: {e}", exc_info=True)
            return False

    def count(self) -> int:
        """
        Возвращает количество записей.

        Returns:
            int: Количество записей
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            result = self.db_manager.execute_query_fetch_one(query)
            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения количества {self.model_class.__name__}: {e}", exc_info=True)
            return 0

    def bulk_create(self, models: List[T]) -> Tuple[bool, Optional[str]]:
        """
        Создает несколько записей.

        Args:
            models: Список моделей

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            if not models:
                return True, None

            # Проверка всех моделей
            for model in models:
                is_valid, errors = model.validate()
                if not is_valid:
                    error_msg = f"Ошибка валидации при массовом создании {self.model_class.__name__}: {errors}"
                    logger.error(error_msg)
                    return False, error_msg

            # Подготовка данных
            data_list = [self._prepare_data_for_insert(model) for model in models]

            if not data_list:
                return True, None

            # Формирование запроса
            columns = ', '.join(data_list[0].keys())
            placeholders = ', '.join(['?'] * len(data_list[0]))
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

            # Подготовка параметров
            params_list = [list(data.values()) for data in data_list]

            # Выполнение запроса
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()

                # Обновляем модели с ID
                cursor.execute("SELECT last_insert_rowid()")
                first_id = cursor.fetchone()[0]

                for i, model in enumerate(models):
                    model.id = first_id + i
                    model.created_at = datetime.now()
                    model.updated_at = model.created_at

                return True, None

        except Exception as e:
            logger.error(f"Ошибка массового создания {self.model_class.__name__}: {e}", exc_info=True)
            return False, str(e)

    def bulk_update(self, models: List[T]) -> Tuple[bool, Optional[str]]:
        """
        Обновляет несколько записей.

        Args:
            models: Список моделей

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            if not models:
                return True, None

            # Проверка всех моделей
            for model in models:
                if model.id is None:
                    error_msg = "Невозможно обновить запись без ID"
                    logger.error(error_msg)
                    return False, error_msg

                is_valid, errors = model.validate()
                if not is_valid:
                    error_msg = f"Ошибка валидации при массовом обновлении {self.model_class.__name__}: {errors}"
                    logger.error(error_msg)
                    return False, error_msg

            # Подготовка данных
            data_list = [self._prepare_data_for_update(model) for model in models]

            if not data_list:
                return True, None

            # Формирование запроса
            set_clause = ', '.join([f"{key} = ?" for key in data_list[0].keys() if key != "id"])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"

            # Подготовка параметров
            params_list = []
            for model, data in zip(models, data_list):
                params = list(data.values()) + [model.id]
                params_list.append(params)

            # Выполнение запроса
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()

                # Обновляем время обновления
                current_time = datetime.now()
                for model in models:
                    model.updated_at = current_time

                return True, None

        except Exception as e:
            logger.error(f"Ошибка массового обновления {self.model_class.__name__}: {e}", exc_info=True)
            return False, str(e)