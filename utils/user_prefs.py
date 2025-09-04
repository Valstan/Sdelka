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
    # Яндекс.Диск (WebDAV)
    yandex_remote_dir: str | None = None
    # Метод аутентификации: "oauth" или "basic"
    yandex_auth_method: str | None = "oauth"
    # OAuth токен
    yandex_oauth_token: str | None = None
    # Basic: логин и пароль приложения
    yandex_username: str | None = None
    yandex_app_password: str | None = None
    # Публичная ссылка на папку с базой (для скачивания без токена)
    yandex_public_folder_url: str | None = None
    # Приватный полный путь к файлу базы на Диске (например, "/SdelkaBackups/sdelka_base.db")
    yandex_private_file_path: str | None = None


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
                yandex_remote_dir=data.get("yandex_remote_dir") or (CONFIG.yandex_default_remote_dir or "/SdelkaBackups"),
                yandex_auth_method=(data.get("yandex_auth_method") or "oauth"),
                yandex_oauth_token=data.get("yandex_oauth_token") or None,
                yandex_username=data.get("yandex_username") or None,
                yandex_app_password=data.get("yandex_app_password") or None,
                yandex_public_folder_url=data.get("yandex_public_folder_url") or None,
                yandex_private_file_path=data.get("yandex_private_file_path") or None,
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