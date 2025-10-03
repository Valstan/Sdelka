from __future__ import annotations

from pathlib import Path

from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db


def test_initialize_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    # Создаем директорию если она не существует
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Используем прямой путь к БД
    import sqlite3
    with sqlite3.connect(str(db_path)) as conn:
        initialize_schema(conn)
        # таблица должна существовать
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workers'"
        ).fetchall()
        assert rows


def test_backup_rotation(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    backups_dir = tmp_path / "backups"
    
    # Создаем директории если они не существуют
    db_path.parent.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)

    # создать пустую БД
    import sqlite3
    with sqlite3.connect(str(db_path)) as conn:
        initialize_schema(conn)

    # сделать 22 бэкапа, оставить 20
    for _ in range(22):
        backup_sqlite_db(db_path, backups_dir=backups_dir, max_backups=20)

    files = sorted(backups_dir.glob("test_*"))
    assert len(files) <= 20
