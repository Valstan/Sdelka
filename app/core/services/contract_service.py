# File: app/core/services/contract_service.py

from typing import List, Dict, Any, Optional
from app.core.models.contract import Contract
from app.core.database.repository.contract_repository import ContractRepository
from app.core.database.dao.base_dao import BaseDAO
from logging import getLogger

logger = getLogger(__name__)

class ContractService:
    def __init__(self, dao: BaseDAO):
        self.dao = dao
        self.repository = ContractRepository(dao)
    
    def create_table(self) -> None:
        """Создает таблицу контрактов, если её нет."""
        self.repository.create_table()
    
    def create_contract(self, contract: Contract) -> int:
        """Создает новый контракт."""
        contract.validate()
        return self.repository.create(contract)
    
    def get_all_contracts(self) -> List[Dict[str, Any]]:
        """Получает все контракты."""
        return self.repository.get_all()
    
    def get_contract(self, contract_id: int) -> Optional[Dict[str, Any]]:
        """Получает контракт по ID."""
        return self.repository.get_by_id(contract_id)
    
    def update_contract(self, contract: Contract) -> None:
        """Обновляет контракт."""
        contract.validate()
        self.repository.update(contract)
    
    def delete_contract(self, contract_id: int) -> None:
        """Удаляет контракт."""
        self.repository.delete(contract_id)