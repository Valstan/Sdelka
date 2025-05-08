# app/core/database/repositories/worker_repository.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from app.core.models.base_model import Worker
from app.core.database.repositories.base_repository import BaseRepository


class WorkerRepository(BaseRepository):
    """
    Репозиторий для работы с работниками.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий работников.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, Worker, "workers")

    def get_by_employee_number(self, employee_number: str) -> Optional[Worker]:
        """
        Получает работника по табельному номеру.

        Args:
            employee_number: Табельный номер

        Returns:
            Optional[Worker]: Работник или None
        """
        try:
            query = "SELECT * FROM workers WHERE employee_number = ?"
            result = self.db_manager.execute_query_fetch_one(query, (employee_number,))

            if result:
                return self._create_model_from_db(result)
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения работника по табельному номеру: {e}", exc_info=True)
            return None

    def search_workers(self, criteria: Dict[str, Any]) -> List[Worker]:
        """
        Выполняет поиск работников по критериям.

        Args:
            criteria: Словарь с условиями поиска

        Returns:
            List[Worker]: Список подходящих работников
        """
        # Добавляем префикс к полям для поиска
        prefixed_criteria = {}
        for field, value in criteria.items():
            if value is not None:
                prefixed_criteria[f"workers.{field}"] = value

        return super().search(prefixed_criteria)