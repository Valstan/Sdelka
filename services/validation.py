from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from config.settings import CONFIG


class ValidationError(ValueError):
    pass


DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")


def validate_date(date_str: str) -> None:
    if not DATE_RE.match(date_str):
        raise ValidationError(
            f"Некорректный формат даты: {date_str}. Ожидается {CONFIG.date_format}"
        )
    day, month, year = map(int, date_str.split("."))
    try:
        dt.date(year, month, day)
    except ValueError as exc:  # noqa: TRY003
        raise ValidationError(f"Некорректная дата: {date_str}") from exc


def validate_positive_quantity(value: float) -> None:
    if value <= 0:
        raise ValidationError("Количество должно быть положительным")


@dataclass(frozen=True)
class WorkOrderRules:
    one_contract_per_order: bool = True


RULES = WorkOrderRules()
