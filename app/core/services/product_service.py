# app/core/services/product_service.py
from typing import Any, Optional

from app.core.models.base import Product
from app.core.repositories.product_repository import ProductRepository
from app.core.services.base_service import BaseService

class ProductService(BaseService):
    """
    Сервис для работы с изделиями.
    """
    
    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис изделий.
        
        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, ProductRepository(db_manager))
        
    def get_by_number(self, product_number: str) -> Optional[Product]:
        """
        Получает изделие по номеру.
        
        Args:
            product_number: Номер изделия
            
        Returns:
            Optional[Product]: Изделие или None
        """
        return self.repository.get_by_number(product_number)