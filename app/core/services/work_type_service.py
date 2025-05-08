# app/core/services/work_type_service.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import date

from app.core.models.base_model import WorkType
from app.core.database.repositories.work_type_repository import WorkTypeRepository
from app.core.services.base_service import BaseService

class WorkTypeService(BaseService):
    """
    Сервис для работы с видами работ.
    """
    
    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис видов работ.
        
        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkTypeRepository(db_manager))
        
    def get_current_price(self, work_type_id: int, date_: date) -> Optional[float]:
        """
        Получает цену вида работы на определенную дату.
        
        Args:
            work_type_id: ID вида работы
            date_: Дата
            
        Returns:
            Optional[float]: Цена или None
        """
        return self.repository.get_current_price(work_type_id, date_)
        
    def get_all_active(self, date_: date) -> List[WorkType]:
        """
        Получает все активные виды работ на определенную дату.
        
        Args:
            date_: Дата
            
        Returns:
            List[WorkType]: Список активных видов работ
        """
        return self.repository.get_all_active(date_)