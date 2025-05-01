"""
Модуль с утилитарными функциями для проекта.
Содержит общие функции, которые могут быть использованы в разных частях приложения.
"""
import os
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def format_date(input_date: Union[date, datetime, str], format_str: str = "%d.%m.%Y") -> str:
    """
    Форматирует дату в строку заданного формата.

    Args:
        input_date: Входная дата в формате date, datetime или строки
        format_str: Строка формата для вывода

    Returns:
        Отформатированная строка с датой
    """
    if isinstance(input_date, (date, datetime)):
        return input_date.strftime(format_str)
    elif isinstance(input_date, str):
        try:
            parsed_date = datetime.strptime(input_date, "%Y-%m-%d")
            return parsed_date.strftime(format_str)
        except ValueError:
            logger.warning(f"Невозможно распознать строку как дату: {input_date}")
            return input_date
    else:
        logger.warning(f"Неподдерживаемый тип данных для форматирования даты: {type(input_date)}")
        return str(input_date)

def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[date]:
    """
    Парсит строку в объект date.

    Args:
        date_str: Строка с датой
        format_str: Формат строки с датой

    Returns:
        Объект date или None в случае ошибки
    """
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        logger.error(f"Невозможно преобразовать строку в дату: {date_str}")
        return None

def format_currency(amount: Union[float, int], decimal_places: int = 2) -> str:
    """
    Форматирует сумму в валюту с заданным количеством знаков после запятой.

    Args:
        amount: Сумма для форматирования
        decimal_places: Количество знаков после запятой

    Returns:
        Отформатированная строка с суммой
    """
    return f"{amount:.{decimal_places}f}"

def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Проверяет корректность диапазона дат.

    Args:
        start_date: Начальная дата
        end_date: Конечная дата

    Returns:
        True, если диапазон корректен, иначе False
    """
    return start_date <= end_date

def get_current_date() -> date:
    """Возвращает текущую дату"""
    return date.today()

def get_current_datetime() -> datetime:
    """Возвращает текущую дату и время"""
    return datetime.now()

def create_directory(path: str) -> bool:
    """
    Создает директорию по указанному пути, если она не существует.

    Args:
        path: Путь к директории

    Returns:
        True, если директория создана или уже существует, иначе False
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка создания директории {path}: {e}")
        return False

def read_file(file_path: str) -> Optional[str]:
    """
    Читает содержимое файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Содержимое файла или None в случае ошибки
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}")
        return None

def write_file(file_path: str, content: str) -> bool:
    """
    Записывает содержимое в файл.

    Args:
        file_path: Путь к файлу
        content: Содержимое для записи

    Returns:
        True, если запись успешна, иначе False
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в файл {file_path}: {e}")
        return False

def chunk_list(input_list: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Делит список на чанки заданного размера.

    Args:
        input_list: Исходный список
        chunk_size: Размер чанка

    Returns:
        Список чанков
    """
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]

def merge_dicts(*dicts: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Объединяет несколько словарей в один.

    Args:
        *dicts: Словари для объединения

    Returns:
        Объединенный словарь
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result

def is_empty(value: Any) -> bool:
    """
    Проверяет, является ли значение пустым.

    Args:
        value: Значение для проверки

    Returns:
        True, если значение пустое (None, пустая строка, пустой список и т.д.), иначе False
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    if isinstance(value, (list, dict, set)) and len(value) == 0:
        return True
    return False

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

def truncate_text(text: str, max_length: int) -> str:
    """
    Обрезает текст до заданной длины, добавляя многоточие в конце.

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
        True, если строка является валидным email-адресом, иначе False
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone: str) -> bool:
    """
    Проверяет, является ли строка валидным номером телефона.

    Args:
        phone: Строка для проверки

    Returns:
        True, если строка является валидным номером телефона, иначе False
    """
    import re
    pattern = r'^\+?[78][-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}$'
    return re.match(pattern, phone) is not None
