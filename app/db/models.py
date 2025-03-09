"""
Модуль содержит классы моделей данных для работы с базой данных.
Представляет собой объектно-ориентированную абстракцию над таблицами БД.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Worker:
    """Модель для представления сотрудника"""
    id: Optional[int] = None
    last_name: str = ""
    first_name: str = ""
    middle_name: Optional[str] = None
    position: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Полное имя сотрудника"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    @property
    def short_name(self) -> str:
        """Сокращенное имя сотрудника (Фамилия И. О.)"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name[0]}. {self.middle_name[0]}."
        return f"{self.last_name} {self.first_name[0]}."

@dataclass
class WorkType:
    """Модель для представления вида работы"""
    id: Optional[int] = None
    name: str = ""
    price: float = 0.0
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Product:
    """Модель для представления изделия"""
    id: Optional[int] = None
    product_number: str = ""
    product_type: str = ""
    additional_number: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Полное наименование изделия"""
        if self.additional_number:
            return f"{self.product_number} {self.product_type} ({self.additional_number})"
        return f"{self.product_number} {self.product_type}"

@dataclass
class Contract:
    """Модель для представления контракта"""
    id: Optional[int] = None
    contract_number: str = ""
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Инициализация после создания объекта"""
        # Обработка начальной даты
        if isinstance(self.start_date, str) and self.start_date:
            try:
                self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
            except ValueError:
                pass

        # Обработка конечной даты
        if isinstance(self.end_date, str) and self.end_date:
            try:
                self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
            except ValueError:
                pass

        # Обработка дат создания и обновления
        if isinstance(self.created_at, str) and self.created_at:
            try:
                self.created_at = datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        if isinstance(self.updated_at, str) and self.updated_at:
            try:
                self.updated_at = datetime.strptime(self.updated_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

    @property
    def formatted_start_date(self) -> str:
        """Отформатированная начальная дата контракта"""
        if self.start_date:
            if isinstance(self.start_date, datetime):
                return self.start_date.strftime("%d.%m.%Y")
            return str(self.start_date)
        return "-"

    @property
    def formatted_end_date(self) -> str:
        """Отформатированная конечная дата контракта"""
        if self.end_date:
            if isinstance(self.end_date, datetime):
                return self.end_date.strftime("%d.%m.%Y")
            return str(self.end_date)
        return "-"

@dataclass
class WorkCardItem:
    """Модель для представления элемента карточки работ (вида работы в карточке)"""
    id: Optional[int] = None
    work_card_id: int = 0
    work_type_id: int = 0
    quantity: int = 0
    amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Дополнительные поля для отображения
    work_name: Optional[str] = None
    price: Optional[float] = None

@dataclass
class WorkCardWorker:
    """Модель для представления сотрудника в карточке работ"""
    id: Optional[int] = None
    work_card_id: int = 0
    worker_id: int = 0
    amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Дополнительные поля для отображения
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Полное имя сотрудника"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

@dataclass
class WorkCard:
    """Модель для представления карточки работ"""
    id: Optional[int] = None
    card_number: int = 0
    card_date: Optional[datetime] = None
    product_id: Optional[int] = None
    contract_id: Optional[int] = None
    total_amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Дополнительные поля для отображения
    product_number: Optional[str] = None
    product_type: Optional[str] = None
    contract_number: Optional[str] = None

    # Связанные объекты
    items: List[WorkCardItem] = None
    workers: List[WorkCardWorker] = None

    def __post_init__(self):
        """Инициализация после создания объекта"""
        # Инициализация списков
        if self.items is None:
            self.items = []
        if self.workers is None:
            self.workers = []

        # Обработка даты карточки
        if isinstance(self.card_date, str) and self.card_date:
            try:
                # Пытаемся преобразовать строку в datetime
                self.card_date = datetime.strptime(self.card_date, "%Y-%m-%d")
            except ValueError:
                # Если формат строки неверный, оставляем строку (будет обработано в formatted_date)
                pass

    def calculate_total_amount(self) -> float:
        """Расчет общей суммы карточки на основе элементов"""
        if not self.items:
            return 0.0
        return sum(item.amount for item in self.items)

    def calculate_worker_amount(self) -> float:
        """Расчет суммы на одного работника"""
        if not self.workers or self.total_amount == 0:
            return 0.0
        return self.total_amount / len(self.workers)

    def distribute_amount_to_workers(self) -> None:
        """Распределение суммы между работниками бригады"""
        worker_amount = self.calculate_worker_amount()
        for worker in self.workers:
            worker.amount = worker_amount

    @property
    def formatted_date(self) -> str:
        """Отформатированная дата карточки в удобном для отображения формате"""
        if self.card_date:
            if isinstance(self.card_date, datetime):
                return self.card_date.strftime("%d.%m.%Y")
            return str(self.card_date)  # Если дата в виде строки
        return "-"