# File: app/core/database/repository/contract_repository.py

from typing import List, Optional, Dict, Any
from app.core.models.contract import Contract
from app.core.database.dao.base_dao import BaseDAO
from app.core.database.queries import ContractQueries
from logging import getLogger

logger = getLogger(__name__)


class ContractRepository:
    def __init__(self, dao: BaseDAO):
        self.dao = dao

    def create_table(self) -> None:
        """Создает таблицу, если её нет."""
        self.dao._execute(ContractQueries.CREATE_TABLE)

    def create(self, contract: Contract) -> int:
        """Создает новый контракт."""
        return self.dao._execute(
            ContractQueries.INSERT,
            (
                contract.contract_number,
                contract.start_date.isoformat(),
                contract.end_date.isoformat(),
                contract.description
            )
        )

    def get_all(self) -> List[Dict[str, Any]]:
        """Получает все контракты."""
        return self.dao._execute(ContractQueries.SELECT_ALL, fetch_all=True)

    def get_by_id(self, contract_id: int) -> Optional[Dict[str, Any]]:
        """Получает контракт по ID."""
        return self.dao._execute(ContractQueries.SELECT_BY_ID, (contract_id,), fetch_one=True)

    def update(self, contract: Contract) -> None:
        """Обновляет контракт."""
        self.dao._execute(
            ContractQueries.UPDATE,
            (
                contract.contract_number,
                contract.start_date.isoformat(),
                contract.end_date.isoformat(),
                contract.description,
                contract.id
            )
        )

    def delete(self, contract_id: int) -> None:
        """Удаляет контракт."""
        self.dao._execute(ContractQueries.DELETE, (contract_id,))