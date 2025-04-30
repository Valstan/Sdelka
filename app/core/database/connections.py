"""
File: app/core/database/connections.py
Модуль обеспечивает безопасное подключение к базе данных SQLite с возможностью
резервного копирования и мониторинга состояния соединения.
"""

import sqlite3
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Generator
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Класс для управления соединением с базой данных SQLite.

    Attributes:
        db_path (Path): Путь к файлу базы данных
        backup_dir (Path): Директория для резервных копий
        max_backups (int): Максимальное количество резервных копий
        connection (Optional[sqlite3.Connection]): Активное соединение с БД
    """

    def __init__(self, db_path: str, backup_dir: str = "backups", max_backups: int = 20):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных
            backup_dir: Директория для резервных копий
            max_backups: Максимальное количество резервных копий
        """
        self.db_path = Path(db_path).absolute()
        self.backup_dir = Path(backup_dir).absolute()
        self.max_backups = max_backups
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_database()

    def _setup_database(self) -> None:
        """Инициализация структуры базы данных."""
        self.backup_dir.mkdir(exist_ok=True)

        if not self.db_path.exists():
            logger.info(f"Создание новой базы данных по пути {self.db_path}")
            self.db_path.touch()

        self._create_tables()
        self._create_backup()

    def _create_tables(self) -> None:
        """Создание таблиц базы данных."""
        with self.connect() as conn:
            with conn:
                for query_file in [
                    "app/core/database/queries/contracts.sql",
                    "app/core/database/queries/workers.sql",
                    "app/core/database/queries/work_types.sql",
                    "app/core/database/queries/products.sql",
                    "app/core/database/queries/work_cards.sql"
                ]:
                    with open(query_file, "r", encoding="utf-8") as f:
                        queries = f.read().split(";")
                        for query in queries:
                            if query.strip():
                                conn.execute(query)

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Контекстный менеджер для безопасного подключения к базе данных.

        Yields:
            sqlite3.Connection: Активное соединение с базой данных

        Raises:
            sqlite3.Error: Если произошла ошибка при подключении
        """
        new_connection = False
        try:
            if self.connection is None or self.connection.closed:
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    isolation_level=None,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                self.connection.row_factory = sqlite3.Row
                new_connection = True
                logger.info(f"Новое соединение установлено с базой данных: {self.db_path}")

            yield self.connection

        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}", exc_info=True)
            raise

    def begin_transaction(self) -> None:
        """Начало транзакции."""
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

    def commit_transaction(self) -> None:
        """Подтверждение транзакции."""
        if self.connection:
            self.connection.commit()

    def rollback_transaction(self) -> None:
        """Откат транзакции."""
        if self.connection:
            self.connection.rollback()

    def create_backup(self) -> bool:
        """
        Создание резервной копии базы данных.

        Returns:
            bool: True, если резервная копия успешно создана
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.db"

            with self.connect() as conn:
                with conn:  # Автоматический коммит
                    dest_conn = sqlite3.connect(backup_file)
                    try:
                        conn.backup(dest_conn)
                    finally:
                        dest_conn.close()
            logger.info(f"Резервная копия создана: {backup_file}")
            self._cleanup_old_backups()
            return True

        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}", exc_info=True)
            return False

    def _cleanup_old_backups(self) -> None:
        """
        Очистка старых резервных копий, если их количество превышает лимит.
        """
        backups = sorted(
            (f for f in self.backup_dir.glob("backup_*.db") if f.is_file()),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
                logger.info(f"Удалена старая резервная копия: {old_backup}")
            except Exception as e:
                logger.error(f"Ошибка удаления резервной копии: {e}", exc_info=True)