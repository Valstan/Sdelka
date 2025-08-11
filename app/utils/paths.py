from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Strongly-typed container for application paths."""

    root: Path
    data_dir: Path
    db_file: Path
    backups_dir: Path
    logs_dir: Path
    reports_dir: Path
    templates_dir: Path


def get_paths() -> AppPaths:
    """Return primary application filesystem paths.

    Returns:
        AppPaths: Resolved paths.
    """
    root = Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    backups_dir = data_dir / "backups"
    logs_dir = root / "logs"
    db_file = data_dir / "app.db"
    reports_dir = root / "reports"
    templates_dir = root / "app" / "reports" / "templates"
    return AppPaths(
        root=root,
        data_dir=data_dir,
        db_file=db_file,
        backups_dir=backups_dir,
        logs_dir=logs_dir,
        reports_dir=reports_dir,
        templates_dir=templates_dir,
    )


def ensure_directories() -> None:
    """Ensure required directories exist."""
    paths = get_paths()
    for directory in (paths.data_dir, paths.backups_dir, paths.logs_dir, paths.reports_dir):
        directory.mkdir(parents=True, exist_ok=True)