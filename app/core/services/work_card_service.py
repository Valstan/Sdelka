"""
Сервис для работы с нарядами
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from dataclasses import asdict
from app.core.models.work_card import WorkCard
from app.core.models.worker import Worker
from app.core.models.work_type import WorkType
from app.core.models.product import Product
from app.core.models.contract import Contract
from app.core.repositories.work_card_repository import WorkCardRepository
from app.core.repositories.worker_repository import WorkerRepository
from app.core.repositories.work_type_repository import WorkTypeRepository
from app.core.repositories.product_repository import ProductRepository
from app.core.repositories.contract_repository import ContractRepository
from app.utils.exceptions import (
    ValidationError,
    DatabaseError,
    NotFoundError
)
from app.utils.validators.common_validators import common_validators


class WorkCardService:
    """
    Сервис для управления нарядами работ
    """

    def __init__(
        self,
        work_card_repository: WorkCardRepository,
        worker_repository: WorkerRepository,
        work_type_repository: WorkTypeRepository,
        product_repository: ProductRepository,
        contract_repository: ContractRepository
    ):
        """
        Инициализация сервиса

        Args:
            work_card_repository: Репозиторий нарядов
            worker_repository: Репозиторий работников
            work_type_repository: Репозиторий видов работ
            product_repository: Репозиторий изделий
            contract_repository: Репозиторий контрактов
        """
        self.work_card_repository = work_card_repository
        self.worker_repository = worker_repository
        self.work_type_repository = work_type_repository
        self.product_repository = product_repository
        self.contract_repository = contract_repository

    def create_work_card(self, data: Dict[str, Any]) -> Tuple[bool, Optional[WorkCard], List[str]]:
        """
        Создает новый наряд

        Args:
            data: Данные для создания наряда

        Returns:
            Tuple[bool, Optional[WorkCard], List[str]]: (успех, наряд, список ошибок)
        """
        try:
            # Валидация входных данных
            is_valid, errors = self._validate_work_card_data(data)
            if not is_valid:
                return False, None, errors

            # Создание наряда
            work_card = WorkCard(**data)

            # Валидация модели
            model_valid, model_errors = work_card.validate()
            if not model_valid:
                return False, None, model_errors

            # Сохранение в БД
            result = self.work_card_repository.create(work_card)
            if not result:
                return False, None, ["Ошибка сохранения наряда в БД"]

            return True, result, []

        except Exception as e:
            return False, None, [f"Неожиданная ошибка: {str(e)}"]

    def update_work_card(self, work_card_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[WorkCard], List[str]]:
        """
        Обновляет существующий наряд

        Args:
            work_card_id: ID наряда для обновления
            data: Новые данные для наряда

        Returns:
            Tuple[bool, Optional[WorkCard], List[str]]: (успех, наряд, список ошибок)
        """
        try:
            # Проверка наличия наряда
            existing_card = self.work_card_repository.get_by_id(work_card_id)
            if not existing_card:
                return False, None, ["Наряд не найден"]

            # Валидация входных данных
            is_valid, errors = self._validate_work_card_data(data)
            if not is_valid:
                return False, None, errors

            # Обновление данных
            for key, value in data.items():
                if hasattr(existing_card, key):
                    setattr(existing_card, key, value)

            # Валидация модели
            model_valid, model_errors = existing_card.validate()
            if not model_valid:
                return False, None, model_errors

            # Обновление в БД
            result = self.work_card_repository.update(existing_card)
            if not result:
                return False, None, ["Ошибка обновления наряда в БД"]

            return True, result, []

        except Exception as e:
            return False, None, [f"Неожиданная ошибка: {str(e)}"]

    def get_work_card(self, work_card_id: int) -> Tuple[bool, Optional[WorkCard], List[str]]:
        """
        Получает наряд по ID

        Args:
            work_card_id: ID наряда

        Returns:
            Tuple[bool, Optional[WorkCard], List[str]]: (успех, наряд, список ошибок)
        """
        try:
            work_card = self.work_card_repository.get_by_id(work_card_id)
            if not work_card:
                return False, None, ["Наряд не найден"]
            return True, work_card, []
        except Exception as e:
            return False, None, [f"Ошибка получения наряда: {str(e)}"]

    def delete_work_card(self, work_card_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет наряд

        Args:
            work_card_id: ID наряда для удаления

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        try:
            # Проверка наличия наряда
            if not self.work_card_repository.exists(work_card_id):
                return False, ["Наряд не найден"]

            # Удаление из БД
            result = self.work_card_repository.delete(work_card_id)
            if not result:
                return False, ["Ошибка удаления наряда из БД"]

            return True, []

        except Exception as e:
            return False, [f"Неожиданная ошибка: {str(e)}"]

    def add_work_item(
        self,
        work_card_id: int,
        work_type_id: int,
        quantity: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Добавляет элемент в наряд

        Args:
            work_card_id: ID наряда
            work_type_id: ID вида работы
            quantity: Количество

        Returns:
            Tuple[bool, Optional[Dict[str, Any]], List[str]]: (успех, элемент наряда, список ошибок)
        """
        try:
            # Проверка наличия наряда
            work_card = self.work_card_repository.get_by_id(work_card_id)
            if not work_card:
                return False, None, ["Наряд не найден"]

            # Проверка наличия вида работы
            work_type = self.work_type_repository.get_by_id(work_type_id)
            if not work_type:
                return False, None, ["Вид работы не найден"]

            # Валидация количества
            if quantity <= 0:
                return False, None, ["Количество должно быть положительным числом"]

            # Создание элемента наряда
            item_data = {
                "work_card_id": work_card_id,
                "work_type_id": work_type_id,
                "quantity": quantity,
                "amount": quantity * work_type.price
            }

            # Добавление в БД
            result = self.work_card_repository.add_item(item_data)
            if not result:
                return False, None, ["Ошибка добавления элемента в БД"]

            # Обновление общей суммы наряда
            work_card.total_amount += item_data["amount"]
            self.work_card_repository.update(work_card)

            return True, result, []

        except Exception as e:
            return False, None, [f"Неожиданная ошибка: {str(e)}"]

    def remove_work_item(
        self,
        work_card_id: int,
        item_id: int
    ) -> Tuple[bool, List[str]]:
        """
        Удаляет элемент из наряда

        Args:
            work_card_id: ID наряда
            item_id: ID элемента

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        try:
            # Проверка наличия наряда
            work_card = self.work_card_repository.get_by_id(work_card_id)
            if not work_card:
                return False, ["Наряд не найден"]

            # Проверка наличия элемента
            work_card_item = self.work_card_repository.get_item_by_id(item_id)
            if not work_card_item or work_card_item["work_card_id"] != work_card_id:
                return False, ["Элемент наряда не найден"]

            # Удаление из БД
            result = self.work_card_repository.remove_item(item_id)
            if not result:
                return False, ["Ошибка удаления элемента из БД"]

            # Обновление общей суммы наряда
            work_card.total_amount -= work_card_item["amount"]
            self.work_card_repository.update(work_card)

            return True, []

        except Exception as e:
            return False, [f"Неожиданная ошибка: {str(e)}"]

    def get_workers_for_card(self, work_card_id: int) -> Tuple[bool, Optional[List[Worker]], List[str]]:
        """
        Получает список работников для наряда

        Args:
            work_card_id: ID наряда

        Returns:
            Tuple[bool, Optional[List[Worker]], List[str]]: (успех, список работников, список ошибок)
        """
        try:
            workers = self.work_card_repository.get_workers(work_card_id)
            if not workers:
                return False, None, ["Работники не найдены"]
            return True, workers, []
        except Exception as e:
            return False, None, [f"Ошибка получения работников: {str(e)}"]

    def add_worker_to_card(self, work_card_id: int, worker_id: int) -> Tuple[bool, List[str]]:
        """
        Добавляет работника в наряд

        Args:
            work_card_id: ID наряда
            worker_id: ID работника

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        try:
            # Проверка наличия наряда
            if not self.work_card_repository.exists(work_card_id):
                return False, ["Наряд не найден"]

            # Проверка наличия работника
            if not self.worker_repository.exists(worker_id):
                return False, ["Работник не найден"]

            # Проверка, что работник уже не добавлен
            if self.work_card_repository.is_worker_in_card(work_card_id, worker_id):
                return False, ["Работник уже добавлен в наряд"]

            # Добавление работника в наряд
            result = self.work_card_repository.add_worker(work_card_id, worker_id)
            if not result:
                return False, ["Ошибка добавления работника в наряд"]

            return True, []

        except Exception as e:
            return False, [f"Неожиданная ошибка: {str(e)}"]

    def remove_worker_from_card(self, work_card_id: int, worker_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет работника из наряда

        Args:
            work_card_id: ID наряда
            worker_id: ID работника

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        try:
            # Проверка наличия наряда
            if not self.work_card_repository.exists(work_card_id):
                return False, ["Наряд не найден"]

            # Проверка наличия работника в наряде
            if not self.work_card_repository.is_worker_in_card(work_card_id, worker_id):
                return False, ["Работник не найден в наряде"]

            # Удаление работника из наряда
            result = self.work_card_repository.remove_worker(work_card_id, worker_id)
            if not result:
                return False, ["Ошибка удаления работника из наряда"]

            return True, []

        except Exception as e:
            return False, [f"Неожиданная ошибка: {str(e)}"]

    def calculate_worker_amounts(self, work_card_id: int) -> Tuple[bool, Optional[Dict[int, float]], List[str]]:
        """
        Рассчитывает сумму для каждого работника бригады

        Args:
            work_card_id: ID наряда

        Returns:
            Tuple[bool, Optional[Dict[int, float]], List[str]]: (успех, словарь с суммами, список ошибок)
        """
        try:
            # Получаем наряд
            success, work_card, errors = self.get_work_card(work_card_id)
            if not success:
                return False, None, errors

            # Получаем список работников
            success, workers, errors = self.get_workers_for_card(work_card_id)
            if not success:
                return False, None, errors

            if not workers:
                return False, None, ["Наряд не содержит работников"]

            worker_count = len(workers)
            if worker_count == 0:
                return False, None, ["Наряд не содержит работников"]

            amount_per_worker = work_card.total_amount / worker_count
            worker_amounts = {worker.id: amount_per_worker for worker in workers}

            return True, worker_amounts, []

        except Exception as e:
            return False, None, [f"Неожиданная ошибка: {str(e)}"]

    def _validate_work_card_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Валидирует данные наряда

        Args:
            data: Данные для валидации

        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []

        # Проверка обязательных полей
        required_fields = {
            "card_number": "Номер наряда",
            "card_date": "Дата наряда",
            "product_id": "ID изделия",
            "contract_id": "ID контракта"
        }

        for field, field_name in required_fields.items():
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"{field_name} не может быть пустым")

        # Проверка даты
        if "card_date" in data:
            try:
                card_date = date.fromisoformat(data["card_date"])
                if card_date > date.today():
                    errors.append("Дата наряда не может быть в будущем")
            except ValueError:
                errors.append("Некорректная дата наряда")

        # Проверка ID изделий
        if "product_id" in data and int(data["product_id"]) <= 0:
            errors.append("ID изделия должно быть положительным числом")

        # Проверка ID контрактов
        if "contract_id" in data and int(data["contract_id"]) <= 0:
            errors.append("ID контракта должно быть положительным числом")

        return len(errors) == 0, errors

    def get_all_work_cards(self) -> Tuple[bool, Optional[List[WorkCard]], List[str]]:
        """
        Получает все наряды

        Returns:
            Tuple[bool, Optional[List[WorkCard]], List[str]]: (успех, список нарядов, список ошибок)
        """
        try:
            work_cards = self.work_card_repository.get_all()
            if not work_cards:
                return False, None, ["Наряды не найдены"]
            return True, work_cards, []
        except Exception as e:
            return False, None, [f"Ошибка получения нарядов: {str(e)}"]

    def search_work_cards(self, **kwargs) -> Tuple[bool, Optional[List[WorkCard]], List[str]]:
        """
        Поиск нарядов по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            Tuple[bool, Optional[List[WorkCard]], List[str]]: (успех, список нарядов, список ошибок)
        """
        try:
            work_cards = self.work_card_repository.search(**kwargs)
            if not work_cards:
                return False, None, ["Наряды не найдены"]
            return True, work_cards, []
        except Exception as e:
            return False, None, [f"Ошибка поиска нарядов: {str(e)}"]