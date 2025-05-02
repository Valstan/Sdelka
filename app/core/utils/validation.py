"""
File: app/core/utils/validation.py
Базовые функции валидации данных.
"""

import re
from typing import Any, Callable, Optional, Tuple
from datetime import date, datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def is_not_empty(value: Any) -> bool:
    """Проверяет, что значение не пустое."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict, set)) and not value:
        return False
    return True


def is_valid_date(value: Any) -> bool:
    """Проверяет, что значение является корректной датой."""
    if isinstance(value, date):
        return True
    if isinstance(value, str):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


def is_valid_email(email: str) -> bool:
    """Проверяет, что строка является корректным email-адресом."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def is_positive_number(value: Any) -> bool:
    """Проверяет, что значение является положительным числом."""
    try:
        number = float(value)
        return number > 0
    except (ValueError, TypeError):
        return False


def is_valid_phone(phone: str) -> bool:
    """Проверяет, что строка является корректным телефонным номером."""
    phone_regex = r'^\+?1?\d{9,15}$'
    return re.match(phone_regex, phone) is not None


def validate_field(
        value: Any,
        validators: list,
        error_message: str = "Некорректное значение"
) -> Tuple[bool, Optional[str]]:
    """Валидирует значение с помощью списка валидаторов."""
    for validator in validators:
        if not validator(value):
            return False, error_message
    return True, None


def validate_form(fields: dict) -> Tuple[bool, dict]:
    """Валидирует форму с полями и их валидаторами."""
    errors = {}

    for field_name, (value, validators, error_message) in fields.items():
        for validator in validators:
            if not validator(value):
                errors[field_name] = error_message
                break

    return not errors, errors


def validate_model(model: object, fields: dict) -> Tuple[bool, dict]:
    """Валидирует модель с полями и их валидаторами."""
    errors = {}

    for field_name, (getter, validators, error_message) in fields.items():
        value = getter(model)
        for validator in validators:
            if not validator(value):
                errors[field_name] = error_message
                break

    return not errors, errors


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Проверяет, что диапазон дат корректен."""
    return start_date <= end_date


def validate_unique(collection: list, key_func: Callable) -> bool:
    """Проверяет, что все элементы в коллекции уникальны по указанному ключу."""
    seen = set()
    for item in collection:
        key = key_func(item)
        if key in seen:
            return False
        seen.add(key)
    return True


def validate_positive(value: Any) -> bool:
    """Проверяет, что значение является положительным."""
    try:
        number = float(value)
        return number > 0
    except (ValueError, TypeError):
        return False


def validate_min_length(min_length: int) -> Callable:
    """Создает валидатор для проверки минимальной длины."""

    def validator(value: Any) -> bool:
        return len(str(value)) >= min_length

    return validator


def validate_max_length(max_length: int) -> Callable:
    """Создает валидатор для проверки максимальной длины."""

    def validator(value: Any) -> bool:
        return len(str(value)) <= max_length

    return validator


def validate_range(min_value: Any, max_value: Any) -> Callable:
    """Создает валидатор для проверки диапазона значений."""

    def validator(value: Any) -> bool:
        try:
            num = float(value)
            return min_value <= num <= max_value
        except (ValueError, TypeError):
            return False

    return validator


def validate_with_message(validator: Callable, message: str) -> Callable:
    """Оборачивает валидатор, добавляя сообщение об ошибке."""

    def wrapper(value: Any) -> Tuple[bool, str]:
        result = validator(value)
        return result, "" if result else message

    return wrapper


def validate_required_field(field_name: str) -> Callable:
    """Создает валидатор для обязательного поля."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[bool, str]:
            value = kwargs.get(field_name)
            if value is None:
                for arg in args:
                    if hasattr(arg, field_name):
                        value = getattr(arg, field_name)
                        break

            if not is_not_empty(value):
                return False, f"Поле '{field_name}' обязательно для заполнения"

            return func(*args, **kwargs)

        return wrapper

    return decorator