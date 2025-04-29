# File: app/services/products_service.py
"""
Сервис для работы с изделиями.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from app.models.product import Product
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ProductsService(BaseService):
    """
    Сервис для работы с изделиями.
    """

    def get_query_file(self, filename: str) -> str:
        """Загружает SQL-запрос из файла."""
        return super().get_query_file(filename)

    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Получает список всех изделий.

        Returns:
            Список изделий в формате словарей
        """
        query = self.get_query_file("products.sql")
        result = self.execute_query(query)

        if result:
            return [dict(row) for row in result]
        return []

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию об изделии по его ID.

        Args:
            product_id: ID изделия

        Returns:
            Информация об изделии в формате словаря или None
        """
        query = self.get_query_file("products.sql")
        result = self.execute_query(query, (product_id,), fetch_one=True)

        return dict(result) if result else None

    def search_products(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Выполняет поиск изделий по названию или номеру.

        Args:
            search_text: Текст для поиска

        Returns:
            Список найденных изделий
        """
        search_pattern = f"%{search_text}%"
        query = self.get_query_file("products.sql")
        result = self.execute_query(query, (search_pattern, search_pattern))

        return [dict(row) for row in result] if result else []

    def add_product(self, product: Product) -> Tuple[bool, Optional[int]]:
        """
        Добавляет новое изделие в базу данных.

        Args:
            product: Объект Product с данными для добавления

        Returns:
            Кортеж (успех, ID добавленного изделия)
        """
        query = self.get_query_file("products.sql")
        params = (
            product.name,
            product.product_number
        )

        return self._save_entity(query, params, "изделие")

    def update_product(self, product: Product) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные существующего изделия.

        Args:
            product: Объект Product с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("products.sql")
        params = (
            product.name,
            product.product_number,
            datetime.now(),
            product.id
        )

        return self._save_entity(query, params, "изделие")

    def delete_product(self, product_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет изделие из базы данных.

        Args:
            product_id: ID изделия для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("products.sql")
        return self._delete_entity(query, (product_id,), "изделие")

    def check_number_exists(self, product_number: str, product_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже изделие с таким номером.

        Args:
            product_number: Номер изделия
            product_id: ID текущего изделия (если редактируем)

        Returns:
            True, если номер существует в базе данных
        """
        query = self.get_query_file("products.sql")
        result = self.execute_query(query, (product_number, product_id), fetch_one=True)
        return bool(result and result["exists"])