"""
Сервисы приложения для работы с различными сущностями.
Содержит бизнес-логику для взаимодействия с базой данных.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.db_manager import DatabaseManager
from app.models import Worker, WorkType, Product, Contract

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Базовый класс сервиса с общими методами."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    @abstractmethod
    def get_all(self) -> List[object]:
        """Получение всех записей."""
        pass

    @abstractmethod
    def search(self, search_text: str) -> List[object]:
        """Поиск записей по тексту."""
        pass

    @abstractmethod
    def save(self, entity: object) -> Tuple[bool, Optional[str]]:
        """Сохранение записи."""
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> Tuple[bool, Optional[str]]:
        """Удаление записи."""
        pass


class WorkerService(BaseService):
    """Сервис для работы с сотрудниками."""

    def get_all(self) -> List[Worker]:
        """Получение всех работников."""
        return self.db.get_all_workers()

    def search(self, search_text: str) -> List[Worker]:
        """Поиск работников по фамилии."""
        return self.db.search_workers(search_text)

    def save(self, worker: Worker) -> Tuple[bool, Optional[str]]:
        """Сохранение работника."""
        try:
            if worker.id:
                success = self.db.update_worker(worker)
            else:
                worker_id = self.db.add_worker(worker)
                success = worker_id > 0
                if success:
                    worker.id = worker_id
            return (success, None) if success else (False, "Не удалось сохранить работника")
        except Exception as e:
            logger.error(f"Ошибка при сохранении работника: {e}", exc_info=True)
            return False, f"Ошибка при сохранении работника: {str(e)}"

    def delete(self, worker_id: int) -> Tuple[bool, Optional[str]]:
        """Удаление работника."""
        try:
            success = self.db.delete_worker(worker_id)
            return (success, None) if success else (False, "Не удалось удалить работника")
        except Exception as e:
            logger.error(f"Ошибка при удалении работника: {e}", exc_info=True)
            return False, f"Ошибка при удалении работника: {str(e)}"


class WorkTypeService(BaseService):
    """Сервис для работы с видами работ."""

    def get_all(self) -> List[WorkType]:
        """Получение всех видов работ."""
        return self.db.get_all_work_types()

    def search(self, search_text: str) -> List[WorkType]:
        """Поиск видов работ по наименованию."""
        return self.db.search_work_types(search_text)

    def save(self, work_type: WorkType) -> Tuple[bool, Optional[str]]:
        """Сохранение вида работы."""
        try:
            if work_type.id:
                success = self.db.update_work_type(work_type)
            else:
                work_type_id = self.db.add_work_type(work_type)
                success = work_type_id > 0
                if success:
                    work_type.id = work_type_id
            return (success, None) if success else (False, "Не удалось сохранить вид работы")
        except Exception as e:
            logger.error(f"Ошибка при сохранении вида работы: {e}", exc_info=True)
            return False, f"Ошибка при сохранении вида работы: {str(e)}"

    def delete(self, work_type_id: int) -> Tuple[bool, Optional[str]]:
        """Удаление вида работы."""
        try:
            success = self.db.delete_work_type(work_type_id)
            return (success, None) if success else (False, "Не удалось удалить вид работы")
        except Exception as e:
            logger.error(f"Ошибка при удалении вида работы: {e}", exc_info=True)
            return False, f"Ошибка при удалении вида работы: {str(e)}"


class ProductService(BaseService):
    """Сервис для работы с изделиями."""

    def get_all(self) -> List[Product]:
        """Получение всех изделий."""
        return self.db.get_all_products()

    def search(self, search_text: str) -> List[Product]:
        """Поиск изделий по номеру или типу."""
        return self.db.search_products(search_text)

    def save(self, product: Product) -> Tuple[bool, Optional[str]]:
        """Сохранение изделия."""
        try:
            if product.id:
                success = self.db.update_product(product)
            else:
                product_id = self.db.add_product(product)
                success = product_id > 0
                if success:
                    product.id = product_id
            return (success, None) if success else (False, "Не удалось сохранить изделие")
        except Exception as e:
            logger.error(f"Ошибка при сохранении изделия: {e}", exc_info=True)
            return False, f"Ошибка при сохранении изделия: {str(e)}"

    def delete(self, product_id: int) -> Tuple[bool, Optional[str]]:
        """Удаление изделия."""
        try:
            success = self.db.delete_product(product_id)
            return (success, None) if success else (False, "Не удалось удалить изделие")
        except Exception as e:
            logger.error(f"Ошибка при удалении изделия: {e}", exc_info=True)
            return False, f"Ошибка при удалении изделия: {str(e)}"


class ContractService(BaseService):
    """Сервис для работы с контрактами."""

    def get_all(self) -> List[Contract]:
        """Получение всех контрактов."""
        return self.db.get_all_contracts()

    def search(self, search_text: str) -> List[Contract]:
        """Поиск контрактов по номеру."""
        return self.db.search_contracts(search_text)

    def save(self, contract: Contract) -> Tuple[bool, Optional[str]]:
        """Сохранение контракта."""
        try:
            if contract.id:
                success = self.db.update_contract(contract)
            else:
                contract_id = self.db.add_contract(contract)
                success = contract_id > 0
                if success:
                    contract.id = contract_id
            return (success, None) if success else (False, "Не удалось сохранить контракт")
        except Exception as e:
            logger.error(f"Ошибка при сохранении контракта: {e}", exc_info=True)
            return False, f"Ошибка при сохранении контракта: {str(e)}"

    def delete(self, contract_id: int) -> Tuple[bool, Optional[str]]:
        """Удаление контракта."""
        try:
            success = self.db.delete_contract(contract_id)
            return (success, None) if success else (False, "Не удалось удалить контракт")
        except Exception as e:
            logger.error(f"Ошибка при удалении контракта: {e}", exc_info=True)
            return False, f"Ошибка при удалении контракта: {str(e)}"