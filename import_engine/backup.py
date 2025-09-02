from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from utils.user_prefs import get_current_db_path
from config.settings import CONFIG


def make_backup_copy(dest_dir: str | Path | None = None) -> str:
    src = Path(get_current_db_path())
    if not src.exists():
        return ""
    # Приводим к стандарту backup_base_sdelka_MMDD_HHMM
    stamp = datetime.now().strftime("%m%d_%H%M")
    backup_name = f"backup_base_sdelka_{stamp}{src.suffix}"
    # По умолчанию — всегда в каталог бэкапов приложения
    target_dir = Path(dest_dir) if dest_dir else CONFIG.backups_dir
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    target = target_dir / backup_name
    shutil.copy2(src, target)
    return str(target)


