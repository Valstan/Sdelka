from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "PieceworkApp"
    base_dir: Path = Path(os.environ.get("APP_BASE_DIR", Path.cwd()))

    data_dir: Path = base_dir / "data"
    db_path: Path = data_dir / "app.db"
    user_settings_path: Path = data_dir / "user_settings.json"

    backups_dir: Path = base_dir / "backups"
    logs_dir: Path = base_dir / "logs"

    # UI
    date_format: str = "%d.%m.%Y"  # ДД.ММ.ГГГГ
    autocomplete_limit: int = 10
    autocomplete_debounce_ms: int = 250

    # Backup
    max_backup_files: int = 20

    # DB
    enable_wal: bool = True


CONFIG = AppConfig()

# Ensure directories exist at import time
CONFIG.data_dir.mkdir(parents=True, exist_ok=True)
CONFIG.backups_dir.mkdir(parents=True, exist_ok=True)
CONFIG.logs_dir.mkdir(parents=True, exist_ok=True)