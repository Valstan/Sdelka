"""
Общие валидаторы для различных сущностей
"""

from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import date
from decimal import Decimal
from app.utils.validators.base_validator import BaseValidator


class CommonValidators(BaseValidator):
    """
    Общий валидатор с универсальными правилами валидации
    """

    def __init__(self):
        """Инициализация валидатора"""
        super().__init__()
        self._error_prefix = "Данные"

    def validate_date_range(
            self,
            start_date: Optional[date],
            end_date: Optional[date],
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
        result = super().validate_date_range(start_date, end_date, field_name)
        self._error_prefix = "Дата"
        return result

    def validate_positive_number(
            self,
            value: Union[int, float, Decimal],
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
        result = super().validate_positive_number(value, field_name)
        self._error_prefix = "Число"
        return result

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
        result = super().validate_required_fields(data, required_fields)
        self._error_prefix = "Поле"
        return result

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
        result = super().validate_string_length(value, field_name, min_length, max_length)
        self._error_prefix = "Строка"
        return result

    def validate_unique_value(
            self,
            value: Any,
            existing_values: List[Any],
            field_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет уникальность значения

        Args:
            value: Значение для проверки
            existing_values: Список существующих значений
            field_name: Название поля

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if value in existing_values:
            return False, f"{field_name} '{value}' уже существует"
        return True, None

    def validate_nested_objects(
            self,
            items: List[Any],
            field_name: str
    ) -> Tuple[bool, List[str]]:
        """
        Проверяет вложенные объекты

        Args:
            items: Список объектов для проверки
            field_name: Название поля

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        if not items:
            return True, []

        for i, item in enumerate(items):
            if hasattr(item, "validate"):
                is_valid, item_errors = item.validate()
                if not is_valid:
                    for error in item_errors:
                        errors.append(f"{field_name} #{i + 1}: {error}")

        return len(errors) == 0, errors

    def validate_non_empty_list(
            self,
            items: List[Any],
            field_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет, что список не пустой

        Args:
            items: Список для проверки
            field_name: Название поля

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if not items:
            return False, f"{field_name} должен содержать хотя бы один элемент"
        return True, None


# Глобальный экземпляр валидатора для использования в разных модулях
common_validators = CommonValidators()