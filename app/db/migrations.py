from __future__ import annotations

from pathlib import Path

from app.db.connection import Database
from app.utils.paths import ensure_directories, get_paths


def _read_queries_file() -> str:
    paths = get_paths()
    queries_path = paths.root / "app" / "db" / "queries.sql"
    return queries_path.read_text(encoding="utf-8")


def initialize_database() -> None:
    """Create database schema if not exists."""
    ensure_directories()
    db = Database.instance()
    sql = _read_queries_file()
    # Execute full SQL script to handle Windows newlines and complex statements
    db.connection.executescript(sql)


def destroy_database_for_tests() -> None:
    """Dangerous: remove DB file; used only in tests."""
    paths = get_paths()
    try:
        Database.reset_for_tests()
        Path(paths.db_file).unlink(missing_ok=True)
    except Exception:
        pass