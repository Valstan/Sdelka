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


def short_fio(full_name: str) -> str:
    """Format full name to 'Фамилия И.О.' keeping only initials for name and patronymic.

    - Trims spaces, collapses multiple spaces
    - Handles hyphenated surnames and multi-part names; takes first word as surname
    - Returns original string if it cannot parse at least a surname
    """
    if not full_name:
        return ""
    s = " ".join(str(full_name).strip().split())
    if not s:
        return ""
    parts = s.split(" ")
    if len(parts) == 1:
        return parts[0]
    surname = parts[0]
    initials = []
    for p in parts[1:3]:  # имя, отчество
        p = p.strip(" .-")
        if p:
            initials.append(p[0].upper())
    if not initials:
        return surname
    return f"{surname} {' '.join(i + '.' for i in initials)}"