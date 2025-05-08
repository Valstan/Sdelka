# app/utils/formatters.py
import decimal
from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime
from decimal import Decimal


def format_date(value: Union[date, datetime, str], input_format: str = "%Y-%m-%d",
                output_format: str = "%d.%m.%Y") -> str:
    """
    Форматирует дату.

    Args:
        value: Дата в виде строки или объекта date/datetime
        input_format: Формат входной даты
        output_format: Формат выходной даты

    Returns:
        str: Отформатированная дата
    """
    if isinstance(value, (date, datetime)):
        return value.strftime(output_format)
    try:
        return datetime.strptime(value, input_format).strftime(output_format)
    except (ValueError, TypeError):
        return value


def format_currency(value: Union[int, float, Decimal], currency: str = "руб.") -> str:
    """
    Форматирует денежное значение.

    Args:
        value: Числовое значение
        currency: Валюта

    Returns:
        str: Отформатированное значение
    """
    try:
        # Проверяем, является ли значение числом
        numeric_value = Decimal(value)
        # Форматируем с разделением на разряды
        formatted_value = "{:,.2f}".format(numeric_value).replace(",", " ")
        return f"{formatted_value} {currency}"
    except (ValueError, TypeError, decimal.InvalidOperation):
        return f"{value} {currency}"


def format_full_name(last_name: str, first_name: str, middle_name: Optional[str] = None) -> str:
    """
    Форматирует полное имя.

    Args:
        last_name: Фамилия
        first_name: Имя
        middle_name: Отчество (опционально)

    Returns:
        str: Полное имя
    """
    if middle_name:
        return f"{last_name} {first_name} {middle_name}"
    return f"{last_name} {first_name}"