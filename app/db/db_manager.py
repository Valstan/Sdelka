"""
Модуль для работы с базой данных SQLite.
Управляет соединением с БД, выполняет запросы и создает резервные копии.
"""
import os
import sqlite3
import shutil
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any, Tuple, Union

from app.config import DB_PATH, BACKUP_DIR, get_backup_filename

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем все модели данных
from app.db.models import (
    Worker, WorkType, Product, Contract,
    WorkCard, WorkCardItem, WorkCardWorker
)
from app.db.queries import *  # Импортируем все SQL-запросы


def format_date_for_db(date_value: Optional[Union[datetime, str]]) -> Optional[str]:
    """
    Форматирует дату для сохранения в БД.

    Args:
        date_value: Дата в формате datetime или строке

    Returns:
        Optional[str]: Дата в строковом формате для БД или None
    """
    if not date_value:
        return None

    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    return str(date_value)


class DatabaseManager:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_path: str = DB_PATH):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self.connection = None
        self.create_backup()
        self.connect()
        self.initialize_db()

    def connect(self) -> None:
        """Установка соединения с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Соединение с БД {self.db_path} установлено")
        except sqlite3.Error as e:
            logger.error(f"Ошибка соединения с БД: {e}")
            raise

    def create_backup(self) -> str:
        """
        Создает резервную копию базы данных с текущей датой и временем в имени файла.

        Returns:
            str: Путь к созданной резервной копии
        """
        if not os.path.exists(self.db_path):
            logger.info(f"Файл БД {self.db_path} не существует, резервная копия не создана")
            return ""

        # Убедимся, что директория для резервных копий существует
        if not os.path.exists(BACKUP_DIR):
            try:
                os.makedirs(BACKUP_DIR)
                logger.info(f"Создана директория для резервных копий: {BACKUP_DIR}")
            except Exception as e:
                logger.error(f"Не удалось создать директорию для резервных копий: {e}")
                return ""

        # Вызываем функцию со скобками
        backup_path = os.path.join(BACKUP_DIR, get_backup_filename())

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Создана резервная копия БД: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""

    def initialize_db(self) -> None:
        """Инициализация структуры базы данных при первом запуске"""
        from app.db.queries import CREATE_TABLES_QUERIES

        try:
            cursor = self.connection.cursor()

            # Создаем все необходимые таблицы
            for query in CREATE_TABLES_QUERIES:
                cursor.execute(query)

            self.connection.commit()
            logger.info("Структура БД успешно инициализирована")
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def execute_query(self, query: str, parameters: Tuple = ()) -> Optional[sqlite3.Cursor]:
        """
        Выполнение SQL-запроса без возврата данных.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Cursor объект SQLite или None в случае ошибки
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return None

    def execute_query_fetchall(self, query: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Выполнение SQL-запроса с возвратом всех строк результата.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Список словарей с данными из запроса
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)

            # Преобразуем результат в список словарей
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return []

    def execute_query_fetchone(self, query: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Выполнение SQL-запроса с возвратом одной строки результата.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Словарь с данными или None если нет результата или произошла ошибка
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)

            row = cursor.fetchone()
            if row:
                # Преобразуем строку в словарь
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, параметры: {parameters}")
            return None

    def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с БД закрыто")

    # Методы для работы с работниками (Workers)
    def get_all_workers(self) -> List[Worker]:
        """Получение всех работников из БД"""
        rows = self.execute_query_fetchall(GET_ALL_WORKERS)
        return [Worker(**row) for row in rows]

    def get_worker_by_id(self, worker_id: int) -> Optional[Worker]:
        """Получение работника по ID"""
        row = self.execute_query_fetchone(GET_WORKER_BY_ID, (worker_id,))
        return Worker(**row) if row else None

    def search_workers(self, search_text: str) -> List[Worker]:
        """Поиск работников по фамилии"""
        rows = self.execute_query_fetchall(SEARCH_WORKERS, (search_text,))
        return [Worker(**row) for row in rows]

    def add_worker(self, worker: Worker) -> int:
        """Добавление нового работника"""
        cursor = self.execute_query(
            ADD_WORKER,
            (worker.last_name, worker.first_name, worker.middle_name, worker.position)
        )
        return cursor.lastrowid if cursor else 0

    def update_worker(self, worker: Worker) -> bool:
        """Обновление данных работника"""
        cursor = self.execute_query(
            UPDATE_WORKER,
            (worker.last_name, worker.first_name, worker.middle_name, worker.position, worker.id)
        )
        return cursor is not None

    def delete_worker(self, worker_id: int) -> bool:
        """Удаление работника"""
        cursor = self.execute_query(DELETE_WORKER, (worker_id,))
        return cursor is not None

    # Методы для работы с видами работ (WorkTypes)
    def get_all_work_types(self) -> List[WorkType]:
        """Получение всех видов работ из БД"""
        rows = self.execute_query_fetchall(GET_ALL_WORK_TYPES)
        return [WorkType(**row) for row in rows]

    def get_work_type_by_id(self, work_type_id: int) -> Optional[WorkType]:
        """Получение вида работы по ID"""
        row = self.execute_query_fetchone(GET_WORK_TYPE_BY_ID, (work_type_id,))
        return WorkType(**row) if row else None

    def search_work_types(self, search_text: str) -> List[WorkType]:
        """Поиск видов работ по наименованию"""
        rows = self.execute_query_fetchall(SEARCH_WORK_TYPES, (search_text,))
        return [WorkType(**row) for row in rows]

    def add_work_type(self, work_type: WorkType) -> int:
        """Добавление нового вида работы"""
        cursor = self.execute_query(
            ADD_WORK_TYPE,
            (work_type.name, work_type.price, work_type.description)
        )
        return cursor.lastrowid if cursor else 0

    def update_work_type(self, work_type: WorkType) -> bool:
        """Обновление данных вида работы"""
        cursor = self.execute_query(
            UPDATE_WORK_TYPE,
            (work_type.name, work_type.price, work_type.description, work_type.id)
        )
        return cursor is not None

    def delete_work_type(self, work_type_id: int) -> bool:
        """Удаление вида работы"""
        cursor = self.execute_query(DELETE_WORK_TYPE, (work_type_id,))
        return cursor is not None

    # Методы для работы с изделиями (Products)
    def get_all_products(self) -> List[Product]:
        """Получение всех изделий из БД"""
        rows = self.execute_query_fetchall(GET_ALL_PRODUCTS)
        return [Product(**row) for row in rows]

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение изделия по ID"""
        row = self.execute_query_fetchone(GET_PRODUCT_BY_ID, (product_id,))
        return Product(**row) if row else None

    def search_products(self, search_text: str) -> List[Product]:
        """Поиск изделий по номеру или типу"""
        rows = self.execute_query_fetchall(SEARCH_PRODUCTS, (search_text, search_text))
        return [Product(**row) for row in rows]

    def add_product(self, product: Product) -> int:
        """Добавление нового изделия"""
        cursor = self.execute_query(
            ADD_PRODUCT,
            (product.product_number, product.product_type, product.additional_number, product.description)
        )
        return cursor.lastrowid if cursor else 0

    def update_product(self, product: Product) -> bool:
        """Обновление данных изделия"""
        cursor = self.execute_query(
            UPDATE_PRODUCT,
            (product.product_number, product.product_type, product.additional_number, product.description, product.id)
        )
        return cursor is not None

    def delete_product(self, product_id: int) -> bool:
        """Удаление изделия"""
        cursor = self.execute_query(DELETE_PRODUCT, (product_id,))
        return cursor is not None

    # Методы для работы с контрактами (Contracts)
    def get_all_contracts(self) -> List[Contract]:
        """Получение всех контрактов из БД"""
        rows = self.execute_query_fetchall(GET_ALL_CONTRACTS)
        return [Contract(**row) for row in rows]

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """Получение контракта по ID"""
        row = self.execute_query_fetchone(GET_CONTRACT_BY_ID, (contract_id,))
        return Contract(**row) if row else None

    def search_contracts(self, search_text: str) -> List[Contract]:
        """Поиск контрактов по номеру"""
        rows = self.execute_query_fetchall(SEARCH_CONTRACTS, (search_text,))
        return [Contract(**row) for row in rows]

    def add_contract(self, contract: Contract) -> int:
        """Добавление нового контракта"""
        try:
            # Форматируем даты для БД
            start_date_db = None
            if contract.start_date:
                if isinstance(contract.start_date, datetime):
                    start_date_db = contract.start_date.strftime("%Y-%m-%d")
                else:
                    start_date_db = str(contract.start_date)

            end_date_db = None
            if contract.end_date:
                if isinstance(contract.end_date, datetime):
                    end_date_db = contract.end_date.strftime("%Y-%m-%d")
                else:
                    end_date_db = str(contract.end_date)

            cursor = self.execute_query(
                ADD_CONTRACT,
                (contract.contract_number, contract.description, start_date_db, end_date_db)
            )
            return cursor.lastrowid if cursor else 0
        except Exception as e:
            logger.error(f"Ошибка при добавлении контракта: {e}")
            return 0

    def update_contract(self, contract: Contract) -> bool:
        """Обновление контракта"""
        try:
            # Форматируем даты для БД
            start_date_db = None
            if contract.start_date:
                if isinstance(contract.start_date, datetime):
                    start_date_db = contract.start_date.strftime("%Y-%m-%d")
                else:
                    start_date_db = str(contract.start_date)

            end_date_db = None
            if contract.end_date:
                if isinstance(contract.end_date, datetime):
                    end_date_db = contract.end_date.strftime("%Y-%m-%d")
                else:
                    end_date_db = str(contract.end_date)

            result = self.execute_query(
                UPDATE_CONTRACT,
                (contract.contract_number, contract.description, start_date_db, end_date_db, contract.id)
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Ошибка при обновлении контракта: {e}")
            return False

    def delete_contract(self, contract_id: int) -> bool:
        """Удаление контракта"""
        cursor = self.execute_query(DELETE_CONTRACT, (contract_id,))
        return cursor is not None

    # Методы для работы с карточками работ (WorkCards)
    def get_next_card_number(self) -> int:
        """Получение следующего номера карточки"""
        row = self.execute_query_fetchone(GET_NEXT_CARD_NUMBER)
        return row["next_number"] if row else 1

    def get_all_work_cards(self) -> List[WorkCard]:
        """Получение всех карточек работ из БД"""
        rows = self.execute_query_fetchall(GET_ALL_WORK_CARDS)
        return [WorkCard(**row) for row in rows]

    def get_work_card_by_id(self, card_id: int) -> Optional[WorkCard]:
        """Получение карточки работ по ID с элементами и работниками"""
        row = self.execute_query_fetchone(GET_WORK_CARD_BY_ID, (card_id,))
        if not row:
            return None

        work_card = WorkCard(**row)

        # Получаем элементы карточки (виды работ)
        items_rows = self.execute_query_fetchall(GET_WORK_CARD_ITEMS, (card_id,))
        work_card.items = [WorkCardItem(**item_row) for item_row in items_rows]

        # Получаем работников карточки
        workers_rows = self.execute_query_fetchall(GET_WORK_CARD_WORKERS, (card_id,))
        work_card.workers = [WorkCardWorker(**worker_row) for worker_row in workers_rows]

        return work_card

    def add_work_card(self, work_card: WorkCard) -> int:
        """
        Добавление новой карточки работ с элементами и работниками.
        Транзакционная операция.
        """
        try:
            # Начинаем транзакцию
            self.connection.execute("BEGIN TRANSACTION")

            # Вставляем карточку работ
            cursor = self.connection.cursor()
            cursor.execute(
                ADD_WORK_CARD,
                (work_card.card_number, work_card.card_date,
                 work_card.product_id, work_card.contract_id, work_card.total_amount)
            )
            work_card_id = cursor.lastrowid

            # Вставляем элементы карточки (виды работ)
            for item in work_card.items:
                cursor.execute(
                    ADD_WORK_CARD_ITEM,
                    (work_card_id, item.work_type_id, item.quantity, item.amount)
                )

            # Вставляем работников карточки
            for worker in work_card.workers:
                cursor.execute(
                    ADD_WORK_CARD_WORKER,
                    (work_card_id, worker.worker_id, worker.amount)
                )

            # Завершаем транзакцию
            self.connection.commit()
            return work_card_id

        except Exception as e:
            # Отменяем транзакцию в случае ошибки
            self.connection.rollback()
            logger.error(f"Ошибка при добавлении карточки работ: {e}")
            return 0

    def update_work_card(self, work_card: WorkCard) -> bool:
        """
        Обновление карточки работ с элементами и работниками.
        Транзакционная операция.
        """
        try:
            # Начинаем транзакцию
            self.connection.execute("BEGIN TRANSACTION")

            # Обновляем карточку работ
            cursor = self.connection.cursor()
            cursor.execute(
                UPDATE_WORK_CARD,
                (work_card.card_date, work_card.product_id,
                 work_card.contract_id, work_card.total_amount, work_card.id)
            )

            # Удаляем существующие элементы карточки и работников
            cursor.execute(DELETE_WORK_CARD_ITEMS_BY_CARD, (work_card.id,))
            cursor.execute(DELETE_WORK_CARD_WORKERS_BY_CARD, (work_card.id,))

            # Вставляем элементы карточки (виды работ)
            for item in work_card.items:
                cursor.execute(
                    ADD_WORK_CARD_ITEM,
                    (work_card.id, item.work_type_id, item.quantity, item.amount)
                )

            # Вставляем работников карточки
            for worker in work_card.workers:
                cursor.execute(
                    ADD_WORK_CARD_WORKER,
                    (work_card.id, worker.worker_id, worker.amount)
                )

            # Завершаем транзакцию
            self.connection.commit()
            return True

        except Exception as e:
            # Отменяем транзакцию в случае ошибки
            self.connection.rollback()
            logger.error(f"Ошибка при обновлении карточки работ: {e}")
            return False

    def delete_work_card(self, card_id: int) -> bool:
        """Удаление карточки работ и связанных с ней данных"""
        try:
            # Начинаем транзакцию
            self.connection.execute("BEGIN TRANSACTION")

            cursor = self.connection.cursor()
            # Удаляем связанные элементы и работников
            cursor.execute(DELETE_WORK_CARD_ITEMS_BY_CARD, (card_id,))
            cursor.execute(DELETE_WORK_CARD_WORKERS_BY_CARD, (card_id,))
            # Удаляем саму карточку
            cursor.execute(DELETE_WORK_CARD, (card_id,))

            # Завершаем транзакцию
            self.connection.commit()
            return True

        except Exception as e:
            # Отменяем транзакцию в случае ошибки
            self.connection.rollback()
            logger.error(f"Ошибка при удалении карточки работ: {e}")
            return False

    # Метод для формирования отчетов
    def get_report_data(self,
                       worker_id: int = 0,
                       start_date: str = None,
                       end_date: str = None,
                       work_type_id: int = 0,
                       product_id: int = 0,
                       contract_id: int = 0) -> List[Dict]:
        """
        Получение данных для отчета по заданным фильтрам.

        Args:
            worker_id: ID работника (0 - все работники)
            start_date: Начальная дата отчета (формат YYYY-MM-DD)
            end_date: Конечная дата отчета (формат YYYY-MM-DD)
            work_type_id: ID вида работы (0 - все виды работ)
            product_id: ID изделия (0 - все изделия)
            contract_id: ID контракта (0 - все контракты)

        Returns:
            Список словарей с данными для отчета
        """
        # Если даты не заданы, используем широкий диапазон
        if not start_date:
            start_date = "2000-01-01"
        if not end_date:
            end_date = "2100-12-31"

        # Получаем данные из БД
        rows = self.execute_query_fetchall(
            REPORT_BY_WORKER,
            (worker_id, worker_id, start_date, end_date,
             work_type_id, work_type_id, product_id, product_id,
             contract_id, contract_id)
        )

        return rows

