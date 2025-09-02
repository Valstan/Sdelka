from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, Sequence

from config.settings import CONFIG
from utils.user_prefs import get_current_db_path, get_enable_wal, get_busy_timeout_ms
from utils.runtime_mode import is_readonly

logger = logging.getLogger(__name__)


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    # Включаем WAL по пользовательской настройке (или по умолчанию)
    if get_enable_wal():
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    # Настройка таймаута блокировок в миллисекундах
    try:
        timeout_ms = int(get_busy_timeout_ms())
        conn.execute(f"PRAGMA busy_timeout = {timeout_ms};")
    except Exception:
        pass


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    # Берем путь из аргумента, иначе из пользовательских настроек (prefs), иначе из CONFIG
    path = Path(db_path) if db_path else get_current_db_path()
    needs_init = not path.exists()
    # В секундах для sqlite3.connect(timeout=...)
    try:
        connect_timeout_sec = max(1.0, float(get_busy_timeout_ms()) / 1000.0)
    except Exception:
        connect_timeout_sec = 10.0
    # В режиме только чтение открываем БД с mode=ro, чтобы запись была физически невозможна
    if is_readonly():
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(
            uri,
            uri=True,
            timeout=connect_timeout_sec,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
    else:
        conn = sqlite3.connect(
            path,
            timeout=connect_timeout_sec,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
    conn.row_factory = sqlite3.Row
    try:
        try:
            _apply_pragmas(conn)
        except Exception:
            # Некоторые PRAGMA могут быть недоступны в режиме ro — игнорируем
            pass
        if needs_init:
            logger.info("Создана новая БД по пути: %s", path)
        yield conn
        if not is_readonly():
            conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        # Подавляем шум в логах для попыток записи в режиме 'Просмотр'
        msg = str(exc).lower()
        if "readonly" in msg or "read-only" in msg:
            # Не логируем stacktrace, чтобы не засорять лог
            raise
        logger.exception("Откат транзакции из-за ошибки")
        raise
    except Exception:
        conn.rollback()
        logger.exception("Откат транзакции из-за ошибки")
        raise
    finally:
        conn.close()


def execute(conn: sqlite3.Connection, sql: str, params: Sequence[Any] | None = None) -> int:
    if is_readonly() and sql.strip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER"}:
        raise PermissionError("Режим только просмотра: запись запрещена")
    cur = conn.execute(sql, params or [])
    return cur.lastrowid if cur.lastrowid is not None else cur.rowcount


def executemany(conn: sqlite3.Connection, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
    if is_readonly() and sql.strip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE"}:
        raise PermissionError("Режим только просмотра: запись запрещена")
    cur = conn.executemany(sql, seq_of_params)
    return cur.rowcount


def query(conn: sqlite3.Connection, sql: str, params: Sequence[Any] | None = None) -> list[sqlite3.Row]:
    cur = conn.execute(sql, params or [])
    return cur.fetchall()