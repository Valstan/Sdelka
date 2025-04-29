# File: app/services/work_cards_service.py
"""
Сервис для работы с карточками работ.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging
from app.models.work_card import WorkCard
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class WorkCardsService(BaseService):
    """
    Сервис для работы с карточками работ.
    """

    def get_query_file(self, filename: str) -> str:
        """Загружает SQL-запрос из файла."""
        return super().get_query_file(filename)

    def get_all_work_cards(self) -> List[Dict[str, Any]]:
        """
        Получает список всех карточек работ.

        Returns:
            Список карточек работ в формате словарей
        """
        query = self.get_query_file("work_cards.sql")
        result = self.execute_query(query)

        if result:
            return [dict(row) for row in result]
        return []

    def get_work_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о карточке работы по ее ID.

        Args:
            card_id: ID карточки работы

        Returns:
            Информация о карточке работы в формате словаря или None
        """
        query = self.get_query_file("work_cards.sql")
        result = self.execute_query(query, (card_id,), fetch_one=True)

        return dict(result) if result else None

    def search_work_cards(
            self,
            worker_id: Optional[int] = None,
            work_type_id: Optional[int] = None,
            product_id: Optional[int] = None,
            contract_id: Optional[int] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Выполняет поиск карточек работ по различным критериям.

        Args:
            worker_id: ID работника
            work_type_id: ID вида работы
            product_id: ID изделия
            contract_id: ID контракта
            start_date: Начальная дата
            end_date: Конечная дата

        Returns:
            Список найденных карточек работ
        """
        query = self.get_query_file("work_cards.sql")
        params = {
            "worker_id": worker_id,
            "work_type_id": work_type_id,
            "product_id": product_id,
            "contract_id": contract_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

        result = self.execute_query(query, tuple(params.values()))

        return [dict(row) for row in result] if result else []

    def add_work_card(self, card: WorkCard) -> Tuple[bool, Optional[int]]:
        """
        Добавляет новую карточку работы в базу данных.

        Args:
            card: Объект WorkCard с данными для добавления

        Returns:
            Кортеж (успех, ID добавленной карточки)
        """
        query = self.get_query_file("work_cards.sql")
        params = (
            card.card_number,
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount
        )

        return self._save_entity(query, params, "карточка работы")

    def update_work_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные существующей карточки работы.

        Args:
            card: Объект WorkCard с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("work_cards.sql")
        params = (
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount,
            card.id
        )

        return self._save_entity(query, params, "карточка работы")

    def delete_work_card(self, card_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет карточку работы из базы данных.

        Args:
            card_id: ID карточки работы для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = self.get_query_file("work_cards.sql")
        return self._delete_entity(query, (card_id,), "карточка работы")

    def get_next_card_number(self) -> str:
        """
        Генерирует следующий номер карточки работы.

        Returns:
            Следующий номер карточки
        """
        query = self.get_query_file("work_cards.sql")
        result = self.execute_query(query, fetch_one=True)

        next_number = result["coalesce"] if result and "coalesce" in result else 1
        today = datetime.now()

        return f"{next_number}/{today.strftime('%Y')}"