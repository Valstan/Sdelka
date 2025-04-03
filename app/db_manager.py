"""
Модуль для работы с базой данных SQLite.
Управляет соединением с БД, выполняет запросы и создает резервные копии.
"""
import os
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union

from app.models import (
    Worker, WorkType, Product, Contract,
    WorkCard, WorkCardItem, WorkCardWorker
)
from app.queries import (
    CREATE_TABLES_QUERIES,
    GET_ALL_WORKERS, GET_WORKER_BY_ID, SEARCH_WORKERS,
    GET_ALL_WORK_TYPES, GET_WORK_TYPE_BY_ID, SEARCH_WORK_TYPES,
    GET_ALL_PRODUCTS, GET_PRODUCT_BY_ID, SEARCH_PRODUCTS,
    GET_ALL_CONTRACTS, GET_CONTRACT_BY_ID, SEARCH_CONTRACTS,
    GET_ALL_WORK_CARDS, GET_WORK_CARD_BY_ID,
    GET_WORK_CARD_ITEMS, GET_WORK_CARD_WORKERS,
    REPORT_BY_WORKER_BASE, get_report_query
)
from app.config import DB_SETTINGS, DIRECTORIES

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Класс для управления базой данных SQLite.
    Обеспечивает подключение к БД, выполнение запросов и создание резервных копий.
    """

    def __init__(self, db_path: str = None):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path or DB_SETTINGS['database_path']
        self.connection = None

        # Создание директорий, если они не существуют
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        DIRECTORIES['backups'].mkdir(parents=True, exist_ok=True)

        # Создание резервной копии БД при инициализации
        if DB_SETTINGS['create_backup_on_start']:
            self.create_backup()

        # Установка соединения с БД
        self.connect()

        # Инициализация структуры БД, если она не существует
        self.initialize_db()

    def connect(self) -> None:
        """Установка соединения с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Успешно подключено к БД: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise RuntimeError(f"Не удалось подключиться к базе данных: {e}")

    def create_backup(self) -> str:
        """
        Создание резервной копии базы данных.

        Returns:
            Путь к созданной резервной копии
        """
        if not os.path.exists(self.db_path):
            logger.info(f"Файл БД {self.db_path} не существует, резервная копия не создана")
            return ""

        backup_dir = DIRECTORIES['backups']
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Резервная копия БД создана: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""

    def initialize_db(self) -> None:
        """
        Инициализация структуры базы данных при первом запуске.
        Создает необходимые таблицы, если они не существуют.
        """
        try:
            cursor = self.connection.cursor()
            for query in CREATE_TABLES_QUERIES:
                cursor.execute(query)
            self.connection.commit()
            logger.info("Структура БД успешно инициализирована")
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка инициализации БД: {e}")
            raise RuntimeError(f"Ошибка создания таблиц: {e}")

    # Остальные методы класса остаются без изменений
    # (get_all_workers, get_worker_by_id, ..., get_report_data)

    def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с БД закрыто")