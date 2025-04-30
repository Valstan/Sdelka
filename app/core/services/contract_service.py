"""
File: app/core/services/contract_service.py
Сервис для управления контрактами.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
from app.core.services.base_service import BaseService
from app.core.models.contract import Contract
from app.core.models.base_model import BaseModel


class ContractService(BaseService):
    """
    Сервис для управления контрактами.
    """

    def model_class(self) -> type:
        return Contract

    @property
    def table_name(self) -> str:
        return "contracts"

    def create(self, model: Contract) -> Tuple[bool, Optional[int]]:
        """
        Создает новый контракт.

        Args:
            model: Экземпляр модели Contract

        Returns:
            Кортеж (успех, ID новой записи)
        """
        query = """
            INSERT INTO contracts 
            (contract_number, start_date, end_date, description)
            VALUES (?, ?, ?, ?)
        """

        params = (
            model.contract_number,
            model.start_date.isoformat() if model.start_date else None,
            model.end_date.isoformat() if model.end_date else None,
            model.description
        )

        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                model.id = cursor.lastrowid
                return True, model.id
        except Exception as e:
            logger.error(f"Ошибка создания контракта: {e}", exc_info=True)
            return False, None

    def update(self, model: Contract) -> Tuple[bool, Optional[str]]:
        """
        Обновляет информацию о контракте.

        Args:
            model: Экземпляр модели Contract

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """
            UPDATE contracts SET
            contract_number = ?,
            start_date = ?,
            end_date = ?,
            description = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            model.contract_number,
            model.start_date.isoformat() if model.start_date else None,
            model.end_date.isoformat() if model.end_date else None,
            model.description,
            model.id
        )

        try:
            with self.db_manager.connect() as conn:
                conn.execute(query, params)
                return True, None
        except Exception as e:
            logger.error(f"Ошибка обновления контракта: {e}", exc_info=True)
            return False, str(e)

    def find_by_number(self, number: str) -> List[Contract]:
        """
        Поиск контрактов по номеру.

        Args:
            number: Часть номера контракта

        Returns:
            Список подходящих контрактов
        """
        return self.search({"contract_number": number})

    def get_active_contracts(self) -> List[Contract]:
        """
        Получает список активных контрактов.

        Returns:
            Список активных контрактов
        """
        query = """
            SELECT * FROM contracts 
            WHERE start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE
            ORDER BY start_date DESC
        """
        rows = self._execute_query(query)
        return [self._map_to_model(row) for row in rows]

    def exists(self, number: str, contract_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже контракт с таким номером.

        Args:
            number: Номер контракта
            contract_id: ID текущего контракта (если редактируем)

        Returns:
            True если существует, иначе False
        """
        query = """
            SELECT COUNT(*) FROM contracts 
            WHERE contract_number LIKE ? AND (? IS NULL OR id != ?)
        """
        result = self._execute_query(query, (number, contract_id, contract_id), fetch_one=True)
        return result[0] > 0