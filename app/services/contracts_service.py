# File: app/services/contracts_service.py
"""
Сервис для работы с контрактами.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging
from app.models.contract import Contract
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ContractsService(BaseService):
    """
    Сервис для работы с контрактами.
    """

    def get_query_file(self, filename: str) -> str:
        """Загружает SQL-запрос из файла."""
        return super().get_query_file(filename)

    def get_all_contracts(self) -> List[Dict[str, Any]]:
        """
        Получает список всех контрактов.

        Returns:
            Список контрактов в формате словарей
        """
        query = self.get_query_file("contracts.sql")
        result = self.execute_query(query)

        if result:
            return [dict(row) for row in result]
        return []

    def get_contract_by_id(self, contract_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о контракте по его ID.

        Args:
            contract_id: ID контракта

        Returns:
            Информация о контракте в формате словаря или None
        """
        query = self.get_query_file("contracts.sql")
        result = self.execute_query(query, (contract_id,), fetch_one=True)

        return dict(result) if result else None

    def search_contracts(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Выполняет поиск контрактов по номеру или описанию.

        Args:
            search_text: Текст для поиска

        Returns:
            Список найденных контрактов
        """
        search_pattern = f"%{search_text}%"
        query = self.get_query_file("contracts.sql")
        result = self.execute_query(query, (search_pattern, search_pattern))

        return [dict(row) for row in result] if result else []

    def add_contract(self, contract: Contract) -> Tuple[bool, Optional[int]]:
        """
        Добавляет новый контракт в базу данных.

        Args:
            contract: Объект Contract с данными для добавления

        Returns:
            Кортеж (успех, ID добавленного контракта)
        """
        query = self.get_query_file("contracts.sql")
        params = (
            contract.contract_number,
            contract.start_date,
            contract.end_date,
            contract.description
        )

        return self._save_entity(query, params, "контракт")

    def update_contract(self, contract: Contract) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные существующего контракта.

        Args:
            contract: Объект Contract с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("contracts.sql")
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
        Удаляет контракт из базы данных.

        Args:
            contract_id: ID контракта для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("contracts.sql")
        return self._delete_entity(query, (contract_id,), "контракт")

    def check_number_exists(self, contract_number: str, contract_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже контракт с таким номером.

        Args:
            contract_number: Номер контракта
            contract_id: ID текущего контракта (если редактируем)

        Returns:
            True, если номер существует в базе данных
        """
        query = self.get_query_file("contracts.sql")
        result = self.execute_query(query, (contract_number, contract_id), fetch_one=True)
        return bool(result and result["exists"])