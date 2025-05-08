# app/utils/validators.py
from datetime import date
from typing import Any, Dict, List, Tuple, Union, Optional
from decimal import Decimal

def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, Optional[str]]:
    """
    Проверяет диапазон дат.
    
    Args:
        start_date: Дата начала
        end_date: Дата окончания
        
    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    if start_date > end_date:
        return False, "Дата начала не может быть позже даты окончания"
    return True, None

def validate_positive_number(value: Union[int, float, Decimal], field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что число положительное.
    
    Args:
        value: Число для проверки
        field_name: Название поля
        
    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    if value <= 0:
        return False, f"{field_name} должно быть положительным числом"
    return True, None

def validate_not_empty(value: Any, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что значение не пустое.
    
    Args:
        value: Значение для проверки
        field_name: Название поля
        
    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    if value is None or value == "":
        return False, f"{field_name} не может быть пустым"
    return True, None

def validate_worker_card(card: Dict[str, Any]) -> List[Tuple[bool, Optional[str]]]:
    """
    Проверяет данные наряда.
    
    Args:
        card: Данные наряда
        
    Returns:
        List[Tuple[bool, Optional[str]]]: Список результатов валидации
    """
    results = []
    
    # Проверка даты
    if card.get("card_date"):
        results.append(validate_date_range(card["card_date"], date.today()))
    
    # Проверка количества работников
    if "workers" in card and len(card["workers"]) == 0:
        results.append((False, "Наряд должен содержать хотя бы одного работника"))
    
    # Проверка количества работ
    if "items" in card and len(card["items"]) == 0:
        results.append((False, "Наряд должен содержать хотя бы один элемент"))
    
    return results

def validate_unique_contract_number(number: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет уникальность номера контракта.
    
    Args:
        number: Номер контракта
        
    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    # Здесь должна быть реализация проверки уникальности номера в БД
    # Для примера всегда возвращаем успех
    return True, None

def validate_unique_product_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет уникальность названия изделия.
    
    Args:
        name: Название изделия
        
    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    # Здесь должна быть реализация проверки уникальности названия в БД
    # Для примера всегда возвращаем успех
    return True, None