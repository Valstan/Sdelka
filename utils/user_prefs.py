from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from config.settings import CONFIG


@dataclass
class UserPrefs:
    list_font_size: int = 12
    ui_font_size: int = 12
    # Путь к файлу базы данных, если None — используется значение по умолчанию из CONFIG
    db_path: str | None = None
    # Предпочтение WAL: если None — используем CONFIG.enable_wal
    enable_wal: bool | None = None
    # Таймаут ожидания блокировок SQLite в миллисекундах
    busy_timeout_ms: int | None = 10000


def load_prefs() -> UserPrefs:
    path = CONFIG.user_settings_path
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return UserPrefs(
                list_font_size=int(data.get("list_font_size", 12)),
                ui_font_size=int(data.get("ui_font_size", 12)),
                db_path=data.get("db_path") or None,
                enable_wal=data.get("enable_wal") if data.get("enable_wal") is not None else None,
                busy_timeout_ms=int(data.get("busy_timeout_ms", 10000)) if data.get("busy_timeout_ms") is not None else 10000,
            )
    except Exception:
        pass
    return UserPrefs()


def save_prefs(prefs: UserPrefs) -> None:
    path = CONFIG.user_settings_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(prefs), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---- Helpers for DB settings ----

def get_current_db_path() -> Path:
    """Возвращает актуальный путь к БД: пользовательский из prefs либо дефолтный из CONFIG.

    Гарантирует существование директории.
    """
    prefs = load_prefs()
    path = Path(prefs.db_path) if prefs.db_path else Path(CONFIG.db_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return path


def set_db_path(new_path: Path | str) -> None:
    prefs = load_prefs()
    prefs.db_path = str(Path(new_path))
    save_prefs(prefs)


def get_enable_wal() -> bool:
    prefs = load_prefs()
    if prefs.enable_wal is None:
        return bool(CONFIG.enable_wal)
    return bool(prefs.enable_wal)


def set_enable_wal(value: bool) -> None:
    prefs = load_prefs()
    prefs.enable_wal = bool(value)
    save_prefs(prefs)


def get_busy_timeout_ms() -> int:
    prefs = load_prefs()
    try:
        return int(prefs.busy_timeout_ms or 10000)
    except Exception:
        return 10000


def set_busy_timeout_ms(value_ms: int) -> None:
    prefs = load_prefs()
    prefs.busy_timeout_ms = int(value_ms)
    save_prefs(prefs)