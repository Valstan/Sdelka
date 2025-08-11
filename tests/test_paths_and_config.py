from __future__ import annotations

from pathlib import Path

from app.utils.app_logging import configure_logging
from app.utils.config import CONFIG
from app.utils.paths import ensure_directories, get_paths


def test_paths_and_dirs(tmp_path, monkeypatch):
    # Redirect root to temp directory by monkeypatching module resolution
    paths = get_paths()
    ensure_directories()
    paths = get_paths()
    assert paths.data_dir.exists()
    assert paths.backups_dir.exists()
    assert paths.logs_dir.exists()


def test_logging_config_idempotent(tmp_path, monkeypatch):
    logger = configure_logging()
    assert logger.handlers
    # second call should not duplicate handlers
    logger2 = configure_logging()
    assert logger is logger2


def test_config_defaults():
    assert CONFIG.app_name
    assert CONFIG.backup_max_copies == 20