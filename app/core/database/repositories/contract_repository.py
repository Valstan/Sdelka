# app/core/database/repositories/contract_repository.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import date

from app.core.models.base_model import Contract
from app.core.database.repositories.base_repository import BaseRepository


class ContractRepository(BaseRepository):
    """
    Репозиторий для работы с контрактами.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий контрактов.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, Contract, "contracts")

    def get_active_contracts(self, date_: Optional[date] = None) -> List[Contract]:
        """
        Получает активные контракты на определенную дату.

        Args:
            date_: Дата (по умолчанию - текущая дата)

        Returns:
            List[Contract]: Список активных контрактов
        """
        try:
            if date_ is None:
                date_ = date.today()

            query = """
                SELECT * 
                FROM contracts 
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY start_date DESC
            """
            results = self.db_manager.execute_query(query, (date_.isoformat(), date_.isoformat()))

            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            self.logger.error(f"Ошибка получения активных контрактов: {e}", exc_info=True)
            return []

    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        """
        Получает контракт по шифру.

        Args:
            contract_number: Шифр контракта

        Returns:
            Optional[Contract]: Контракт или None
        """
        try:
            query = "SELECT * FROM contracts WHERE contract_number = ?"
            result = self.db_manager.execute_query_fetch_one(query, (contract_number,))

            if result:
                return self._create_model_from_db(result)
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения контракта по шифру: {e}", exc_info=True)
            return None