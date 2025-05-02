"""
File: app/core/services/worker_service.py
Сервис для работы с работниками.
"""

from typing import List, Optional, Tuple

from app.core.services.base_service import BaseService
from app.core.models.worker import Worker
from app.core.utils.utils import logger


class WorkerService(BaseService):
    """
    Сервис для управления работниками предприятия.
    """

    def model_class(self) -> type:
        return Worker

    @property
    def table_name(self) -> str:
        return "workers"

    def create(self, model: Worker) -> Tuple[bool, Optional[int]]:
        """
        Создает нового работника.

        Args:
            model: Экземпляр модели Worker

        Returns:
            Кортеж (успех, ID новой записи)
        """
        query = """
            INSERT INTO workers 
            (last_name, first_name, middle_name, workshop_number, position, employee_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        params = (
            model.last_name,
            model.first_name,
            model.middle_name,
            model.workshop_number,
            model.position,
            model.employee_id
        )

        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                model.id = cursor.lastrowid
                return True, model.id
        except Exception as e:
            logger.error(f"Ошибка создания работника: {e}", exc_info=True)
            return False, None

    def update(self, model: Worker) -> Tuple[bool, Optional[str]]:
        """
        Обновляет информацию о работнике.

        Args:
            model: Экземпляр модели Worker

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """
            UPDATE workers SET
            last_name = ?,
            first_name = ?,
            middle_name = ?,
            workshop_number = ?,
            position = ?,
            employee_id = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            model.last_name,
            model.first_name,
            model.middle_name,
            model.workshop_number,
            model.position,
            model.employee_id,
            model.id
        )

        try:
            with self.db_manager.connect() as conn:
                conn.execute(query, params)
                return True, None
        except Exception as e:
            logger.error(f"Ошибка обновления работника: {e}", exc_info=True)
            return False, str(e)

    def find_by_name(self, name: str) -> List[Worker]:
        """
        Поиск работников по имени или фамилии.

        Args:
            name: Часть имени или фамилии

        Returns:
            Список подходящих работников
        """
        return self.search({
            "last_name": name,
            "first_name": name
        })

    def get_by_employee_id(self, employee_id: str) -> Optional[Worker]:
        """
        Получает работника по табельному номеру.

        Args:
            employee_id: Табельный номер

        Returns:
            Экземпляр модели Worker или None
        """
        query = "SELECT * FROM workers WHERE employee_id=?"
        row = self._execute_query(query, (employee_id,), fetch_one=True)
        return self._map_to_model(row) if row else None

    def exists(self, employee_id: str) -> bool:
        """
        Проверяет, существует ли уже такой табельный номер.

        Args:
            employee_id: Табельный номер

        Returns:
            True если существует, иначе False
        """
        query = "SELECT COUNT(*) FROM workers WHERE employee_id=?"
        result = self._execute_query(query, (employee_id,), fetch_one=True)
        return result[0] > 0