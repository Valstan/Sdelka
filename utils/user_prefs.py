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


def load_prefs() -> UserPrefs:
    path = CONFIG.user_settings_path
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return UserPrefs(
                list_font_size=int(data.get("list_font_size", 12)),
                ui_font_size=int(data.get("ui_font_size", 12)),
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