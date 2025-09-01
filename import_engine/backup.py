from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from utils.user_prefs import get_current_db_path


def make_backup_copy(dest_dir: str | Path | None = None) -> str:
    src = Path(get_current_db_path())
    if not src.exists():
        return ""
    # Приводим к стандарту backup_base_sdelka_MMDD_HHMM
    stamp = datetime.now().strftime("%m%d_%H%M")
    backup_name = f"backup_base_sdelka_{stamp}{src.suffix}"
    if dest_dir:
        target = Path(dest_dir) / backup_name
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target = src.parent / backup_name
    shutil.copy2(src, target)
    return str(target)


