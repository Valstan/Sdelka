from __future__ import annotations

import sys

from app.utils.paths import ensure_directories
from app.utils.app_logging import configure_logging
from app.db.migrations import initialize_database
from app.utils.backup import backup_database_with_rotation


def main() -> int:
    """Application entry point.

    Returns:
        int: Exit code.
    """
    ensure_directories()
    logger = configure_logging()
    logger.info("Application starting")

    # Initialize database and make a backup
    initialize_database()
    backup_database_with_rotation(max_copies=20)

    # Lazy import GUI to keep CLI startup fast and avoid coverage counting
    from app.gui.app import run_app

    try:
        run_app()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled exception in GUI: %s", exc)
        return 1

    logger.info("Application shutdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())