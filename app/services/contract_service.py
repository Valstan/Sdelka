# File: app/services/contract_service.py
"""
Сервис для работы с данными контрактов.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from app.models.models import Contract
from app.services.base_service import BaseService


class ContractService(BaseService):
    """
    Сервис для работы с данными контрактов.

    Методы:
        get_all_contracts(): Получает список всех контрактов
        get_contract_by_id(contract_id): Получает данные контракта по ID
        search_contracts(query): Ищет контракты по шифру
        add_contract(contract): Добавляет новый контракт
        update_contract(contract): Обновляет данные контракта
        delete_contract(contract_id): Удаляет контракт
    """

    def get_all_contracts(self) -> List[Contract]:
        """
        Получает список всех контрактов

        Returns:
            Список объектов Contract
        """
        contracts_data = self._fetch_all("SELECT * FROM contracts ORDER BY contract_number")
        return [Contract(**data) for data in contracts_data]

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """
        Получает данные контракта по ID

        Args:
            contract_id: ID контракта

        Returns:
            Объект Contract или None если контракт не найден
        """
        contract_data = self._fetch_one("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        return Contract(**contract_data) if contract_data else None

    def search_contracts(self, query: str) -> List[Contract]:
        """
        Ищет контракты по шифру

        Args:
            query: Текст для поиска

        Returns:
            Список подходящих контрактов
        """
        contracts_data = self._fetch_all(
            "SELECT * FROM contracts WHERE contract_number LIKE ? ORDER BY contract_number",
            (f"{query}%",))
        return [Contract(**data) for data in contracts_data]

    def add_contract(self, contract: Contract) -> Tuple[bool, Optional[str]]:
        """
        Добавляет новый контракт

        Args:
            contract: Объект Contract с данными для добавления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = "INSERT INTO contracts (contract_number, start_date, end_date, description) VALUES (?, ?, ?, ?)"
        params = (
            contract.contract_number,
            contract.start_date,
            contract.end_date,
            contract.description
        )
        return self._save_entity(query, params, "контракт")

    def update_contract(self, contract: Contract) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные контракта

        Args:
            contract: Объект Contract с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """UPDATE contracts SET
                    contract_number = ?, start_date = ?, end_date = ?, description = ?,
                    updated_at = ?
                  WHERE id = ?"""
        params = (
            contract.contract_number,
            contract.start_date,
            contract.end_date,
            contract.description,
            datetime.now(),
            contract.id
        )
        return self._save_entity(query, params, "контракт")

    def delete_contract(self, contract_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет контракт

        Args:
            contract_id: ID контракта для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        return self._delete_entity("DELETE FROM contracts WHERE id = ?", (contract_id,), "контракт")