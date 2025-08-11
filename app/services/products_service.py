from __future__ import annotations

from app.db.models import Product
from app.services.common import BaseService


class ProductsService(BaseService):
    def create_product(self, name: str, sku: str | None = None, description: str | None = None) -> int:
        product = Product(id=None, name=name.strip(), sku=sku.strip() if sku else None, description=description)
        return self.repository.add_product(product)

    def list_products(self) -> list[dict]:
        return self.repository.list_products()