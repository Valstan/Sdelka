# app/core/services/worker_service.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from app.core.models.base_model import Worker
from app.core.database.repositories.worker_repository import WorkerRepository
from app.core.services.base_service import BaseService

class WorkerService(BaseService):
    """
    Сервис для работы с работниками.
    """
    
    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис работников.
        
        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkerRepository(db_manager))
        
    def get_by_employee_number(self, employee_number: str) -> Optional[Worker]:
        """
        Получает работника по табельному номеру.
        
        Args:
            employee_number: Табельный номер
            
        Returns:
            Optional[Worker]: Работник или None
        """
        return self.repository.get_by_employee_number(employee_number)