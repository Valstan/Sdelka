from __future__ import annotations

from enum import Enum


class AppMode(str, Enum):
    FULL = "full"
    READONLY = "readonly"


_CURRENT_MODE: AppMode = AppMode.FULL


def set_mode(mode: AppMode) -> None:
    global _CURRENT_MODE
    _CURRENT_MODE = mode


def get_mode() -> AppMode:
    return _CURRENT_MODE


def is_readonly() -> bool:
    return _CURRENT_MODE == AppMode.READONLY


