# app/core/services/work_card_service.py
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import date

from jsonschema.exceptions import ValidationError

from app.core.models.base_model import WorkCard
from app.core.database.repositories.work_card_repository import WorkCardRepository
from app.core.services.base_service import BaseService
from app.core.services.worker_service import WorkerService
from app.core.services.work_type_service import WorkTypeService
from app.core.services.product_service import ProductService
from app.core.services.contract_service import ContractService


class WorkCardService(BaseService):
    """
    Сервис для работы с нарядами.
    """

    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис нарядов.

        Args:
            db_manager: Менеджер базы данных
        """
        super().__init__(db_manager, WorkCardRepository(db_manager))

        # Инициализируем связанные сервисы
        self.worker_service = WorkerService(db_manager)
        self.work_type_service = WorkTypeService(db_manager)
        self.product_service = ProductService(db_manager)
        self.contract_service = ContractService(db_manager)

    def get_with_details(self, work_card_id: int) -> Optional[WorkCard]:
        """
        Получает наряд с деталями (элементы и работники).

        Args:
            work_card_id: ID наряда

        Returns:
            Optional[WorkCard]: Наряд с деталями или None
        """
        return self.repository.get_with_details(work_card_id)

    def create_with_details(self, work_card: WorkCard) -> WorkCard:
        """
        Создает наряд с деталями (элементы и работники).

        Args:
            work_card: Наряд с деталями

        Returns:
            WorkCard: Созданный наряд
        """
        try:
            # Валидация данных
            is_valid, errors = work_card.validate()
            if not is_valid:
                raise ValidationError(f"Ошибка валидации при создании наряда: {errors}")

            # Валидация элементов
            for item in work_card.items:
                is_valid, errors = item.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации элемента наряда: {errors}")

            # Валидация работников
            for worker in work_card.workers:
                is_valid, errors = worker.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации работника по наряду: {errors}")

            # Проверка существования связанных сущностей
            if not self.product_service.exists(work_card.product_id):
                raise NotFoundError(f"Изделие с ID {work_card.product_id} не найдено")

            if not self.contract_service.exists(work_card.contract_id):
                raise NotFoundError(f"Контракт с ID {work_card.contract_id} не найден")

            for item in work_card.items:
                if not self.work_type_service.exists(item.work_type_id):
                    raise NotFoundError(f"Вид работы с ID {item.work_type_id} не найден")

            for worker in work_card.workers:
                if not self.worker_service.exists(worker.worker_id):
                    raise NotFoundError(f"Работник с ID {worker.worker_id} не найден")

            # Создание в БД
            success, work_card_id = self.repository.create_with_details(work_card)
            if not success or work_card_id is None:
                raise DatabaseError("Ошибка создания наряда с деталями")

            # Получаем созданный наряд
            created_card = self.repository.get_with_details(work_card_id)
            if not created_card:
                raise DatabaseError("Не удалось получить созданный наряд")

            return created_card

        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка создания наряда с деталями: {e}", exc_info=True)
            raise DatabaseError("Ошибка создания наряда с деталями") from e

    def update_with_details(self, work_card: WorkCard) -> WorkCard:
        """
        Обновляет наряд с деталями (элементы и работники).

        Args:
            work_card: Наряд с деталями

        Returns:
            WorkCard: Обновленный наряд
        """
        try:
            # Проверка наличия ID
            if work_card.id is None:
                raise ValidationError("Невозможно обновить наряд без ID")

            # Валидация данных
            is_valid, errors = work_card.validate()
            if not is_valid:
                raise ValidationError(f"Ошибка валидации при обновлении наряда: {errors}")

            # Валидация элементов
            for item in work_card.items:
                is_valid, errors = item.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации элемента наряда: {errors}")

            # Валидация работников
            for worker in work_card.workers:
                is_valid, errors = worker.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации работника по наряду: {errors}")

            # Проверка существования
            if not self.repository.exists(work_card.id):
                raise NotFoundError(f"Наряд с ID {work_card.id} не найден")

            # Проверка существования связанных сущностей
            if not self.product_service.exists(work_card.product_id):
                raise NotFoundError(f"Изделие с ID {work_card.product_id} не найдено")

            if not self.contract_service.exists(work_card.contract_id):
                raise NotFoundError(f"Контракт с ID {work_card.contract_id} не найден")

            for item in work_card.items:
                if not self.work_type_service.exists(item.work_type_id):
                    raise NotFoundError(f"Вид работы с ID {item.work_type_id} не найден")

            for worker in work_card.workers:
                if not self.worker_service.exists(worker.worker_id):
                    raise NotFoundError(f"Работник с ID {worker.worker_id} не найден")

            # Обновление в БД
            success, error = self.repository.update_with_details(work_card)
            if not success:
                raise DatabaseError(f"Ошибка обновления наряда с деталями: {error}")

            # Получаем обновленный наряд
            updated_card = self.repository.get_with_details(work_card.id)
            if not updated_card:
                raise DatabaseError("Не удалось получить обновленный наряд")

            return updated_card

        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления наряда с деталями: {e}", exc_info=True)
            raise DatabaseError("Ошибка обновления наряда с деталями") from e