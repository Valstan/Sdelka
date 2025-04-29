# File: app/services/base_service.py
"""
Базовый класс для всех сервисов, обеспечивающий общую функциональность.
"""

import sqlite3
from typing import Any, Dict, Optional, Tuple
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Абстрактный базовый класс для всех сервисов.

    Attributes:
        db_manager: Менеджер базы данных
    """

    def __init__(self, db_manager: 'DatabaseManager'):
        """
        Инициализирует базовый сервис.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db_manager = db_manager

    @abstractmethod
    def get_query_file(self, filename: str) -> str:
        """
        Загружает SQL-запрос из файла.

        Args:
            filename: Имя файла с SQL-запросом

        Returns:
            Содержимое файла с SQL-запросом
        """
        pass

    def execute_query(
            self,
            query: str,
            params: Optional[Tuple] = None,
            fetch_one: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет SQL-запрос к базе данных.

        Args:
            query: SQL-запрос
            params: Параметры для запроса (по умолчанию - None)
            fetch_one: Нужно ли получить только одну запись

        Returns:
            Результат выполнения запроса или None
        """
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                result = cursor.fetchone() if fetch_one else cursor.fetchall()

                # Логируем результат только если есть данные
                if result and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Выполнен запрос: {query[:50]}... | "
                        f"Количество строк: {len(result) if isinstance(result, list) else 1}"
                    )

                return result

        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения SQL-запроса: {e}", exc_info=True)
            raise

    def _save_entity(
            self,
            query: str,
            params: Tuple,
            entity_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Сохраняет сущность в базе данных.

        Args:
            query: SQL-запрос для сохранения
            params: Параметры для запроса
            entity_name: Название сущности для логирования

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                last_row_id = cursor.lastrowid
                logger.info(f"{entity_name} успешно сохранен с ID: {last_row_id}")

                return True, last_row_id

        except sqlite3.IntegrityError as e:
            error_msg = f"Нарушение целостности данных при сохранении {entity_name}: {e}"
            logger.warning(error_msg, exc_info=True)
            return False, error_msg

        except sqlite3.Error as e:
            error_msg = f"Ошибка сохранения {entity_name}: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _delete_entity(
            self,
            query: str,
            params: Tuple,
            entity_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Удаляет сущность из базы данных.

        Args:
            query: SQL-запрос для удаления
            params: Параметры для запроса
            entity_name: Название сущности для логирования

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                if cursor.rowcount > 0:
                    logger.info(f"{entity_name} успешно удален")
                    return True, None
                else:
                    error_msg = f"{entity_name} не найден для удаления"
                    logger.warning(error_msg)
                    return False, error_msg

        except sqlite3.Error as e:
            error_msg = f"Ошибка удаления {entity_name}: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg