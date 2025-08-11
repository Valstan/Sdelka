from __future__ import annotations

import sqlite3
from threading import RLock
from typing import Any, Iterable

from app.utils.config import CONFIG
from app.utils.paths import get_paths


class Database:
    """Thread-safe SQLite connection singleton."""

    _instance: "Database | None" = None
    _lock = RLock()

    def __init__(self) -> None:
        paths = get_paths()
        self._connection = sqlite3.connect(
            paths.db_file,
            timeout=CONFIG.db_timeout_seconds,
            isolation_level=None,  # autocommit
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._connection.execute("PRAGMA journal_mode = WAL;")

    @classmethod
    def instance(cls) -> "Database":
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database()
            return cls._instance

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance._connection.close()
                except Exception:
                    pass
                finally:
                    cls._instance = None

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> sqlite3.Cursor:
        cur = self._connection.cursor()
        cur.execute(sql, params or [])
        return cur

    def executemany(self, sql: str, seq_of_params: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        cur = self._connection.cursor()
        cur.executemany(sql, seq_of_params)
        return cur

    def query_all(self, sql: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
        return list(self.execute(sql, params))

    def query_one(self, sql: str, params: Iterable[Any] | None = None) -> sqlite3.Row | None:
        cur = self.execute(sql, params)
        return cur.fetchone()