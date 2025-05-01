"""
File: app/core/services/product_service.py
Сервис для управления изделиями.
"""

from typing import List, Optional, Tuple
from app.core.services.base_service import BaseService
from app.core.models.product import Product
from app.utils.utils import logger


class ProductService(BaseService):
    """
    Сервис для управления изделиями.
    """

    def model_class(self) -> type:
        return Product

    @property
    def table_name(self) -> str:
        return "products"

    def create(self, model: Product) -> Tuple[bool, Optional[int]]:
        """
        Создает новое изделие.

        Args:
            model: Экземпляр модели Product

        Returns:
            Кортеж (успех, ID новой записи)
        """
        query = """
            INSERT INTO products 
            (product_code, name)
            VALUES (?, ?)
        """

        params = (
            model.product_code,
            model.name
        )

        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                model.id = cursor.lastrowid
                return True, model.id
        except Exception as e:
            logger.error(f"Ошибка создания изделия: {e}", exc_info=True)
            return False, None

    def update(self, model: Product) -> Tuple[bool, Optional[str]]:
        """
        Обновляет информацию о изделии.

        Args:
            model: Экземпляр модели Product

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """
            UPDATE products SET
            product_code = ?,
            name = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            model.product_code,
            model.name,
            model.id
        )

        try:
            with self.db_manager.connect() as conn:
                conn.execute(query, params)
                return True, None
        except Exception as e:
            logger.error(f"Ошибка обновления изделия: {e}", exc_info=True)
            return False, str(e)

    def find_by_name(self, name: str) -> List[Product]:
        """
        Поиск изделий по названию.

        Args:
            name: Часть названия изделия

        Returns:
            Список подходящих изделий
        """
        return self.search({"name": name})

    def get_by_code(self, code: str) -> Optional[Product]:
        """
        Получает изделие по шифру.

        Args:
            code: Шифр изделия

        Returns:
            Экземпляр модели Product или None
        """
        query = "SELECT * FROM products WHERE product_code=?"
        row = self._execute_query(query, (code,), fetch_one=True)
        return self._map_to_model(row) if row else None

    def exists(self, code: str, product_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже изделие с таким шифром.

        Args:
            code: Шифр изделия
            product_id: ID текущего изделия (если редактируем)

        Returns:
            True если существует, иначе False
        """
        query = """
            SELECT COUNT(*) FROM products 
            WHERE product_code LIKE ? AND (? IS NULL OR id != ?)
        """
        result = self._execute_query(query, (code, product_id, product_id), fetch_one=True)
        return result[0] > 0