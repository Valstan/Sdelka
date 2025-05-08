# app/core/database/repositories/work_type_repository.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import date

from app.core.models.base_model import WorkType
from app.core.database.repositories.base_repository import BaseRepository


class WorkTypeRepository(BaseRepository):
    """
    Репозиторий для работы с видами работ.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий видов работ.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkType, "work_types")

    def get_current_price(self, work_type_id: int, date_: date) -> Optional[float]:
        """
        Получает цену вида работы на определенную дату.

        Args:
            work_type_id: ID вида работы
            date_: Дата

        Returns:
            Optional[float]: Цена или None
        """
        try:
            query = """
                SELECT price 
                FROM work_types 
                WHERE id = ? AND valid_from <= ?
                ORDER BY valid_from DESC
                LIMIT 1
            """
            result = self.db_manager.execute_query_fetch_one(query, (work_type_id, date_.isoformat()))

            if result:
                return result["price"]
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения цены вида работы: {e}", exc_info=True)
            return None

    def get_all_active(self, date_: date) -> List[WorkType]:
        """
        Получает все активные виды работ на определенную дату.

        Args:
            date_: Дата

        Returns:
            List[WorkType]: Список активных видов работ
        """
        try:
            query = """
                SELECT wt.* 
                FROM work_types wt
                INNER JOIN (
                    SELECT id, MAX(valid_from) as max_date
                    FROM work_types
                    WHERE valid_from <= ?
                    GROUP BY name
                ) AS latest
                ON wt.id = latest.id
                ORDER BY wt.name
            """
            results = self.db_manager.execute_query(query, (date_.isoformat(),))

            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            self.logger.error(f"Ошибка получения активных видов работ: {e}", exc_info=True)
            return []