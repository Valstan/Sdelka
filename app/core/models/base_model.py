# app/core/models/base_model.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseModel')

@dataclass
class BaseModel(ABC):
    """
    Базовая модель для всех сущностей приложения.

    Attributes:
        id: Уникальный идентификатор сущности
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления
    """
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует модель в словарь.

        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            field: value.isoformat() if isinstance(value, (date, datetime)) else value
            for field, value in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Создает экземпляр модели из словаря.

        Args:
            data: Словарь с данными

        Returns:
            T: Экземпляр модели
        """
        # Фильтруем неизвестные поля
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных модели.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        # Проверка обязательных полей
        for field_name, field_info in self.__dataclass_fields__.items():  # type: ignore
            if not field_info.init:
                continue

            value = getattr(self, field_name)

            # Проверка обязательных полей
            if field_info.default is field_info.default_factory is None and value is None:
                errors.append(f"Поле '{field_name}' не может быть пустым")

        return len(errors) == 0, errors

    def __post_init__(self):
        """Дополнительная инициализация после создания объекта"""
        # Убедимся, что даты имеют правильный формат
        for field_name, field_type in self.__annotations__.items():
            value = getattr(self, field_name)

            if value is None:
                continue

            if field_type == datetime and not isinstance(value, datetime):
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except (ValueError, TypeError):
                    logger.warning(f"Неверный формат даты для поля {field_name}: {value}")

            elif field_type == date and not isinstance(value, date):
                try:
                    setattr(self, field_name, date.fromisoformat(value))
                except (ValueError, TypeError):
                    logger.warning(f"Неверный формат даты для поля {field_name}: {value}")

    def __str__(self) -> str:
        """
        Возвращает строковое представление модели.

        Returns:
            str: Строковое представление
        """
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self) -> str:
        """
        Возвращает строку для восстановления объекта.

        Returns:
            str: Строка для восстановления объекта
        """
        fields = []
        for field_name, _ in self.__dataclass_fields__.items():  # type: ignore
            value = getattr(self, field_name)
            if isinstance(value, str):
                fields.append(f"{field_name}='{value}'")
            else:
                fields.append(f"{field_name}={value}")
        return f"{self.__class__.__name__}({', '.join(fields)})"

@dataclass
class Worker(BaseModel):
    """
    Модель работника предприятия.

    Attributes:
        last_name: Фамилия
        first_name: Имя
        middle_name: Отчество
        department_number: Номер цеха
        position: Должность
        employee_number: Табельный номер
    """
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    department_number: int = 0
    position: str = ""
    employee_number: str = ""

    def full_name(self) -> str:
        """
        Возвращает полное имя работника.

        Returns:
            str: Полное имя
        """
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    def short_name(self) -> str:
        """
        Возвращает краткое имя работника.

        Returns:
            str: Краткое имя
        """
        return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}." if self.middle_name else f"{self.last_name} {self.first_name[0]}."

@dataclass
class WorkType(BaseModel):
    """
    Модель вида работы.

    Attributes:
        name: Наименование работы
        unit: Единица измерения ('штуки', 'комплекты')
        price: Цена
        valid_from: Дата начала действия цены
    """
    name: str = ""
    unit: str = "штуки"
    price: float = 0.0
    valid_from: Optional[date] = None

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        success, errors = super().validate()

        # Проверка единицы измерения
        if self.unit not in ("штуки", "комплекты"):
            errors.append("Единица измерения должна быть 'штуки' или 'комплекты'")

        # Проверка цены
        if self.price <= 0:
            errors.append("Цена должна быть положительным числом")

        return len(errors) == 0, errors

@dataclass
class Product(BaseModel):
    """
    Модель изделия.

    Attributes:
        name: Наименование изделия
        product_number: Номер изделия
    """
    name: str = ""
    product_number: str = ""

    def full_name(self) -> str:
        """
        Возвращает полное наименование изделия.

        Returns:
            str: Полное наименование
        """
        return f"{self.product_number} {self.name}"

@dataclass
class Contract(BaseModel):
    """
    Модель контракта.

    Attributes:
        contract_number: Шифр контракта
        start_date: Дата начала
        end_date: Дата окончания
        description: Описание контракта
    """
    contract_number: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: str = ""

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        success, errors = super().validate()

        # Проверка дат
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("Дата начала не может быть позже даты окончания")

        return len(errors) == 0, errors

    @property
    def duration_days(self) -> int:
        """
        Возвращает длительность контракта в днях.

        Returns:
            int: Длительность контракта в днях
        """
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    @property
    def is_active(self) -> bool:
        """
        Проверяет, активен ли контракт.

        Returns:
            bool: True, если контракт активен
        """
        today = date.today()
        return self.start_date <= today <= self.end_date if self.start_date and self.end_date else False

@dataclass
class WorkCardItem(BaseModel):
    """
    Модель элемента наряда работы.

    Attributes:
        work_card_id: ID наряда
        work_type_id: ID вида работы
        quantity: Количество выполненных работ
        amount: Сумма
    """
    work_card_id: int = 0
    work_type_id: int = 0
    quantity: float = 0.0
    amount: float = 0.0

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        success, errors = super().validate()

        # Проверка количества
        if self.quantity <= 0:
            errors.append("Количество должно быть положительным числом")

        # Проверка суммы
        if self.amount <= 0:
            errors.append("Сумма должна быть положительным числом")

        return len(errors) == 0, errors

@dataclass
class WorkCardWorker(BaseModel):
    """
    Модель работника по наряду.

    Attributes:
        work_card_id: ID наряда
        worker_id: ID работника
        amount: Сумма для работника
    """
    work_card_id: int = 0
    worker_id: int = 0
    amount: float = 0.0

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        success, errors = super().validate()

        # Проверка суммы
        if self.amount <= 0:
            errors.append("Сумма должна быть положительным числом")

        return len(errors) == 0, errors

@dataclass
class WorkCard(BaseModel):
    """
    Модель наряда работы.

    Attributes:
        card_number: Номер наряда
        card_date: Дата наряда
        product_id: ID изделия
        contract_id: ID контракта
        total_amount: Итоговая сумма
        items: Элементы наряда
        workers: Работники по наряду
    """
    card_number: str = ""
    card_date: date = date.today()
    product_id: int = 0
    contract_id: int = 0
    total_amount: float = 0.0
    items: List[WorkCardItem] = None  # type: ignore
    workers: List[WorkCardWorker] = None  # type: ignore

    def __post_init__(self):
        """Дополнительная инициализация после создания объекта"""
        super().__post_init__()

        # Инициализация списков, если они не заданы
        if self.items is None:
            self.items = []
        if self.workers is None:
            self.workers = []

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность данных.

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        success, errors = super().validate()

        # Проверка даты
        if not self.card_date:
            errors.append("Дата наряда не может быть пустой")

        # Проверка продукта
        if self.product_id <= 0:
            errors.append("Неверный ID изделия")

        # Проверка контракта
        if self.contract_id <= 0:
            errors.append("Неверный ID контракта")

        # Проверка итоговой суммы
        if self.total_amount <= 0:
            errors.append("Итоговая сумма должна быть положительным числом")

        # Проверка элементов
        if not self.items:
            errors.append("Наряд должен содержать хотя бы один элемент")

        # Проверка работников
        if not self.workers:
            errors.append("Наряд должен содержать хотя бы одного работника")

        return len(errors) == 0, errors

    def calculate_worker_amount(self) -> float:
        """
        Рассчитывает сумму для каждого работника.

        Returns:
            float: Сумма для каждого работника
        """
        if not self.total_amount or not self.workers:
            return 0.0
        return self.total_amount / len(self.workers)