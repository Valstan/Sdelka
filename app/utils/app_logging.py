from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import get_paths


def configure_logging(level: int | str = logging.INFO) -> logging.Logger:
    """Configure application logging to console and file.

    Args:
        level: Logging level.

    Returns:
        Logger: Root logger configured.
    """
    paths = get_paths()
    log_file = paths.logs_dir / "app.log"

    logger = logging.getLogger()
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    return logger