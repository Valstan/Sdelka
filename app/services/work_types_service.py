# File: app/services/work_types_service.py
"""
Сервис для работы с видами работ.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging
from app.models.work_type import WorkType
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class WorkTypesService(BaseService):
    """
    Сервис для работы с видами работ.
    """

    def get_query_file(self, filename: str) -> str:
        """Загружает SQL-запрос из файла."""
        return super().get_query_file(filename)

    def get_all_work_types(self) -> List[Dict[str, Any]]:
        """
        Получает список всех видов работ.

        Returns:
            Список видов работ в формате словарей
        """
        query = self.get_query_file("work_types.sql")
        result = self.execute_query(query)

        if result:
            return [dict(row) for row in result]
        return []

    def get_work_type_by_id(self, work_type_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о виде работы по его ID.

        Args:
            work_type_id: ID вида работы

        Returns:
            Информация о виде работы в формате словаря или None
        """
        query = self.get_query_file("work_types.sql")
        result = self.execute_query(query, (work_type_id,), fetch_one=True)

        return dict(result) if result else None

    def search_work_types(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Выполняет поиск видов работ по названию.

        Args:
            search_text: Текст для поиска

        Returns:
            Список найденных видов работ
        """
        search_pattern = f"%{search_text}%"
        query = self.get_query_file("work_types.sql")
        result = self.execute_query(query, (search_pattern,))

        return [dict(row) for row in result] if result else []

    def add_work_type(self, work_type: WorkType) -> Tuple[bool, Optional[int]]:
        """
        Добавляет новый вид работы в базу данных.

        Args:
            work_type: Объект WorkType с данными для добавления

        Returns:
            Кортеж (успех, ID добавленного вида работы)
        """
        query = self.get_query_file("work_types.sql")
        params = (
            work_type.name,
            work_type.unit,
            work_type.price,
            work_type.valid_from
        )

        return self._save_entity(query, params, "вид работы")

    def update_work_type(self, work_type: WorkType) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные существующего вида работы.

        Args:
            work_type: Объект WorkType с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("work_types.sql")
        params = (
            work_type.name,
            work_type.unit,
            work_type.price,
            work_type.valid_from,
            datetime.now(),
            work_type.id
        )

        return self._save_entity(query, params, "вид работы")

    def delete_work_type(self, work_type_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет вид работы из базы данных.

        Args:
            work_type_id: ID вида работы для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("work_types.sql")
        return self._delete_entity(query, (work_type_id,), "вид работы")

    def check_name_exists(self, name: str, work_type_id: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли уже вид работы с таким названием.

        Args:
            name: Название вида работы
            work_type_id: ID текущего вида работы (если редактируем)

        Returns:
            True, если название существует в базе данных
        """
        query = self.get_query_file("work_types.sql")
        result = self.execute_query(query, (name, work_type_id), fetch_one=True)
        return bool(result and result["exists"])