"""
Валидатор для нарядов работ
"""

from typing import Dict, Any, List, Tuple
from datetime import date
from app.utils.validators.base_validator import BaseValidator


class WorkCardValidator(BaseValidator):
    """
    Валидатор для проверки данных нарядов работ

    Attributes:
        _error_prefix: Префикс для сообщений об ошибках
    """

    def __init__(self):
        """Инициализация валидатора"""
        super().__init__()
        self._error_prefix = "Наряд"

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Проверяет данные наряда

        Args:
            data: Словарь с данными наряда

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        # Проверка обязательных полей
        required_fields = {
            "card_number": "Номер наряда",
            "card_date": "Дата наряда",
            "product_id": "ID изделия",
            "contract_id": "ID контракта"
        }

        for field, field_name in required_fields.items():
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"{self._error_prefix}: {field_name} не может быть пустым")

        # Проверка даты
        if "card_date" in data:
            try:
                card_date = date.fromisoformat(data["card_date"])
                if card_date > date.today():
                    errors.append(f"{self._error_prefix}: Дата наряда не может быть в будущем")
            except ValueError:
                errors.append(f"{self._error_prefix}: Некорректная дата наряда")

        # Проверка ID изделий
        if "product_id" in data and int(data["product_id"]) <= 0:
            errors.append(f"{self._error_prefix}: ID изделия должно быть положительным числом")

        # Проверка ID контрактов
        if "contract_id" in data and int(data["contract_id"]) <= 0:
            errors.append(f"{self._error_prefix}: ID контракта должно быть положительным числом")

        # Проверка уникальности номера наряда
        if "card_number" in data and data["card_number"] in self.existing_card_numbers:
            errors.append(f"{self._error_prefix}: Наряд с таким номером уже существует")

        return len(errors) == 0, errors

    def validate_items(self, items: List[Any]) -> Tuple[bool, List[str]]:
        """
        Проверяет элементы наряда

        Args:
            items: Список элементов наряда

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        if not items:
            errors.append(f"{self._error_prefix}: Наряд должен содержать хотя бы один элемент")
            return False, errors

        for i, item in enumerate(items):
            if hasattr(item, "validate"):
                is_valid, item_errors = item.validate()
                if not is_valid:
                    for error in item_errors:
                        errors.append(f"Элемент #{i + 1}: {error}")

        return len(errors) == 0, errors

    def validate_workers(self, workers: List[int]) -> Tuple[bool, List[str]]:
        """
        Проверяет список работников

        Args:
            workers: Список ID работников

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        if not workers:
            errors.append(f"{self._error_prefix}: Наряд должен содержать хотя бы одного работника")
            return False, errors

        if len(workers) != len(set(workers)):
            errors.append(f"{self._error_prefix}: Список работников содержит дубликаты")

        return len(errors) == 0, errors

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
        if start_date and end_date and start_date > end_date:
            return False, f"{self._error_prefix}: {field_name} не может быть пустым или дата начала не может быть позже даты окончания"
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


# Глобальный экземпляр валидатора для использования в разных модулях
work_card_validator = WorkCardValidator()