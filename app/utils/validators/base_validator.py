"""
Базовый класс валидатора
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import date


class BaseValidator:
    """
    Базовый класс для всех валидаторов в приложении

    Attributes:
        _error_prefix: Префикс для сообщений об ошибках
    """

    def __init__(self):
        """Инициализация валидатора"""
        self._error_prefix = "Данные"

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Проверяет данные на валидность

        Args:
            data: Словарь с данными для валидации

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        raise NotImplementedError("Метод validate должен быть реализован в подклассе")

    def validate_date_range(
            self,
            start_date: date,
            end_date: date,
            field_name: str = "период"
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет диапазон дат

        Args:
            start_date: Дата начала
            end_date: Дата окончания
            field_name: Название поля для сообщения об ошибке

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if start_date > end_date:
            return (
                False,
                f"{self._error_prefix}: {field_name} не может быть пустым или дата начала не может быть позже даты окончания"
            )
        return True, None

    def validate_positive_number(
            self,
            value: float,
            field_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет, что число положительное

        Args:
            value: Число для проверки
            field_name: Название поля

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if value <= 0:
            return False, f"{self._error_prefix}: {field_name} должно быть положительным числом"
        return True, None

    def validate_required_fields(
            self,
            data: Dict[str, Any],
            required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Проверяет обязательные поля

        Args:
            data: Данные для проверки
            required_fields: Список обязательных полей

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"{self._error_prefix}: Поле '{field}' не может быть пустым")

        return len(errors) == 0, errors

    def validate_date_field(
            self,
            value: Any,
            field_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет, что значение является корректной датой

        Args:
            value: Значение для проверки
            field_name: Название поля

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if value is None:
            return True, None

        if not isinstance(value, date):
            return False, f"{self._error_prefix}: {field_name} должно быть корректной датой"

        return True, None

    def validate_string_length(
            self,
            value: str,
            field_name: str,
            min_length: int = 0,
            max_length: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет длину строки

        Args:
            value: Строка для проверки
            field_name: Название поля
            min_length: Минимальная длина
            max_length: Максимальная длина

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if len(value) < min_length:
            return False, f"{self._error_prefix}: {field_name} должно содержать не менее {min_length} символов"

        if max_length is not None and len(value) > max_length:
            return False, f"{self._error_prefix}: {field_name} должно содержать не более {max_length} символов"

        return True, None