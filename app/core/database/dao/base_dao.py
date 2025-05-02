# File: app/core/database/dao/base_dao.py

import sqlite3
from typing import Optional, List, Dict, Any
from app.core.database.connections import DatabaseManager
from logging import getLogger

logger = getLogger(__name__)


class BaseDAO:
    """Базовый класс DAO для работы с таблицами в базе данных."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _execute(
            self,
            query: str,
            params: Optional[tuple] = None,
            fetch_one: bool = False,
            fetch_all: bool = False
    ) -> Optional[Any]:
        """Выполняет SQL-запрос."""
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.execute(query, params) if params else conn.execute(query)

                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения SQL-запроса: {e}", exc_info=True)
            raise