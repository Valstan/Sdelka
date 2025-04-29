# File: app/core/database/connections.py
"""
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
        db_path: Путь к файлу базы данных
        backup_dir: Путь к каталогу резервных копий
        max_backups: Максимальное количество сохраняемых резервных копий
        connection: Активное соединение с базой данных
    """

    def __init__(self, db_path: str, backup_dir: Optional[str] = None, max_backups: int = 20):
        """
        Инициализирует менеджер базы данных.

        Args:
            db_path: Путь к файлу базы данных
            backup_dir: Путь к каталогу резервных копий (по умолчанию - рядом с БД)
            max_backups: Максимальное количество резервных копий
        """
        self.db_path = Path(db_path).resolve()
        self.max_backups = max_backups

        if backup_dir is None:
            self.backup_dir = self.db_path.parent / 'backups'
        else:
            self.backup_dir = Path(backup_dir).resolve()

        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_backup_directory()

    def _ensure_backup_directory(self) -> None:
        """Создает каталог резервных копий, если его не существует."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(
                f"Каталог резервных копий {'создан' if not self.backup_dir.exists() else 'обновлен'}: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Не удалось создать каталог резервных копий: {e}")

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Создает и управляет соединением с базой данных.

        Yields:
            Активное соединение с базой данных

        Raises:
            sqlite3.Error: Если произошла ошибка при подключении
        """
        new_connection = False
        try:
            if self.connection is None:
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
        finally:
            if new_connection and self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Соединение с базой данных закрыто")

    def create_backup(self) -> bool:
        """
        Создает резервную копию базы данных.

        Returns:
            Успех операции
        """
        try:
            if not self.db_path.exists():
                logger.warning(f"База данных не найдена для создания резерва: {self.db_path}")
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.db"

            # Создаем бэкап
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
        Удаляет старые резервные копии, если их количество превышает лимит.
        """
        try:
            backups = sorted(
                (f for f in self.backup_dir.glob("backup_*.db") if f.is_file()),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
                logger.debug(f"Удалена старая резервная копия: {old_backup}")

        except Exception as e:
            logger.error(f"Ошибка очистки резервных копий: {e}", exc_info=True)

    def get_status(self) -> dict:
        """
        Возвращает статус базы данных.

        Returns:
            Словарь с информацией о состоянии БД
        """
        status = {
            "database_exists": self.db_path.exists(),
            "connection_active": self.connection is not None,
            "backup_count": len(list(self.backup_dir.glob("backup_*.db")))
        }

        if status["database_exists"]:
            status.update({
                "size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2),
                "last_modified": datetime.fromtimestamp(self.db_path.stat().st_mtime).isoformat()
            })

        return status


if __name__ == "__main__":
    # Пример использования
    import logging.config

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    })

    db_manager = DatabaseManager("test.db")
    print("Статус БД:", db_manager.get_status())

    with db_manager.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES ('Test')")

    print("Статус БД после теста:", db_manager.get_status())
    db_manager.create_backup()