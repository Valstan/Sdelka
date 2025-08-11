from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from dateutil import parser

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class ValidationError(Exception):
    """Domain validation error."""

    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def require_positive(value: float, name: str) -> None:
    """Ensure value is strictly positive.

    Args:
        value: Numeric value to validate.
        name: Field name for error message.

    Raises:
        ValidationError: If value <= 0.
    """
    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")


def require_non_negative(value: float, name: str) -> None:
    """Ensure value is non-negative."""
    if value < 0:
        raise ValidationError(f"{name} must be >= 0, got {value}")


def parse_iso_date(value: str) -> date:
    """Parse and validate ISO date (YYYY-MM-DD)."""
    if not DATE_RE.match(value):
        raise ValidationError(f"Date must be YYYY-MM-DD, got {value}")
    try:
        dt = parser.isoparse(value).date()
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"Invalid date: {value}") from exc
    return dt


def ensure_unique(values: Iterable[str], entity: str, field: str) -> None:
    """Validate uniqueness within a batch to import/insert."""
    seen: set[str] = set()
    for v in values:
        if (v_norm := v.strip().lower()) in seen:
            raise ValidationError(f"Duplicate {entity} {field}: {v}")
        seen.add(v_norm)