from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    app_name: str = "Piecework Accounting"
    db_timeout_seconds: int = 10
    backup_max_copies: int = 20


CONFIG = AppConfig()