from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from config.settings import CONFIG
from db.sqlite import get_connection

logger = logging.getLogger(__name__)


def backup_sqlite_db(db_path: Path | str, backups_dir: Path | str | None = None, max_backups: int | None = None) -> Path | None:
    db_path = Path(db_path)
    if not db_path.exists():
        logger.info("Бэкап пропущен: файл БД не найден: %s", db_path)
        return None

    backups_dir = Path(backups_dir) if backups_dir else CONFIG.backups_dir
    backups_dir.mkdir(parents=True, exist_ok=True)
    max_backups = max_backups or CONFIG.max_backup_files

    # Именование: backup_base_sdelka_MMDD_HHMM.db (без года)
    ts = datetime.now().strftime("%m%d_%H%M")
    backup_name = f"backup_base_sdelka_{ts}{db_path.suffix}"
    backup_path = backups_dir / backup_name

    # Используем Online Backup API SQLite для консистентной копии, безопасной для WAL
    try:
        with get_connection(db_path) as src:
            with sqlite3.connect(backup_path) as dest:
                src.backup(dest)
        logger.info("Создан бэкап БД (online backup): %s", backup_path)
    except Exception as exc:
        # Фолбэк на прямое копирование файла (может быть неконсистентно при активном WAL)
        shutil.copy2(db_path, backup_path)
        logger.warning("Online backup не удался (%s). Выполнено файловое копирование: %s", exc, backup_path)

    rotate_backups(backups_dir, prefix="backup_base_sdelka_", suffix=db_path.suffix, keep=max_backups)
    return backup_path


def rotate_backups(backups_dir: Path, prefix: str, suffix: str, keep: int) -> None:
    files = sorted(
        (p for p in backups_dir.glob(f"{prefix}*{suffix}") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for idx, path in enumerate(files):
        if idx >= keep:
            try:
                path.unlink()
                logger.info("Удален старый бэкап: %s", path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Не удалось удалить бэкап %s: %s", path, exc)