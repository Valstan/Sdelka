from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.utils.paths import get_paths


def backup_database_with_rotation(max_copies: int = 20) -> Path:
    """Create timestamped backup of the database and rotate old copies.

    Args:
        max_copies: Maximum number of backups to retain.

    Returns:
        Path: Backup file path created.
    """
    paths = get_paths()
    db_path = paths.db_file
    if not db_path.exists():
        return db_path  # Nothing to back up yet

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = paths.backups_dir / f"app_{timestamp}.db"
    shutil.copy2(db_path, backup_path)

    backups = sorted(paths.backups_dir.glob("app_*.db"), reverse=True)
    for old in backups[max_copies:]:
        try:
            old.unlink()
        except Exception:
            pass
    return backup_path