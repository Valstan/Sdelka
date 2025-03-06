"""
Сервис для работы с карточками работ.
Содержит бизнес-логику по созданию, редактированию и расчету карточек работ.
"""
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any

from app.db.db_manager import DatabaseManager
from app.db.models import (
    WorkCard, WorkCardItem, WorkCardWorker,
    Worker, WorkType, Product, Contract
)

logger = logging.getLogger(__name__)

class CardService:
    """
    Сервис для работы с карточками работ.
    Обеспечивает бизнес-логику операций с карточками.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def create_new_card(self) -> WorkCard:
        """
        Создание новой пустой карточки работ с автоматическим номером.

        Returns:
            WorkCard: Новая карточка работ
        """
        next_number = self.db.get_next_card_number()
        card = WorkCard(
            card_number=next_number,
            card_date=date.today(),
            total_amount=0.0
        )
        return card

    def save_card(self, card: WorkCard) -> Tuple[bool, Optional[str]]:
        """
        Сохранение карточки работ в базу данных.

        Args:
            card: Карточка работ для сохранения

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            # Обновляем общую сумму перед сохранением
            card.total_amount = card.calculate_total_amount()

            # Распределяем сумму между работниками
            worker_amount = card.calculate_worker_amount()
            for worker in card.workers:
                worker.amount = worker_amount

            # Сохраняем карточку в БД
            if card.id:
                success = self.db.update_work_card(card)
            else:
                card_id = self.db.add_work_card(card)
                success = card_id > 0
                if success:
                    card.id = card_id

            if success:
                return True, None
            else:
                return False, "Не удалось сохранить карточку в базе данных"

        except Exception as e:
            logger.error(f"Ошибка при сохранении карточки: {e}")
            return False, f"Ошибка при сохранении карточки: {str(e)}"

    def delete_card(self, card_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаление карточки работ.

        Args:
            card_id: ID карточки для удаления

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            success = self.db.delete_work_card(card_id)
            if success:
                return True, None
            else:
                return False, "Не удалось удалить карточку"

        except Exception as e:
            logger.error(f"Ошибка при удалении карточки: {e}")
            return False, f"Ошибка при удалении карточки: {str(e)}"

    def get_card(self, card_id: int) -> Optional[WorkCard]:
        """
        Получение карточки работ по ID.

        Args:
            card_id: ID карточки

        Returns:
            Optional[WorkCard]: Карточка работ или None
        """
        return self.db.get_work_card_by_id(card_id)

    def get_all_cards(self) -> List[WorkCard]:
        """
        Получение всех карточек работ.

        Returns:
            List[WorkCard]: Список карточек работ
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
        # Получаем информацию о виде работы
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
        # Получаем информацию о работнике
        worker = self.db.get_worker_by_id(worker_id)
        if not worker:
            raise ValueError(f"Работник с ID {worker_id} не найден")

        # Проверяем, есть ли уже такой работник в карточке
        for card_worker in card.workers:
            if card_worker.worker_id == worker_id:
                return  # Работник уже добавлен

        # Создаем запись о работнике в карточке
        card_worker = WorkCardWorker(
            work_card_id=card.id if card.id else 0,
            worker_id=worker_id,
            amount=0.0,  # Сумма будет рассчитана при сохранении
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

    def calculate_card_totals(self, card: WorkCard) -> None:
        """
        Расчет итоговых сумм для карточки и распределение между работниками.

        Args:
            card: Карточка работ
        """
        # Рассчитываем общую сумму карточки
        card.total_amount = card.calculate_total_amount()

        # Распределяем сумму между работниками
        worker_amount = card.calculate_worker_amount()
        for worker in card.workers:
            worker.amount = worker_amount

class WorkerService:
    """
    Сервис для работы с сотрудниками.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def get_all_workers(self) -> List[Worker]:
        """
        Получение всех работников.

        Returns:
            List[Worker]: Список работников
        """
        return self.db.get_all_workers()

    def search_workers(self, search_text: str) -> List[Worker]:
        """
        Поиск работников по фамилии.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Worker]: Список найденных работников
        """
        return self.db.search_workers(search_text)

    def save_worker(self, worker: Worker) -> Tuple[bool, Optional[str]]:
        """
        Сохранение работника.

        Args:
            worker: Работник для сохранения

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            if worker.id:
                success = self.db.update_worker(worker)
            else:
                worker_id = self.db.add_worker(worker)
                success = worker_id > 0
                if success:
                    worker.id = worker_id

            return success, None if success else "Не удалось сохранить работника"

        except Exception as e:
            logger.error(f"Ошибка при сохранении работника: {e}")
            return False, f"Ошибка при сохранении работника: {str(e)}"

    def delete_worker(self, worker_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаление работника.

        Args:
            worker_id: ID работника для удаления

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            success = self.db.delete_worker(worker_id)
            return success, None if success else "Не удалось удалить работника"

        except Exception as e:
            logger.error(f"Ошибка при удалении работника: {e}")
            return False, f"Ошибка при удалении работника: {str(e)}"

class WorkTypeService:
    """
    Сервис для работы с видами работ.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def get_all_work_types(self) -> List[WorkType]:
        """
        Получение всех видов работ.

        Returns:
            List[WorkType]: Список видов работ
        """
        return self.db.get_all_work_types()

    def search_work_types(self, search_text: str) -> List[WorkType]:
        """
        Поиск видов работ по наименованию.

        Args:
            search_text: Текст для поиска

        Returns:
            List[WorkType]: Список найденных видов работ
        """
        return self.db.search_work_types(search_text)

    def save_work_type(self, work_type: WorkType) -> Tuple[bool, Optional[str]]:
        """
        Сохранение вида работы.

        Args:
            work_type: Вид работы для сохранения

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            if work_type.id:
                success = self.db.update_work_type(work_type)
            else:
                work_type_id = self.db.add_work_type(work_type)
                success = work_type_id > 0
                if success:
                    work_type.id = work_type_id

            return success, None if success else "Не удалось сохранить вид работы"

        except Exception as e:
            logger.error(f"Ошибка при сохранении вида работы: {e}")
            return False, f"Ошибка при сохранении вида работы: {str(e)}"

    def delete_work_type(self, work_type_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаление вида работы.

        Args:
            work_type_id: ID вида работы для удаления

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            success = self.db.delete_work_type(work_type_id)
            return success, None if success else "Не удалось удалить вид работы"

        except Exception as e:
            logger.error(f"Ошибка при удалении вида работы: {e}")
            return False, f"Ошибка при удалении вида работы: {str(e)}"

class ProductService:
    """
    Сервис для работы с изделиями.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def get_all_products(self) -> List[Product]:
        """
        Получение всех изделий.

        Returns:
            List[Product]: Список изделий
        """
        return self.db.get_all_products()

    def search_products(self, search_text: str) -> List[Product]:
        """
        Поиск изделий по номеру или типу.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Product]: Список найденных изделий
        """
        return self.db.search_products(search_text)

    def save_product(self, product: Product) -> Tuple[bool, Optional[str]]:
        """
        Сохранение изделия.

        Args:
            product: Изделие для сохранения

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            if product.id:
                success = self.db.update_product(product)
            else:
                product_id = self.db.add_product(product)
                success = product_id > 0
                if success:
                    product.id = product_id

            return success, None if success else "Не удалось сохранить изделие"

        except Exception as e:
            logger.error(f"Ошибка при сохранении изделия: {e}")
            return False, f"Ошибка при сохранении изделия: {str(e)}"

    def delete_product(self, product_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаление изделия.

        Args:
            product_id: ID изделия для удаления

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            success = self.db.delete_product(product_id)
            return success, None if success else "Не удалось удалить изделие"

        except Exception as e:
            logger.error(f"Ошибка при удалении изделия: {e}")
            return False, f"Ошибка при удалении изделия: {str(e)}"

class ContractService:
    """
    Сервис для работы с контрактами.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def get_all_contracts(self) -> List[Contract]:
        """
        Получение всех контрактов.

        Returns:
            List[Contract]: Список контрактов
        """
        return self.db.get_all_contracts()

    def search_contracts(self, search_text: str) -> List[Contract]:
        """
        Поиск контрактов по номеру.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Contract]: Список найденных контрактов
        """
        return self.db.search_contracts(search_text)

    def save_contract(self, contract: Contract) -> Tuple[bool, Optional[str]]:
        """
        Сохранение контракта.

        Args:
            contract: Контракт для сохранения

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            if contract.id:
                success = self.db.update_contract(contract)
            else:
                contract_id = self.db.add_contract(contract)
                success = contract_id > 0
                if success:
                    contract.id = contract_id

            return success, None if success else "Не удалось сохранить контракт"

        except Exception as e:
            logger.error(f"Ошибка при сохранении контракта: {e}")
            return False, f"Ошибка при сохранении контракта: {str(e)}"

    def delete_contract(self, contract_id: int) -> Tuple[bool, Optional[str]]:
        """
        Удаление контракта.

        Args:
            contract_id: ID контракта для удаления

        Returns:
            Tuple[bool, Optional[str]]: Успех операции и сообщение об ошибке
        """
        try:
            success = self.db.delete_contract(contract_id)
            return success, None if success else "Не удалось удалить контракт"

        except Exception as e:
            logger.error(f"Ошибка при удалении контракта: {e}")
            return False, f"Ошибка при удалении контракта: {str(e)}"