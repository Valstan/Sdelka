"""
Модуль для работы с базой данных SQLite.
Управляет соединением с БД, выполняет запросы и создает резервные копии.
"""
import os
import sqlite3
import shutil
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any, Tuple, Union

from app.config import DB_PATH, BACKUP_DIR, get_backup_filename

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_path: str = DB_PATH):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self.connection = None
        self.create_backup()
        self.connect()
        self.initialize_db()

    def connect(self) -> None:
        """Установка соединения с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Соединение с БД {self.db_path} установлено")
        except sqlite3.Error as e:
            logger.error(f"Ошибка соединения с БД: {e}")
            raise

    def create_backup(self) -> str:
        """
        Создает резервную копию базы данных с текущей датой и временем в имени файла.

        Returns:
            str: Путь к созданной резервной копии
        """
        if not os.path.exists(self.db_path):
            logger.info(f"Файл БД {self.db_path} не существует, резервная копия не создана")
            return ""

        backup_filename = get_backup_filename()
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Создана резервная копия БД: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""

    def initialize_db(self) -> None:
        """Инициализация структуры базы данных при первом запуске"""
        from app.db.queries import CREATE_TABLES_QUERIES

        try:
            cursor = self.connection.cursor()

            # Создаем все необходимые таблицы
            for query in CREATE_TABLES_QUERIES:
                cursor.execute(query)

            self.connection.commit()
            logger.info("Структура БД успешно инициализирована")
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def execute_query(self, query: str, parameters: Tuple = ()) -> Optional[sqlite3.Cursor]:
        """
        Выполнение SQL-запроса без возврата данных.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Cursor объект SQLite или None в случае ошибки
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return None

    def execute_query_fetchall(self, query: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Выполнение SQL-запроса с возвратом всех строк результата.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Список словарей с данными из запроса
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)

            # Преобразуем результат в список словарей
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return []

    def execute_query_fetchone(self, query: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Выполнение SQL-запроса с возвратом одной строки результата.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Словарь с данными или None если нет результата или произошла ошибка
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)

            row = cursor.fetchone()
            if row:
                # Преобразуем строку в словарь
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return None

    def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с БД закрыто")