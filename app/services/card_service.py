"""
Сервис для работы с карточками работ.
Содержит бизнес-логику операций с карточками.
"""
import logging
from typing import List, Optional, Tuple

from future.backports.datetime import date

from app.models.models import WorkCard, WorkCardItem, WorkCardWorker
from app.base import BaseService

logger = logging.getLogger(__name__)


class CardService(BaseService):
    def __init__(self, db_manager, product_service):
        super().__init__(db_manager)
        self.product_service = product_service

    def create_new_card(self) -> WorkCard:
        """Создание новой пустой карточки работ с автоматическим номером."""
        next_number = self.db.get_next_card_number()
        return WorkCard(
            card_number=next_number,
            card_date=date.today(),
            total_amount=0.0
        )

    def save_card(self, card: WorkCard) -> Tuple[bool, str]:
        """
        Сохранение карточки работ в базе данных.

        Args:
            card: Карточка для сохранения

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            # Обновляем общую сумму перед сохранением
            card.total_amount = card.calculate_total_amount()

            # Распределяем сумму между работниками
            worker_amount = card.calculate_worker_amount()
            for worker in card.workers:
                worker.amount = worker_amount

            if card.id:
                success = self.db.update_work_card(card)
            else:
                card_id = self.db.add_work_card(card)
                success = card_id > 0
                if success:
                    card.id = card_id

            return success, None if success else "Не удалось сохранить карточку"

        except Exception as e:
            logger.error(f"Ошибка при сохранении карточки: {e}")
            return False, f"Ошибка при сохранении карточки: {str(e)}"

    def delete_card(self, card_id: int) -> Tuple[bool, str]:
        """
        Удаление карточки работ.

        Args:
            card_id: ID карточки для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            success = self.db.delete_work_card(card_id)
            return success, None if success else "Не удалось удалить карточку"
        except Exception as e:
            logger.error(f"Ошибка при удалении карточки: {e}")
            return False, f"Ошибка при удалении карточки: {str(e)}"

    def get_card(self, card_id: int) -> Optional[WorkCard]:
        """
        Получение карточки работ по ID.

        Args:
            card_id: ID карточки

        Returns:
            Карточка работ или None
        """
        return self.db.get_work_card_by_id(card_id)

    def get_all_cards(self) -> List[WorkCard]:
        """
        Получение всех карточек работ.

        Returns:
            Список карточек работ
        """
        return self.db.get_all_work_cards()

    def add_work_item(self, card: WorkCard, work_type_id: int, quantity: int) -> None:
        """
        Добавление вида работы в карточку.

        Args:
            card: Карточка работ
            work_type_id: ID вида работы
            quantity: Количество
        """
        work_type = self.db.get_work_type_by_id(work_type_id)
        if not work_type:
            raise ValueError(f"Вид работы с ID {work_type_id} не найден")

        # Проверяем, есть ли уже такой вид работы в карточке
        for item in card.items:
            if item.work_type_id == work_type_id:
                # Обновляем существующий элемент
                item.quantity += quantity
                item.amount = item.quantity * work_type.price
                return

        # Создаем новый элемент
        item = WorkCardItem(
            work_card_id=card.id if card.id else 0,
            work_type_id=work_type_id,
            quantity=quantity,
            amount=quantity * work_type.price,
            work_name=work_type.name,
            price=work_type.price
        )
        card.items.append(item)

    def remove_work_item(self, card: WorkCard, item_index: int) -> None:
        """
        Удаление вида работы из карточки.

        Args:
            card: Карточка работ
            item_index: Индекс элемента в списке
        """
        if 0 <= item_index < len(card.items):
            del card.items[item_index]

    def add_worker(self, card: WorkCard, worker_id: int) -> None:
        """
        Добавление работника в карточку.

        Args:
            card: Карточка работ
            worker_id: ID работника
        """
        worker = self.db.get_worker_by_id(worker_id)
        if not worker:
            raise ValueError(f"Работник с ID {worker_id} не найден")

        # Проверяем, есть ли уже такой работник в карточке
        for card_worker in card.workers:
            if card_worker.worker_id == worker_id:
                return

        # Создаем запись о работнике в карточке
        card_worker = WorkCardWorker(
            work_card_id=card.id if card.id else 0,
            worker_id=worker_id,
            amount=0.0,
            last_name=worker.last_name,
            first_name=worker.first_name,
            middle_name=worker.middle_name
        )
        card.workers.append(card_worker)

    def remove_worker(self, card: WorkCard, worker_index: int) -> None:
        """
        Удаление работника из карточки.

        Args:
            card: Карточка работ
            worker_index: Индекс работника в списке
        """
        if 0 <= worker_index < len(card.workers):
            del card.workers[worker_index]
