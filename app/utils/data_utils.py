"""
File: app/utils/data_utils.py
Различные утилиты для работы с данными.
"""
import os
from typing import Any, Dict, List, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


def is_empty(value: Any) -> bool:
    """
    Проверяет, является ли значение пустым.

    Args:
        value: Значение для проверки

    Returns:
        True, если значение пустое
    """
    return value is None or (
            isinstance(value, (str, list, dict, set)) and not value
    ) or (
            isinstance(value, str) and value.strip() == ''
    )


def calculate_age(birthdate: date) -> int:
    """
    Вычисляет возраст по дате рождения.

    Args:
        birthdate: Дата рождения

    Returns:
        Возраст в годах
    """
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


def truncate_text(text: str, max_length: int = 30) -> str:
    """
    Обрезает текст до заданной длины, добавляя многоточие.

    Args:
        text: Исходный текст
        max_length: Максимальная длина

    Returns:
        Обрезанный текст
    """
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def get_file_extension(filename: str) -> str:
    """
    Возвращает расширение файла.

    Args:
        filename: Имя файла

    Returns:
        Расширение файла в нижнем регистре
    """
    return os.path.splitext(filename)[1].lower()


def is_valid_email(email: str) -> bool:
    """
    Проверяет, является ли строка валидным email-адресом.

    Args:
        email: Строка для проверки

    Returns:
        True если email валиден
    """
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


def get_unique_filename(directory: str, filename: str, extension: str) -> str:
    """
    Возвращает уникальное имя файла.

    Args:
        directory: Директория
        filename: Базовое имя файла
        extension: Расширение файла

    Returns:
        Уникальное имя файла
    """
    base_path = os.path.join(directory, f"{filename}.{extension}")
    counter = 1

    while os.path.exists(base_path):
        base_path = os.path.join(directory, f"{filename}_{counter}.{extension}")
        counter += 1

    return base_path


def chunk_list(input_list: List[Any], chunk_size: int = 100) -> List[List[Any]]:
    """
    Разбивает список на чанки.

    Args:
        input_list: Исходный список
        chunk_size: Размер чанка

    Returns:
        Список с разбиением
    """
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]