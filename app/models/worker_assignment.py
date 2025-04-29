# File: app/models/worker_assignment.py
"""
Модель для представления назначения работника к карточке работы.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkerAssignment:
    """
    Модель для представления назначения работника к карточке работы.

    Attributes:
        id: Уникальный идентификатор назначения
        card_id: ID карточки работы
        worker_id: ID работника
        amount: Сумма для работника
        created_at: Дата создания записи
    """

    id: Optional[int] = None
    card_id: int = 0
    worker_id: int = 0
    amount: float = 0.0
    created_at: Optional[datetime] = None