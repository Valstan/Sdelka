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
    """Класс для управления подключением к базе данных SQLite."""

    def __init__(self, db_path: str):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / "backups"
        self.max_backups = 20
        self.connection = None
        self._setup_database()

    def _setup_database(self) -> None:
        """Настройка базы данных при запуске."""
        try:
            self._create_backup_on_start()
            self._create_tables()
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}", exc_info=True)
            raise

    def _create_backup_on_start(self) -> None:
        """Создает резервную копию базы данных при запуске."""
        try:
            if self.db_path.exists():
                self.backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"backup_{timestamp}.db"

                shutil.copy2(self.db_path, backup_file)
                self._cleanup_old_backups()
                logger.info(f"Резервная копия создана: {backup_file}")
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}", exc_info=True)

    def _cleanup_old_backups(self) -> None:
        """Очистка старых резервных копий."""
        if not self.backup_dir.exists():
            return

        backups = sorted(
            (f for f in self.backup_dir.glob("backup_*.db") if f.is_file()),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
                logger.debug(f"Удалена старая резервная копия: {old_backup}")
            except Exception as e:
                logger.error(f"Ошибка удаления резервной копии: {e}", exc_info=True)

    def _create_tables(self) -> None:
        """Создает таблицы, если их нет."""
        schema_files = [
            "app/core/database/queries/contracts.sql",
            "app/core/database/queries/workers.sql",
            "app/core/database/queries/work_types.sql",
            "app/core/database/queries/products.sql",
            "app/core/database/queries/work_cards.sql"
        ]

        with self.connect() as conn:
            for file_path in schema_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                    # Удаляем комментарии в формате Python
                    sql_statements = [
                        stmt for stmt in sql_script.split(";")
                        if not stmt.strip().startswith("\"\"\"")
                    ]

                    for statement in sql_statements:
                        if statement.strip():
                            conn.execute(statement)

                    logger.debug(f"Выполнен скрипт из файла: {file_path}")
                except Exception as e:
                    logger.error(f"Ошибка выполнения скрипта {file_path}: {e}", exc_info=True)
                    raise

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Контекстный менеджер для безопасного подключения к БД."""
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
            if new_connection:
                self.connection.close()
            raise

    def begin_transaction(self) -> None:
        """Начало транзакции."""
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            logger.debug("Начата транзакция")

    def backup(self, backup_path: str) -> bool:
        """Создает резервную копию базы данных."""
        try:
            with self.connect() as conn:
                dest_conn = sqlite3.connect(backup_path)
                try:
                    conn.backup(dest_conn)
                finally:
                    dest_conn.close()
                logger.info(f"Резервная копия создана: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}", exc_info=True)
            return False