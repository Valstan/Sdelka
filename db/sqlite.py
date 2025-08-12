from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, Sequence

from config.settings import CONFIG

logger = logging.getLogger(__name__)


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    if CONFIG.enable_wal:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA temp_store = MEMORY;")


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    path = Path(db_path) if db_path else CONFIG.db_path
    needs_init = not path.exists()
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    try:
        _apply_pragmas(conn)
        if needs_init:
            logger.info("Создана новая БД по пути: %s", path)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Откат транзакции из-за ошибки")
        raise
    finally:
        conn.close()


def execute(conn: sqlite3.Connection, sql: str, params: Sequence[Any] | None = None) -> int:
    cur = conn.execute(sql, params or [])
    return cur.lastrowid if cur.lastrowid is not None else cur.rowcount


def executemany(conn: sqlite3.Connection, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
    cur = conn.executemany(sql, seq_of_params)
    return cur.rowcount


def query(conn: sqlite3.Connection, sql: str, params: Sequence[Any] | None = None) -> list[sqlite3.Row]:
    cur = conn.execute(sql, params or [])
    return cur.fetchall()