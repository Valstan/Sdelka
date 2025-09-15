from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "PieceworkApp"
    base_dir: Path = Path(os.environ.get("APP_BASE_DIR", Path.cwd()))

    data_dir: Path = base_dir / "data"
    db_path: Path = data_dir / "base_sdelka_rmz.db"
    user_settings_path: Path = data_dir / "user_settings.json"

    backups_dir: Path = base_dir / "backups"
    logs_dir: Path = base_dir / "logs"

    # UI
    date_format: str = "%d.%m.%Y"  # ДД.ММ.ГГГГ
    autocomplete_limit: int = 10
    autocomplete_debounce_ms: int = 250

    # Backup
    max_backup_files: int = 20

    # Yandex Disk defaults
    yandex_default_remote_dir: str = "/SdelkaBackups"
    # OAuth token is loaded from environment variable `YADISK_OAUTH_TOKEN` at runtime.
    # Do NOT store secrets in source code. Leave blank here.
    yandex_default_oauth_token: str = ""

    # DB
    enable_wal: bool = True


CONFIG = AppConfig()


def ensure_data_directories(config: AppConfig = CONFIG) -> None:
    """Create data, backups and logs directories. Call explicitly during startup.

    This avoids side-effects at module import time and makes the operation
    explicit and testable.
    """
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.backups_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
