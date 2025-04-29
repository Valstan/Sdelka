# File: app/models/worker.py
"""
Модель для представления данных о работнике.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Worker:
    """
    Модель для представления данных о работнике.

    Attributes:
        id: Уникальный идентификатор работника
        last_name: Фамилия
        first_name: Имя
        middle_name: Отчество
        workshop_number: Номер цеха
        position: Должность
        employee_id: Табельный номер
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    id: Optional[int] = None
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    workshop_number: int = 0
    position: str = ""
    employee_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """
        Возвращает полное имя работника в формате "Фамилия И.О.".

        Returns:
            Полное имя работника
        """
        names = [self.last_name, self.first_name[0] + "." if self.first_name else ""]

        if self.middle_name:
            names.append(self.middle_name[0] + ".")

        return " ".join(names)