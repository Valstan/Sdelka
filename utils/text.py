from __future__ import annotations

import re
from datetime import datetime


def normalize_for_search(value: str | None) -> str | None:
    if value is None:
        return None
    return value.casefold().strip()


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Return a filesystem-safe filename stem (без расширения).

    - Удаляет запрещённые символы / \ : * ? " < > | и управляющие
    - Режет до max_length
    - Убирает начальные/конечные точки и пробелы
    """
    # Replace forbidden characters with underscore
    name = re.sub(r"[\\/:*?\"<>|\x00-\x1F]", "_", name)
    # Collapse spaces
    name = re.sub(r"\s+", " ", name).strip()
    # Remove trailing dots/spaces
    name = name.strip(" .")
    # Limit length
    if len(name) > max_length:
        name = name[:max_length].rstrip(" .")
    return name or "file"