# app/core/database/database_manager.py
import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления подключением к базе данных SQLite."""

    def __init__(self, db_path: str):
        """
        Инициализирует менеджер базы данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = Path(db_path)
        self._initialize_database()
        self.backup_dir = self.db_path.parent / "backups"
        self.backup_limit = 20
        self._create_backup_dir()

    def _initialize_database(self) -> None:
        """Инициализирует соединение с базой данных."""
        try:
            # Создаем директорию для базы данных, если ее нет
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Создаем соединение с базой данных
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )

            # Настраиваем соединение
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Успешно подключено к базе данных: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}", exc_info=True)
            raise

    def _create_backup_dir(self) -> None:
        """Создает директорию для резервных копий."""
        try:
            self.backup_dir.mkdir(exist_ok=True)
            logger.info(f"Резервные копии будут сохраняться в: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Ошибка создания директории для резервных копий: {e}", exc_info=True)

    @contextmanager
    def connect(self) -> sqlite3.Connection:
        """
        Контекстный менеджер для безопасного соединения с базой данных.

        Returns:
            sqlite3.Connection: Соединение с базой данных
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Выполняет SQL-запрос и возвращает результат.

        Args:
            query: SQL-запрос
            params: Параметры запроса

        Returns:
            List[sqlite3.Row]: Результат запроса
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                conn.commit()
                return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}", exc_info=True)
            return []

    def execute_update(self, query: str, params: tuple = ()) -> Tuple[bool, Optional[str]]:
        """
        Выполняет SQL-запрос на изменение данных.

        Args:
            query: SQL-запрос
            params: Параметры запроса

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}", exc_info=True)
            return False, str(e)

    def execute_many(self, query: str, params_list: List[tuple]) -> Tuple[bool, Optional[str]]:
        """
        Выполняет SQL-запрос для множества параметров.

        Args:
            query: SQL-запрос
            params_list: Список параметров

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения массового запроса: {e}", exc_info=True)
            return False, str(e)

    def create_backup(self) -> Tuple[bool, Optional[str]]:
        """
        Создает резервную копию базы данных.

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            from datetime import datetime

            # Создаем имя файла резервной копии
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_name

            # Создаем резервную копию
            with self.connect() as conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    conn.backup(backup_conn)

            # Удаляем старые резервные копии, если их больше лимита
            self._cleanup_backups()

            logger.info(f"Резервная копия создана: {backup_path}")
            return True, None
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}", exc_info=True)
            return False, str(e)

    def _cleanup_backups(self) -> None:
        """Очищает старые резервные копии."""
        try:
            # Получаем список всех резервных копий
            backups = sorted(
                self.backup_dir.glob("backup_*.db"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            # Удаляем лишние копии
            for backup in backups[self.backup_limit:]:
                backup.unlink()
                logger.info(f"Удалена старая резервная копия: {backup}")
        except Exception as e:
            logger.error(f"Ошибка очистки резервных копий: {e}", exc_info=True)

    def begin_transaction(self) -> Tuple[bool, Optional[str]]:
        """
        Начинает новую транзакцию.

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка начала транзакции: {e}", exc_info=True)
            return False, str(e)

    def commit_transaction(self) -> Tuple[bool, Optional[str]]:
        """
        Фиксирует текущую транзакцию.

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка фиксации транзакции: {e}", exc_info=True)
            return False, str(e)

    def rollback_transaction(self) -> Tuple[bool, Optional[str]]:
        """
        Откатывает текущую транзакцию.

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                conn.rollback()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка отката транзакции: {e}", exc_info=True)
            return False, str(e)

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получает информацию о структуре таблицы.

        Args:
            table_name: Название таблицы

        Returns:
            List[Dict[str, Any]]: Список информации о колонках
        """
        try:
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(query)

            table_info = []
            for row in result:
                column_info = {
                    "cid": row["cid"],
                    "name": row["name"],
                    "type": row["type"],
                    "notnull": bool(row["notnull"]),
                    "dflt_value": row["dflt_value"],
                    "pk": bool(row["pk"])
                }
                table_info.append(column_info)

            return table_info
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения информации о таблице: {e}", exc_info=True)
            return []

    def table_exists(self, table_name: str) -> bool:
        """
        Проверяет существование таблицы в базе данных.

        Args:
            table_name: Название таблицы

        Returns:
            bool: True, если таблица существует
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки существования таблицы: {e}", exc_info=True)
            return False

    def create_table(self, table_sql: str) -> Tuple[bool, Optional[str]]:
        """
        Создает новую таблицу.

        Args:
            table_sql: SQL-запрос создания таблицы

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                conn.execute(table_sql)
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблицы: {e}", exc_info=True)
            return False, str(e)

    def execute_script(self, sql_script: str) -> Tuple[bool, Optional[str]]:
        """
        Выполняет SQL-скрипт.

        Args:
            sql_script: SQL-скрипт

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                conn.executescript(sql_script)
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения SQL-скрипта: {e}", exc_info=True)
            return False, str(e)

    def get_last_insert_id(self) -> Optional[int]:
        """
        Получает ID последней вставленной строки.

        Returns:
            Optional[int]: ID последней вставленной строки или None
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения последнего ID: {e}", exc_info=True)
            return None

    def execute_query_fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Выполняет SQL-запрос и возвращает первую строку результата.

        Args:
            query: SQL-запрос
            params: Параметры запроса

        Returns:
            Optional[sqlite3.Row]: Первая строка результата или None
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}", exc_info=True)
            return None

    def execute_non_query(self, query: str, params: tuple = ()) -> Tuple[bool, Optional[str]]:
        """
        Выполняет SQL-запрос, который не возвращает результат.

        Args:
            query: SQL-запрос
            params: Параметры запроса

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}", exc_info=True)
            return False, str(e)