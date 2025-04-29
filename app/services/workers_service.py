# File: app/services/workers_service.py
"""
Сервис для работы с работниками предприятия.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from app.services.base_service import BaseService
from app.models.worker import Worker

logger = logging.getLogger(__name__)


@dataclass
class WorkerService(BaseService):
    """
    Сервис для работы с работниками предприятия.
    """

    def get_query_file(self, filename: str) -> str:
        """Загружает SQL-запрос из файла."""
        return super().get_query_file(filename)

    def get_all_workers(self) -> List[Dict[str, Any]]:
        """
        Получает список всех работников.

        Returns:
            Список работников в формате словарей
        """
        query = self.get_query_file("workers.sql")
        result = self.execute_query(query)

        if result:
            return [dict(row) for row in result]
        return []

    def get_worker_by_id(self, worker_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о работнике по его ID.

        Args:
            worker_id: ID работника

        Returns:
            Информация о работнике в формате словаря или None
        """
        query = self.get_query_file("workers.sql")
        result = self.execute_query(query, (worker_id,), fetch_one=True)

        return dict(result) if result else None

    def search_workers(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Выполняет поиск работников по ФИО.

        Args:
            search_text: Текст для поиска

        Returns:
            Список найденных работников
        """
        search_pattern = f"%{search_text}%"
        query = self.get_query_file("workers.sql")
        result = self.execute_query(query, (search_pattern, search_pattern, search_pattern))

        return [dict(row) for row in result] if result else []

    def add_worker(self, worker: Worker) -> Tuple[bool, Optional[int]]:
        """
        Добавляет нового работника в базу данных.

        Args:
            worker: Объект Worker с данными для добавления

        Returns:
            Кортеж (успех, ID добавленного работника)
        """
        query = self.get_query_file("workers.sql")
        params = (
            worker.last_name,
            worker.first_name,
            worker.middle_name,
            worker.workshop_number,
            worker.position,
            worker.employee_id
        )

        return self._save_entity(query, params, "работник")

    def update_worker(self, worker: Worker) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные существующего работника.

        Args:
            worker: Объект Worker с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("workers.sql")
        params = (
            worker.last_name,
            worker.first_name,
            worker.middle_name,
            worker.workshop_number,
            worker.position,
            datetime.now(),
            worker.id
        )

        return self._save_entity(query, params, "работник")

    def delete_worker(self, worker_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет работника из базы данных.

        Args:
            worker_id: ID работника для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("workers.sql")
        return self._delete_entity(query, (worker_id,), "работник")

    def check_employee_id_exists(self, employee_id: int, worker_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже сотрудник с таким табельным номером.

        Args:
            employee_id: Табельный номер
            worker_id: ID текущего работника (если редактируем)

        Returns:
            True, если номер существует в базе данных
        """
        query = self.get_query_file("workers.sql")
        result = self.execute_query(query, (employee_id, worker_id), fetch_one=True)
        return bool(result and result["exists"])