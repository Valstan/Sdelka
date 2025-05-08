# File: app/core/utils/utils.py
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Tuple, Optional, Callable, List
from logging import getLogger

logger = getLogger(__name__)

DATE_FORMATS = {
    'default': '%Y-%m-%d',
    'ui': '%d.%m.%Y',
    'filename': '%Y%m%d_%H%M%S'
}

class DateUtils:
    """Утилиты для работы с датами."""
    
    @staticmethod
    def get_current_date() -> date:
        """Возвращает текущую дату"""
        return date.today()
    
    @staticmethod
    def get_current_datetime() -> datetime:
        """Возвращает текущую дату и время"""
        return datetime.now()
    
    @staticmethod
    def format_date(d: date, fmt: str = 'default') -> str:
        """Форматирует дату по заданному формату"""
        return d.strftime(DATE_FORMATS[fmt])
    
    @staticmethod
    def parse_date(s: str, fmt: str = 'default') -> Optional[date]:
        """Парсит строку в дату"""
        try:
            return datetime.strptime(s, DATE_FORMATS[fmt]).date()
        except ValueError:
            return None
    
    @staticmethod
    def get_last_day_of_month(year: int, month: int) -> int:
        """Возвращает последний день месяца"""
        if month == 12:
            return 31
        return (datetime(year, month + 1, 1) - timedelta(days=1)).day
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """Проверяет, что начальная дата не позже конечной"""
        return start_date <= end_date

class ValidationUtils:
    """Утилиты для валидации данных"""
    
    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """Проверяет, что значение не пустое"""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict, set)) and not value:
            return False
        return True
    
    @staticmethod
    def is_valid_date(value: Any) -> bool:
        """Проверяет, что значение является корректной датой"""
        if isinstance(value, date):
            return True
        if isinstance(value, str):
            try:
                date.fromisoformat(value)
                return True
            except ValueError:
                return False
        return False
    
    @staticmethod
    def is_positive_number(value: Any) -> bool:
        """Проверяет, что значение является положительным числом"""
        try:
            number = float(value)
            return number > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Проверяет, что строка является корректным email-адресом"""
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Проверяет, что строка является корректным телефонным номером"""
        phone_regex = r'^\+?1?\d{9,15}$'
        return re.match(phone_regex, phone) is not None
    
    @staticmethod
    def validate_fields(fields: Dict[str, Tuple[Any, List[Callable], str]]) -> Tuple[bool, Dict[str, str]]:
        """Проверяет поля по заданным валидаторам"""
        errors = {}
        
        for field_name, (value, validators, error_message) in fields.items():
            for validator in validators:
                if not validator(value):
                    errors[field_name] = error_message
                    break
        
        return not errors, errors

class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def create_directory(path: str) -> bool:
        """Создает директорию по указанному пути, если она не существует"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Ошибка создания директории {path}: {e}")
            return False

class StringUtils:
    """Утилиты для работы со строками"""
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Обрезает строку до указанной длины, добавляя суффикс"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class CollectionUtils:
    """Утилиты для работы с коллекциями"""
    
    @staticmethod
    def find_by_attr(items: list, attr: str, value: Any) -> Optional[Any]:
        """Находит элемент в списке по значению атрибута"""
        return next((item for item in items if getattr(item, attr, None) == value), None)
    
    @staticmethod
    def group_by(items: list, key_func: Callable) -> Dict[Any, list]:
        """Группирует элементы по ключу"""
        result = {}
        for item in items:
            key = key_func(item)
            result.setdefault(key, []).append(item)
        return result

class NumberUtils:
    """Утилиты для работы с числами"""
    
    @staticmethod
    def round_to(value: float, precision: int = 2) -> float:
        """Округляет число до указанной точности"""
        return round(value, precision)
    
    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """Ограничивает число между минимальным и максимальным значениями"""
        return max(min_value, min(value, max_value))

class EventUtils:
    """Утилиты для работы с событиями"""
    
    @staticmethod
    def bind_events(widget, events: Dict[str, Callable]) -> None:
        """Привязывает события к виджету"""
        for event, handler in events.items():
            widget.bind(event, handler)

class LoggerUtils:
    """Утилиты для логирования"""
    
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """Настраивает логгер"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Добавляем обработчик по умолчанию, если его нет
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger