"""
Валидатор данных работника
"""

from typing import Dict, List, Tuple, Any, Optional

from app.utils.validators.base_validator import BaseValidator


class WorkerValidator(BaseValidator):
    """
    Валидатор для проверки данных работника

    Attributes:
        _error_prefix: Префикс для сообщений об ошибках
    """

    def __init__(self):
        """Инициализация валидатора"""
        super().__init__()
        self._error_prefix = "Работник"

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Проверяет данные работника

        Args:
            data: Словарь с данными работника

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        # Проверка обязательных полей
        required_fields = {
            "last_name": "Фамилия",
            "first_name": "Имя",
            "employee_id": "Табельный номер",
            "workshop_number": "Номер цеха"
        }

        for field, field_name in required_fields.items():
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"{self._error_prefix}: {field_name} не может быть пустым")

        # Проверка типов данных
        if "employee_id" in data:
            try:
                int(data["employee_id"])
            except (ValueError, TypeError):
                errors.append(f"{self._error_prefix}: Табельный номер должен быть числом")

        if "workshop_number" in data:
            try:
                int(data["workshop_number"])
            except (ValueError, TypeError):
                errors.append(f"{self._error_prefix}: Номер цеха должен быть числом")

        # Проверка диапазонов значений
        if "employee_id" in data and int(data["employee_id"]) <= 0:
            errors.append(f"{self._error_prefix}: Табельный номер должен быть положительным числом")

        if "workshop_number" in data and int(data["workshop_number"]) <= 0:
            errors.append(f"{self._error_prefix}: Номер цеха должен быть положительным числом")

        return len(errors) == 0, errors

    def validate_unique_employee_id(self, employee_id: int, existing_ids: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Проверяет уникальность табельного номера

        Args:
            employee_id: Табельный номер для проверки
            existing_ids: Список существующих табельных номеров

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if employee_id in existing_ids:
            return False, f"{self._error_prefix}: Табельный номер {employee_id} уже существует"
        return True, None

    def validate_workshop_number(self, workshop_number: int) -> Tuple[bool, Optional[str]]:
        """
        Проверяет корректность номера цеха

        Args:
            workshop_number: Номер цеха для проверки

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if workshop_number <= 0:
            return False, f"{self._error_prefix}: Номер цеха должен быть положительным числом"
        return True, None

    def validate_full_name(self, full_name: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет корректность полного имени

        Args:
            full_name: Полное имя (ФИО)

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        parts = full_name.strip().split()
        if len(parts) < 2:
            return False, f"{self._error_prefix}: Введите полное имя (Фамилия Имя [Отчество])"
        return True, None