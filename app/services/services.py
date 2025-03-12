"""
Сервисы приложения для работы с различными сущностями.
Содержит бизнес-логику для взаимодействия с базой данных.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
from future.backports.datetime import date

from app.db_manager import DatabaseManager
from app.models import (
    WorkCard, WorkCardItem, WorkCardWorker,
    Worker, WorkType, Product, Contract
)

logger = logging.getLogger(__name__)


class BaseService:
    """Базовый класс сервиса с общими методами"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager


class WorkerService(BaseService):
    """
    Сервис для работы с сотрудниками.
    """

    def get_all_workers(self) -> List[Worker]:
        """Получение всех работников"""
        return self.db.get_all_workers()

    def search_workers(self, search_text: str) -> List[Worker]:
        """Поиск работников по фамилии"""
        return self.db.search_workers(search_text)

    def save_worker(self, worker: Worker) -> Tuple[bool, str]:
        """Сохранение работника"""
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

    def delete_worker(self, worker_id: int) -> Tuple[bool, str]:
        """Удаление работника"""
        try:
            success = self.db.delete_worker(worker_id)
            return success, None if success else "Не удалось удалить работника"
        except Exception as e:
            logger.error(f"Ошибка при удалении работника: {e}")
            return False, f"Ошибка при удалении работника: {str(e)}"


class WorkTypeService(BaseService):
    """
    Сервис для работы с видами работ.
    """

    def get_all_work_types(self) -> List[WorkType]:
        """Получение всех видов работ"""
        return self.db.get_all_work_types()

    def search_work_types(self, search_text: str) -> List[WorkType]:
        """Поиск видов работ по наименованию"""
        return self.db.search_work_types(search_text)

    def save_work_type(self, work_type: WorkType) -> Tuple[bool, str]:
        """Сохранение вида работы"""
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

    def delete_work_type(self, work_type_id: int) -> Tuple[bool, str]:
        """Удаление вида работы"""
        try:
            success = self.db.delete_work_type(work_type_id)
            return success, None if success else "Не удалось удалить вид работы"
        except Exception as e:
            logger.error(f"Ошибка при удалении вида работы: {e}")
            return False, f"Ошибка при удалении вида работы: {str(e)}"


class ProductService(BaseService):
    """
    Сервис для работы с изделиями.
    """

    def get_all_products(self) -> List[Product]:
        """Получение всех изделий"""
        return self.db.get_all_products()

    def search_products(self, search_text: str) -> List[Product]:
        """Поиск изделий по номеру или типу"""
        return self.db.search_products(search_text)

    def save_product(self, product: Product) -> Tuple[bool, str]:
        """Сохранение изделия"""
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

    def delete_product(self, product_id: int) -> Tuple[bool, str]:
        """Удаление изделия"""
        try:
            success = self.db.delete_product(product_id)
            return success, None if success else "Не удалось удалить изделие"
        except Exception as e:
            logger.error(f"Ошибка при удалении изделия: {e}")
            return False, f"Ошибка при удалении изделия: {str(e)}"


class ContractService(BaseService):
    """
    Сервис для работы с контрактами.
    """

    def get_all_contracts(self) -> List[Contract]:
        """Получение всех контрактов"""
        return self.db.get_all_contracts()

    def search_contracts(self, search_text: str) -> List[Contract]:
        """Поиск контрактов по номеру"""
        return self.db.search_contracts(search_text)

    def save_contract(self, contract: Contract) -> Tuple[bool, str]:
        """Сохранение контракта"""
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

    def delete_contract(self, contract_id: int) -> Tuple[bool, str]:
        """Удаление контракта"""
        try:
            success = self.db.delete_contract(contract_id)
            return success, None if success else "Не удалось удалить контракт"
        except Exception as e:
            logger.error(f"Ошибка при удалении контракта: {e}")
            return False, f"Ошибка при удалении контракта: {str(e)}"
