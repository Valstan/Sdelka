"""
Модуль содержит классы моделей данных для работы с базой данных.
Представляет собой объектно-ориентированную абстракцию над таблицами БД.
"""
from dataclasses import dataclass
from datetime import datetime, date
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
            return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}."
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
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_start_date(self) -> str:
        """Отформатированная дата начала контракта"""
        return self.start_date.strftime("%d.%m.%Y") if self.start_date else "-"

    @property
    def formatted_end_date(self) -> str:
        """Отформатированная дата окончания контракта"""
        return self.end_date.strftime("%d.%m.%Y") if self.end_date else "-"

@dataclass
class WorkCardItem:
    """Модель для представления элемента карточки работ (вида работы в карточке)"""
    id: Optional[int] = None
    card_date: Optional[datetime] = None
    work_card_id: int = 0
    work_type_id: int = 0
    quantity: int = 0
    amount: float = 0.0
    work_name: Optional[str] = None
    price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_date(self) -> str:
        """Отформатированная дата карточки"""
        if isinstance(self.card_date, str):
            # Конвертируем строку в объект date
            try:
                return datetime.strptime(self.card_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            except ValueError:
                return "-"
        elif isinstance(self.card_date, (datetime, date)):
            return self.card_date.strftime("%d.%m.%Y")
        else:
            return "-"

@dataclass
class WorkCardWorker:
    """Модель для представления работника в карточке работ"""
    id: Optional[int] = None
    work_card_id: int = 0
    worker_id: int = 0
    amount: float = 0.0
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Полное имя работника"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

@dataclass
class WorkCard:
    """Модель для представления карточки работ"""
    id: Optional[int] = None
    card_number: int = 0
    card_date: Optional[date] = None
    product_id: Optional[int] = None
    contract_id: Optional[int] = None
    total_amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Связанные сущности
    items: List[WorkCardItem] = None
    workers: List[WorkCardWorker] = None
    product: Optional[Product] = None
    contract: Optional[Contract] = None

    def __post_init__(self):
        """Инициализация списков, если они не заданы"""
        if self.items is None:
            self.items = []
        if self.workers is None:
            self.workers = []

    def calculate_total_amount(self) -> float:
        """Расчет общей суммы карточки на основе элементов"""
        return sum(item.amount for item in self.items)

    def calculate_worker_amount(self) -> float:
        """Расчет суммы на одного работника"""
        if not self.workers or self.total_amount == 0:
            return 0.0
        return self.total_amount / len(self.workers)

    @property
    def formatted_date(self) -> str:
        """Отформатированная дата карточки"""
        return self.card_date.strftime("%d.%m.%Y") if self.card_date else "-"

    @property
    def product_name(self) -> str:
        """Название изделия"""
        return self.product.full_name if self.product else "-"

    @property
    def contract_number(self) -> str:
        """Номер контракта"""
        return self.contract.contract_number if self.contract else "-"
