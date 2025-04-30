"""
File: app/core/services/work_type_service.py
Сервис для управления видами работ.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
from app.core.services.base_service import BaseService
from app.core.models.work_type import WorkType
from app.core.models.base_model import BaseModel


class WorkTypeService(BaseService):
    """
    Сервис для управления видами работ.
    """

    def model_class(self) -> type:
        return WorkType

    @property
    def table_name(self) -> str:
        return "work_types"

    def create(self, model: WorkType) -> Tuple[bool, Optional[int]]:
        """
        Создает новый вид работы.

        Args:
            model: Экземпляр модели WorkType

        Returns:
            Кортеж (успех, ID новой записи)
        """
        query = """
            INSERT INTO work_types 
            (name, unit, price, valid_from)
            VALUES (?, ?, ?, ?)
        """

        params = (
            model.name,
            model.unit,
            model.price,
            model.valid_from.isoformat() if model.valid_from else None
        )

        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                model.id = cursor.lastrowid
                return True, model.id
        except Exception as e:
            logger.error(f"Ошибка создания вида работы: {e}", exc_info=True)
            return False, None

    def update(self, model: WorkType) -> Tuple[bool, Optional[str]]:
        """
        Обновляет информацию о виде работы.

        Args:
            model: Экземпляр модели WorkType

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """
            UPDATE work_types SET
            name = ?,
            unit = ?,
            price = ?,
            valid_from = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            model.name,
            model.unit,
            model.price,
            model.valid_from.isoformat() if model.valid_from else None,
            model.id
        )

        try:
            with self.db_manager.connect() as conn:
                conn.execute(query, params)
                return True, None
        except Exception as e:
            logger.error(f"Ошибка обновления вида работы: {e}", exc_info=True)
            return False, str(e)

    def find_by_name(self, name: str) -> List[WorkType]:
        """
        Поиск видов работ по названию.

        Args:
            name: Часть названия вида работы

        Returns:
            Список подходящих видов работы
        """
        return self.search({"name": name})

    def get_by_date(self, work_type_id: int, date_: date) -> Optional[WorkType]:
        """
        Получает актуальную цену вида работы на определенную дату.

        Args:
            work_type_id: ID вида работы
            date_: Дата для проверки

        Returns:
            Экземпляр модели WorkType или None
        """
        query = """
            SELECT * FROM work_types 
            WHERE id = ? AND valid_from <= ?
            ORDER BY valid_from DESC
            LIMIT 1
        """
        row = self._execute_query(query, (work_type_id, date_.isoformat()), fetch_one=True)
        return self._map_to_model(row) if row else None

    def exists(self, name: str, work_type_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже вид работы с таким названием.

        Args:
            name: Название вида работы
            work_type_id: ID текущего вида работы (если редактируем)

        Returns:
            True если существует, иначе False
        """
        query = """
            SELECT COUNT(*) FROM work_types 
            WHERE name LIKE ? AND (? IS NULL OR id != ?)
        """
        result = self._execute_query(query, (name, work_type_id, work_type_id), fetch_one=True)
        return result[0] > 0