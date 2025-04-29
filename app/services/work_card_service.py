# File: app/services/work_card_service.py
"""
Сервис для работы с данными карточек работ.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from app.models.models import WorkCard, WorkCardItem, WorkCardWorker
from app.services.base_service import BaseService


class WorkCardService(BaseService):
    """
    Сервис для работы с данными карточек работ.

    Методы:
        get_all_work_cards(): Получает список всех карточек работ
        get_work_card_by_id(card_id): Получает данные карточки по ID
        get_work_card_with_relations(card_id): Получает карточку со связанными данными
        add_work_card(card): Добавляет новую карточку
        update_work_card(card): Обновляет карточку
        delete_work_card(card_id): Удаляет карточку
        add_work_item(card_id, work_type_id, quantity): Добавляет вид работы в карточку
        update_work_item(item): Обновляет элемент карточки
        delete_work_item(item_id): Удаляет элемент карточки
        add_worker(card_id, worker_id, amount): Добавляет работника в карточку
        update_worker(card_id, worker_id, amount): Обновляет данные работника в карточке
        delete_worker(card_id, worker_id): Удаляет работника из карточки
    """

    def get_all_work_cards(self) -> List[WorkCard]:
        """
        Получает список всех карточек работ

        Returns:
            Список объектов WorkCard
        """
        cards_data = self._fetch_all("""
            SELECT wc.*, p.product_number, p.product_type, c.contract_number 
            FROM work_cards wc
            LEFT JOIN products p ON wc.product_id = p.id
            LEFT JOIN contracts c ON wc.contract_id = c.id
            ORDER BY wc.card_date DESC
        """)

        return [self._create_work_card(data) for data in cards_data]

    def get_work_card_by_id(self, card_id: int) -> Optional[WorkCard]:
        """
        Получает данные карточки по ID

        Args:
            card_id: ID карточки

        Returns:
            Объект WorkCard или None если карточка не найдена
        """
        card_data = self._fetch_one("""
            SELECT wc.*, p.product_number, p.product_type, c.contract_number 
            FROM work_cards wc
            LEFT JOIN products p ON wc.product_id = p.id
            LEFT JOIN contracts c ON wc.contract_id = c.id
            WHERE wc.id = ?
        """, (card_id,))

        if not card_data:
            return None

        card = self._create_work_card(card_data)

        # Загружаем элементы карточки
        items_data = self._fetch_all("SELECT * FROM work_card_items WHERE work_card_id = ?", (card_id,))
        card.items = [WorkCardItem(**item) for item in items_data]

        # Загружаем работников карточки
        workers_data = self._fetch_all("SELECT * FROM work_card_workers WHERE work_card_id = ?", (card_id,))
        card.workers = [WorkCardWorker(**worker) for worker in workers_data]

        return card

    def _create_work_card(self, data: dict) -> WorkCard:
        """Создает объект WorkCard из словаря данных"""
        return WorkCard(
            id=data.get("id"),
            card_number=int(data.get("card_number")),
            card_date=datetime.strptime(data.get("card_date"), "%Y-%m-%d").date() if isinstance(data.get("card_date"),
                                                                                                str) else data.get(
                "card_date"),
            product_id=data.get("product_id"),
            contract_id=data.get("contract_id"),
            total_amount=float(data.get("total_amount")) if data.get("total_amount") is not None else 0.0,
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None,
            product=Product(
                id=data.get("product_id"),
                product_number=data.get("product_number"),
                product_type=data.get("product_type")
            ) if data.get("product_number") or data.get("product_type") else None,
            contract=Contract(
                id=data.get("contract_id"),
                contract_number=data.get("contract_number")
            ) if data.get("contract_number") else None
        )

    def add_work_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """
        Добавляет новую карточку

        Args:
            card: Объект WorkCard с данными для добавления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """INSERT INTO work_cards 
                  (card_number, card_date, product_id, contract_id, total_amount) 
                  VALUES (?, ?, ?, ?, ?)"""
        params = (
            card.card_number,
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount
        )
        success, message = self._save_entity(query, params, "карточка работы")

        if success:
            # Получаем ID последней вставленной записи
            cursor = self._execute_query("SELECT last_insert_rowid()")
            if cursor:
                result = cursor.fetchone()
                if result:
                    card.id = result[0]

        return success, message

    def update_work_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """
        Обновляет карточку

        Args:
            card: Объект WorkCard с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """UPDATE work_cards SET
                    card_date = ?, product_id = ?, contract_id = ?, total_amount = ?,
                    updated_at = ?
                  WHERE id = ?"""
        params = (
            card.card_date,
            card.product_id,
            card.contract_id,
            card.total_amount,
            datetime.now(),
            card.id
        )
        return self._save_entity(query, params, "карточка работы")

    def delete_work_card(self, card_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет карточку

        Args:
            card_id: ID карточки для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        # Удаляем сначала связанные данные
        self._execute_query("DELETE FROM work_card_items WHERE work_card_id = ?", (card_id,))
        self._execute_query("DELETE FROM work_card_workers WHERE work_card_id = ?", (card_id,))

        return self._delete_entity("DELETE FROM work_cards WHERE id = ?", (card_id,), "карточка работы")

    def add_work_item(self, card_id: int, work_type_id: int, quantity: float) -> Tuple[bool, Optional[str]]:
        """
        Добавляет вид работы в карточку

        Args:
            card_id: ID карточки
            work_type_id: ID вида работы
            quantity: Количество выполненных работ

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        # Получаем цену вида работы
        work_type_data = self._fetch_one("SELECT name, price FROM work_types WHERE id = ?", (work_type_id,))
        if not work_type_data:
            return False, "Не найден вид работы"

        amount = quantity * work_type_data["price"]

        query = "INSERT INTO work_card_items (work_card_id, work_type_id, quantity, amount) VALUES (?, ?, ?, ?)"
        params = (
            card_id,
            work_type_id,
            quantity,
            amount
        )

        return self._save_entity(query, params, "элемент карточки")

    def update_work_item(self, item: WorkCardItem) -> Tuple[bool, Optional[str]]:
        """
        Обновляет элемент карточки

        Args:
            item: Объект WorkCardItem с обновленными данными

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        # Получаем цену вида работы
        work_type_data = self._fetch_one("SELECT price FROM work_types WHERE id = ?", (item.work_type_id,))
        if not work_type_data:
            return False, "Не найден вид работы"

        item.amount = item.quantity * work_type_data["price"]

        query = """UPDATE work_card_items SET
                    work_type_id = ?, quantity = ?, amount = ?,
                    updated_at = ?
                  WHERE id = ?"""
        params = (
            item.work_type_id,
            item.quantity,
            item.amount,
            datetime.now(),
            item.id
        )

        return self._save_entity(query, params, "элемент карточки")

    def delete_work_item(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет элемент карточки

        Args:
            item_id: ID элемента для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        return self._delete_entity("DELETE FROM work_card_items WHERE id = ?", (item_id,), "элемент карточки")

    def add_worker(self, card_id: int, worker_id: int, amount: float = 0.0) -> Tuple[bool, Optional[str]]:
        """
        Добавляет работника в карточку

        Args:
            card_id: ID карточки
            worker_id: ID работника
            amount: Сумма для работника (по умолчанию 0)

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = "INSERT INTO work_card_workers (work_card_id, worker_id, amount) VALUES (?, ?, ?)"
        params = (
            card_id,
            worker_id,
            amount
        )

        return self._save_entity(query, params, "работник карточки")

    def update_worker(self, card_id: int, worker_id: int, amount: float) -> Tuple[bool, Optional[str]]:
        """
        Обновляет данные работника в карточке

        Args:
            card_id: ID карточки
            worker_id: ID работника
            amount: Новая сумма для работника

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        query = """UPDATE work_card_workers SET
                    amount = ?,
                    updated_at = ?
                  WHERE work_card_id = ? AND worker_id = ?"""
        params = (
            amount,
            datetime.now(),
            card_id,
            worker_id
        )

        return self._save_entity(query, params, "работник карточки")

    def delete_worker(self, card_id: int, worker_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаляет работника из карточки

        Args:
            card_id: ID карточки
            worker_id: ID работника для удаления

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        return self._delete_entity(
            "DELETE FROM work_card_workers WHERE work_card_id = ? AND worker_id = ?",
            (card_id, worker_id),
            "работник карточки"
        )