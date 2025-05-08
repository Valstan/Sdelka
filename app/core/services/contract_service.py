# app/core/services/contract_service.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import date

from app.core.models.base_model import Contract
from app.core.database.repositories.contract_repository import ContractRepository
from app.core.services.base_service import BaseService


class ContractService(BaseService):
    """
    Сервис для работы с контрактами.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис контрактов.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, ContractRepository(db_manager))

    def get_active_contracts(self, date_: Optional[date] = None) -> List[Contract]:
        """
        Получает активные контракты на определенную дату.

        Args:
            date_: Дата (по умолчанию - текущая дата)

        Returns:
            List[Contract]: Список активных контрактов
        """
        return self.repository.get_active_contracts(date_)

    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        """
        Получает контракт по шифру.

        Args:
            contract_number: Шифр контракта

        Returns:
            Optional[Contract]: Контракт или None
        """
        return self.repository.get_by_number(contract_number)