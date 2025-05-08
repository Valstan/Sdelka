# app/core/database/repositories/work_card_repository.py
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict
from datetime import date

from app.core.models.base_model import WorkCard, WorkCardItem, WorkCardWorker
from app.core.database.repositories.base_repository import BaseRepository


class WorkCardItemRepository(BaseRepository):
    """
    Репозиторий для работы с элементами нарядов.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий элементов нарядов.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkCardItem, "work_card_items")

    def get_by_work_card(self, work_card_id: int) -> List[WorkCardItem]:
        """
        Получает элементы наряда по ID наряда.

        Args:
            work_card_id: ID наряда

        Returns:
            List[WorkCardItem]: Список элементов наряда
        """
        try:
            query = "SELECT * FROM work_card_items WHERE work_card_id = ?"
            results = self.db_manager.execute_query(query, (work_card_id,))

            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            self.logger.error(f"Ошибка получения элементов наряда: {e}", exc_info=True)
            return []


class WorkCardWorkerRepository(BaseRepository):
    """
    Репозиторий для работы с работниками по нарядам.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий работников по нарядам.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkCardWorker, "work_card_workers")

    def get_by_work_card(self, work_card_id: int) -> List[WorkCardWorker]:
        """
        Получает работников по наряду по ID наряда.

        Args:
            work_card_id: ID наряда

        Returns:
            List[WorkCardWorker]: Список работников по наряду
        """
        try:
            query = "SELECT * FROM work_card_workers WHERE work_card_id = ?"
            results = self.db_manager.execute_query(query, (work_card_id,))

            return [self._create_model_from_db(row) for row in results]

        except Exception as e:
            self.logger.error(f"Ошибка получения работников по наряду: {e}", exc_info=True)
            return []


class WorkCardRepository(BaseRepository):
    """
    Репозиторий для работы с нарядами.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует репозиторий нарядов.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkCard, "work_cards")

        # Инициализируем связанные репозитории
        self.items_repo = WorkCardItemRepository(db_manager)
        self.workers_repo = WorkCardWorkerRepository(db_manager)

    def get_with_details(self, work_card_id: int) -> Optional[WorkCard]:
        """
        Получает наряд с деталями (элементы и работники).

        Args:
            work_card_id: ID наряда

        Returns:
            Optional[WorkCard]: Наряд с деталями или None
        """
        try:
            # Получаем основную информацию о наряде
            work_card = super().get_by_id(work_card_id)
            if not work_card:
                return None

            # Получаем элементы наряда
            work_card.items = self.items_repo.get_by_work_card(work_card_id)

            # Получаем работников по наряду
            work_card.workers = self.workers_repo.get_by_work_card(work_card_id)

            return work_card

        except Exception as e:
            self.logger.error(f"Ошибка получения наряда с деталями: {e}", exc_info=True)
            return None

    def create_with_details(self, work_card: WorkCard) -> Tuple[bool, Optional[int]]:
        """
        Создает наряд с деталями (элементы и работники).

        Args:
            work_card: Наряд с деталями

        Returns:
            Tuple[bool, Optional[int]]: (успех, ID новой записи)
        """
        try:
            # Начинаем транзакцию
            self.db_manager.begin_transaction()

            # Создаем основной наряд
            success, work_card_id = super().create(work_card)
            if not success or work_card_id is None:
                self.db_manager.rollback_transaction()
                return False, None

            # Устанавливаем ID наряда для элементов и работников
            for item in work_card.items:
                item.work_card_id = work_card_id

            for worker in work_card.workers:
                worker.work_card_id = work_card_id

            # Создаем элементы наряда
            items_success, items_error = self.items_repo.bulk_create(work_card.items)
            if not items_success:
                self.db_manager.rollback_transaction()
                return False, None

            # Создаем работников по наряду
            workers_success, workers_error = self.workers_repo.bulk_create(work_card.workers)
            if not workers_success:
                self.db_manager.rollback_transaction()
                return False, None

            # Фиксируем транзакцию
            self.db_manager.commit_transaction()

            return True, work_card_id

        except Exception as e:
            self.db_manager.rollback_transaction()
            self.logger.error(f"Ошибка создания наряда с деталями: {e}", exc_info=True)
            return False, None

    def update_with_details(self, work_card: WorkCard) -> Tuple[bool, Optional[str]]:
        """
        Обновляет наряд с деталями (элементы и работники).

        Args:
            work_card: Наряд с деталями

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            if work_card.id is None:
                error_msg = "Невозможно обновить наряд без ID"
                self.logger.error(error_msg)
                return False, error_msg

            # Начинаем транзакцию
            self.db_manager.begin_transaction()

            # Обновляем основной наряд
            success, error = super().update(work_card)
            if not success:
                self.db_manager.rollback_transaction()
                return False, error

            # Обновляем элементы наряда
            # Сначала удаляем старые элементы
            delete_items_query = "DELETE FROM work_card_items WHERE work_card_id = ?"
            self.db_manager.execute_non_query(delete_items_query, (work_card.id,))

            # Устанавливаем ID наряда для новых элементов
            for item in work_card.items:
                item.work_card_id = work_card.id

            # Создаем новые элементы
            items_success, items_error = self.items_repo.bulk_create(work_card.items)
            if not items_success:
                self.db_manager.rollback_transaction()
                return False, items_error

            # Обновляем работников по наряду
            # Сначала удаляем старых работников
            delete_workers_query = "DELETE FROM work_card_workers WHERE work_card_id = ?"
            self.db_manager.execute_non_query(delete_workers_query, (work_card.id,))

            # Устанавливаем ID наряда для новых работников
            for worker in work_card.workers:
                worker.work_card_id = work_card.id

            # Создаем новых работников
            workers_success, workers_error = self.workers_repo.bulk_create(work_card.workers)
            if not workers_success:
                self.db_manager.rollback_transaction()
                return False, workers_error

            # Фиксируем транзакцию
            self.db_manager.commit_transaction()

            return True, None

        except Exception as e:
            self.db_manager.rollback_transaction()
            self.logger.error(f"Ошибка обновления наряда с деталями: {e}", exc_info=True)
            return False, str(e)

    def search_work_cards(self, criteria: Dict[str, Any]) -> List[WorkCard]:
        """
        Выполняет поиск нарядов по критериям.

        Args:
            criteria: Словарь с условиями поиска

        Returns:
            List[WorkCard]: Список подходящих нарядов
        """
        # Добавляем префикс к полям для поиска
        prefixed_criteria = {}
        for field, value in criteria.items():
            if value is not None:
                prefixed_criteria[f"work_cards.{field}"] = value

        return super().search(prefixed_criteria)