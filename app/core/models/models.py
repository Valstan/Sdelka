# File: app/models/models.py
"""
Модуль содержит классы моделей для представления данных в приложении.
Модели охватывают все основные сущности: Работники, Виды работ, Изделия, Контракты и Карточки работ.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class Worker:
    """
    Модель для представления работника предприятия
    
    Attributes:
        id: Уникальный идентификатор работника
        last_name: Фамилия работника
        first_name: Имя работника
        middle_name: Отчество работника (опционально)
        workshop_number: Номер цеха
        position: Должность
        employee_id: Табельный номер
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
    """
    
    id: Optional[int] = None
    last_name: str = ""
    first_name: str = ""
    middle_name: Optional[str] = None
    workshop_number: str = ""
    position: str = ""
    employee_id: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def full_name(self) -> str:
        """
        Возвращает полное имя работника
        
        Returns:
            Полное имя в формате "Фамилия Имя Отчество" если есть отчество,
            иначе "Фамилия Имя"
        """
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"
    
    @property
    def short_name(self) -> str:
        """
        Возвращает сокращенное имя работника
        
        Returns:
            Строка в формате "Фамилия И.О."
        """
        if self.middle_name:
            return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}."
        return f"{self.last_name} {self.first_name[0]}."

@dataclass
class WorkType:
    """
    Модель для представления вида работы
    
    Attributes:
        id: Уникальный идентификатор вида работы
        name: Наименование работы
        unit: Единица измерения
        price: Цена за единицу работы
        valid_from: Дата начала действия цены
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
    """
    
    id: Optional[int] = None
    name: str = ""
    unit: str = ""
    price: float = 0.0
    valid_from: date = date.today()
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Product:
    """
    Модель для представления изделия
    
    Attributes:
        id: Уникальный идентификатор изделия
        product_number: Номер изделия
        product_type: Тип изделия
        additional_number: Дополнительный номер (опционально)
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
    """
    
    id: Optional[int] = None
    product_number: str = ""
    product_type: str = ""
    additional_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """
        Возвращает полное наименование изделия
        
        Returns:
            Строка с полным наименованием изделия
        """
        full_name = self.product_number + " " + self.product_type
        if self.additional_number:
            full_name += f" ({self.additional_number})"
        return full_name

@dataclass
class Contract:
    """
    Модель для представления контракта
    
    Attributes:
        id: Уникальный идентификатор контракта
        contract_number: Шифр контракта
        start_date: Дата начала действия контракта
        end_date: Дата окончания действия контракта
        description: Описание контракта
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
    """
    
    id: Optional[int] = None
    contract_number: str = ""
    start_date: date = date.today()
    end_date: Optional[date] = None
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class WorkCardItem:
    """
    Модель элемента карточки работы (работа + количество)
    
    Attributes:
        id: Уникальный идентификатор элемента
        work_card_id: ID карточки работы
        work_type_id: ID вида работы
        quantity: Количество выполненных работ
        amount: Сумма за выполненные работы
        work_name: Наименование работы
        price: Цена за единицу работы
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
    """
    
    id: Optional[int] = None
    work_card_id: int = 0
    work_type_id: int = 0
    quantity: float = 0.0
    amount: float = 0.0
    work_name: str = ""
    price: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class WorkCardWorker:
    """
    Модель работника в карточке работы
    
    Attributes:
        work_card_id: ID карточки работы
        worker_id: ID работника
        amount: Сумма для работника
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
        last_name: Фамилия работника
        first_name: Имя работника
        middle_name: Отчество работника (опционально)
    """
    
    work_card_id: int = 0
    worker_id: int = 0
    amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_name: str = ""
    first_name: str = ""
    middle_name: Optional[str] = None
    
    def full_name(self) -> str:
        """
        Возвращает полное имя работника
        
        Returns:
            Полное имя в формате "Фамилия Имя Отчество" если есть отчество,
            иначе "Фамилия Имя"
        """
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

@dataclass
class WorkCard:
    """
    Модель карточки работы
    
    Attributes:
        id: Уникальный идентификатор карточки
        card_number: Номер карточки
        card_date: Дата карточки
        product_id: ID изделия
        contract_id: ID контракта
        total_amount: Общая сумма карточки
        created_at: Дата создания записи
        updated_at: Дата последнего обновления записи
        items: Список элементов работы
        workers: Список работников
        product: Информация об изделии
        contract: Информация о контракте
    """
    
    id: Optional[int] = None
    card_number: int = 0
    card_date: date = date.today()
    product_id: Optional[int] = None
    contract_id: Optional[int] = None
    total_amount: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[WorkCardItem] = None
    workers: List[WorkCardWorker] = None
    product: Optional[Product] = None
    contract: Optional[Contract] = None
    
    def __post_init__(self):
        """Инициализация списков при создании объекта"""
        if self.items is None:
            self.items = []
        if self.workers is None:
            self.workers = []