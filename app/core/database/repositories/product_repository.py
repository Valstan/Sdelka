# app/core/database/repositories/product_repository.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from app.core.models.base_model import Product
from app.core.database.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    """
    Репозиторий для работы с изделиями.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий изделий.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, Product, "products")

    def get_by_number(self, product_number: str) -> Optional[Product]:
        """
        Получает изделие по номеру.

        Args:
            product_number: Номер изделия

        Returns:
            Optional[Product]: Изделие или None
        """
        try:
            query = "SELECT * FROM products WHERE product_number = ?"
            result = self.db_manager.execute_query_fetch_one(query, (product_number,))

            if result:
                return self._create_model_from_db(result)
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения изделия по номеру: {e}", exc_info=True)
            return None

    def search_products(self, criteria: Dict[str, Any]) -> List[Product]:
        """
        Выполняет поиск изделий по критериям.

        Args:
            criteria: Словарь с условиями поиска

        Returns:
            List[Product]: Список подходящих изделий
        """
        # Добавляем префикс к полям для поиска
        prefixed_criteria = {}
        for field, value in criteria.items():
            if value is not None:
                prefixed_criteria[f"products.{field}"] = value

        return super().search(prefixed_criteria)