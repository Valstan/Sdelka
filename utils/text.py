from __future__ import annotations


def normalize_for_search(value: str | None) -> str | None:
    if value is None:
        return None
    return value.casefold().strip()