# File: app/core/utils/form_validator.py

from typing import Callable, Dict, Any
from datetime import date
from tkinter import messagebox
from logging import getLogger

logger = getLogger(__name__)


class FormValidator:
    """Класс для валидации данных формы."""

    @staticmethod
    def required(field_name: str, value: Any, error_message: str = None) -> bool:
        """Проверяет, что поле не пустое."""
        if not value or (isinstance(value, str) and not value.strip()):
            messagebox.showerror("Ошибка", error_message or f"Поле '{field_name}' обязательно для заполнения")
            return False
        return True

    @staticmethod
    def valid_date(field_name: str, value: str, error_message: str = None) -> bool:
        """Проверяет, что значение является корректной датой."""
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            messagebox.showerror("Ошибка", error_message or f"Некорректная дата в поле '{field_name}'")
            return False

    @staticmethod
    def date_after(field_name1: str, value1: str, field_name2: str, value2: str, error_message: str = None) -> bool:
        """Проверяет, что первая дата не позже второй."""
        try:
            date1 = date.fromisoformat(value1)
            date2 = date.fromisoformat(value2)
            if date1 > date2:
                messagebox.showerror("Ошибка",
                                     error_message or f"Дата '{field_name1}' не может быть позже '{field_name2}'")
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def numeric_positive(field_name: str, value: str, error_message: str = None) -> bool:
        """Проверяет, что значение является положительным числом."""
        try:
            number = float(value)
            if number <= 0:
                messagebox.showerror("Ошибка",
                                     error_message or f"Значение в поле '{field_name}' должно быть положительным")
                return False
            return True
        except ValueError:
            messagebox.showerror("Ошибка", error_message or f"Некорректное значение в поле '{field_name}'")
            return False

    @staticmethod
    def unique(field_name: str, value: Any, existing_values: list, error_message: str = None) -> bool:
        """Проверяет уникальность значения."""
        if value in existing_values:
            messagebox.showerror("Ошибка", error_message or f"Значение в поле '{field_name}' должно быть уникальным")
            return False
        return True

    @staticmethod
    def validate_all(validators: list) -> bool:
        """Выполняет все валидаторы и возвращает общий результат."""
        return all(validators)