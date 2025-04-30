# File: app/core/services/work_card_service.py
"""Сервис для работы с карточками работ."""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging

from app.core.models.work_card import WorkCard
from app.core.services.base_service import BaseService
from app.core.database.connections import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class WorkCardsService(BaseService):
    """Сервис для работы с карточками работ."""

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)

    def get_all_work_cards(self) -> List[WorkCard]:
        """Получает все карточки работ."""
        query = self.get_query_file("work_cards.sql")
        rows = self.execute_query(query)
        return [self._map_to_model(row) for row in rows]

    def get_work_card_by_id(self, card_id: int) -> Optional[WorkCard]:
        """Получает карточку работы по ID."""
        query = self.get_query_file("work_cards.sql")
        params = (card_id,)
        row = self.execute_query(query, params, fetch_one=True)
        return self._map_to_model(row) if row else None

    def get_work_card_by_number(self, number: str) -> Optional[WorkCard]:
        """Получает карточку работы по номеру."""
        query = self.get_query_file("work_cards.sql")
        params = (number,)
        row = self.execute_query(query, params, fetch_one=True)
        return self._map_to_model(row) if row else None

    def save_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """Сохраняет карточку работы (создание или обновление)."""
        try:
            # Обновляем общую сумму перед сохранением
            card.total_amount = card.calculate_total_amount()

            if card.id:
                return self.update_work_card(card)
            else:
                return self.add_work_card(card)

        except Exception as e:
            logger.error(f"Ошибка при сохранении карточки: {e}", exc_info=True)
            return False, f"Ошибка при сохранении карточки: {str(e)}"

    def add_work_card(self, card: WorkCard) -> Tuple[bool, Optional[int]]:
        """Добавляет новую карточку работы в базу данных."""
        query = self.get_query_file("work_cards.sql")
        params = (
            card.card_number,
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount
        )
        result = self._save_entity(query, params, "карточка работы")
        success, message = result
        if success:
            card.id = message
            return True, card.id
        else:
            return False, message

    def update_work_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """Обновляет данные существующей карточки работы."""
        query = self.get_query_file("work_cards.sql")
        params = (
            card.card_number,
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount,
            card.id
        )
        return self._update_entity(query, params, "карточка работы")

    def delete_card(self, card_id: int) -> Tuple[bool, Optional[str]]:
        """Удаляет карточку работ по ID."""
        try:
            with self.db_manager.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM work_cards WHERE id=?", (card_id,))
                conn.execute("DELETE FROM work_card_items WHERE work_card_id=?", (card_id,))
                conn.execute("DELETE FROM work_card_workers WHERE work_card_id=?", (card_id,))
                conn.commit()
                return True, None
        except Exception as e:
            logger.error(f"Ошибка при удалении карточки: {e}", exc_info=True)
            conn.rollback()
            return False, str(e)

    def add_work_item(self, card: WorkCard, work_type_id: int, quantity: int) -> Tuple[bool, Optional[str]]:
        """Добавляет элемент работы в карточку."""
        try:
            # Получаем цену вида работы
            work_type = self.work_types_service.get_work_type_by_id(work_type_id)
            if not work_type:
                raise ValueError("Выбранный вид работы не найден")

            amount = quantity * work_type.price

            query = self.get_query_file("work_card_items.sql")
            params = (card.id, work_type_id, quantity, amount)
            result = self._save_entity(query, params, "элемент карточки")
            success, message = result
            if success:
                # Обновляем сумму для каждого работника
                worker_amount = card.calculate_worker_amount()
                for worker in card.workers:
                    worker.amount = worker_amount
            return result
        except Exception as e:
            logger.error(f"Ошибка при добавлении элемента работы: {e}", exc_info=True)
            return False, str(e)

    def update_work_item(self, card: WorkCard, item_index: int) -> None:
        """Обновляет элемент работы."""
        try:
            item = card.items[item_index]
            query = self.get_query_file("work_card_items.sql")
            params = (item.quantity, item.amount, item.id)
            success, message = self._update_entity(query, params, "элемент карточки")
            if success:
                # Пересчитываем общую сумму и распределяем между работниками
                card.total_amount = card.calculate_total_amount()
                worker_amount = card.calculate_worker_amount()
                for worker in card.workers:
                    worker.amount = worker_amount
            else:
                raise ValueError(message)
        except Exception as e:
            logger.error(f"Ошибка при обновлении элемента работы: {e}", exc_info=True)

    def delete_work_item(self, card: WorkCard, item_index: int) -> Tuple[bool, Optional[str]]:
        """Удаляет элемент работы из карточки."""
        item = card.items[item_index]
        query = self.get_query_file("work_card_items.sql")
        params = (item.id,)
        result = self._delete_entity(query, params, "элемент карточки")
        success, message = result
        if success:
            # Пересчитываем общую сумму и перераспределяем между работниками
            card.total_amount = card.calculate_total_amount()
            worker_amount = card.calculate_worker_amount()
            for worker in card.workers:
                worker.amount = worker_amount
        return result

    def add_worker(self, card: WorkCard, worker_id: int) -> Tuple[bool, Optional[str]]:
        """Добавляет работника в карточку."""
        try:
            # Получаем данные работника
            worker = self.worker_service.get_by_id(worker_id)
            if not worker:
                raise ValueError("Работник не найден")

            # Рассчитываем сумму для работника
            worker_amount = card.calculate_worker_amount()

            query = self.get_query_file("work_card_workers.sql")
            params = (card.id, worker.id, worker_amount)
            result = self._save_entity(query, params, "назначение работника")
            success, message = result
            if success:
                card.workers.append(WorkCardWorker(
                    id=message,
                    work_card_id=card.id,
                    worker_id=worker.id,
                    amount=worker_amount
                ))
                return True, None
            else:
                return False, message
        except Exception as e:
            logger.error(f"Ошибка при добавлении работника: {e}", exc_info=True)
            return False, str(e)

    def update_worker(self, card: WorkCard, worker_index: int) -> Tuple[bool, Optional[str]]:
        """Обновляет данные работника в карточке."""
        worker = card.workers[worker_index]
        query = self.get_query_file("work_card_workers.sql")
        params = (worker.amount, worker.id)
        return self._update_entity(query, params, "назначение работника")

    def delete_worker(self, card: WorkCard, worker_index: int) -> Tuple[bool, Optional[str]]:
        """Удаляет работника из карточки."""
        worker = card.workers[worker_index]
        query = self.get_query_file("work_card_workers.sql")
        params = (worker.id,)
        result = self._delete_entity(query, params, "назначение работника")
        success, message = result
        if success:
            del card.workers[worker_index]
        return result

    def get_all_workers(self, card_id: int) -> List[Dict[str, Any]]:
        """Получает всех работников, участвующих в работе."""
        query = self.get_query_file("work_card_workers.sql")
        params = (card_id,)
        return self.execute_query(query, params)

    def get_all_work_types(self, card_id: int) -> List[Dict[str, Any]]:
        """Получает все виды работ по карточке."""
        query = self.get_query_file("work_card_items.sql")
        params = (card_id,)
        return self.execute_query(query, params)

    def _map_to_model(self, row: Dict[str, Any]) -> WorkCard:
        """Преобразует строку БД в модель WorkCard."""
        return WorkCard(**row)