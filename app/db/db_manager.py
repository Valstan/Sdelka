"""
Модуль для работы с базой данных SQLite.
Управляет соединением с БД, выполняет запросы и создает резервные копии.
"""
import os
import sqlite3
import shutil
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Union

from app.config import DB_SETTINGS, DIRECTORIES
from app.db.models import (
    Worker, WorkType, Product, Contract,
    WorkCard, WorkCardItem, WorkCardWorker
)
from app.db.queries import (
    CREATE_TABLES_QUERIES,
    GET_ALL_WORKERS, GET_WORKER_BY_ID, SEARCH_WORKERS,
    GET_ALL_WORK_TYPES, GET_WORK_TYPE_BY_ID, SEARCH_WORK_TYPES,
    GET_ALL_PRODUCTS, GET_PRODUCT_BY_ID, SEARCH_PRODUCTS,
    GET_ALL_CONTRACTS, GET_CONTRACT_BY_ID, SEARCH_CONTRACTS,
    GET_ALL_WORK_CARDS, GET_WORK_CARD_BY_ID,
    GET_WORK_CARD_ITEMS, GET_WORK_CARD_WORKERS,
    REPORT_BY_WORKER_BASE, get_report_query
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Класс для управления базой данных SQLite.
    Обеспечивает подключение к БД, выполнение запросов и создание резервных копий.
    """

    def __init__(self, db_path: str = None):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path or DB_SETTINGS['database_path']
        self.connection = None

        # Создание резервной копии БД при инициализации
        if DB_SETTINGS['create_backup_on_start']:
            self.create_backup()

        # Установка соединения с БД
        self.connect()

        # Инициализация структуры БД, если она не существует
        self.initialize_db()

    def connect(self) -> None:
        """Установка соединения с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Успешно подключено к БД: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def create_backup(self) -> str:
        """
        Создание резервной копии базы данных.

        Returns:
            str: Путь к созданной резервной копии
        """
        if not os.path.exists(self.db_path):
            logger.info(f"Файл БД {self.db_path} не существует, резервная копия не создана")
            return ""

        backup_dir = DIRECTORIES['backups']
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Резервная копия БД создана: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии БД: {e}")
            return ""

    def initialize_db(self) -> None:
        """
        Инициализация структуры базы данных при первом запуске.
        Создает необходимые таблицы, если они не существуют.
        """
        try:
            cursor = self.connection.cursor()
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
            logger.debug(f"Запрос: {query}, Параметры: {parameters}")
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

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, Параметры: {parameters}")
            return []

    def execute_query_fetchone(self, query: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Выполнение SQL-запроса с возвратом одной строки результата.

        Args:
            query: SQL-запрос
            parameters: Параметры для SQL-запроса

        Returns:
            Словарь с данными из запроса или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)

            row = cursor.fetchone()
            if not row:
                return None

            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            logger.debug(f"Запрос: {query}, Параметры: {parameters}")
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
            """
            INSERT INTO workers (last_name, first_name, middle_name, position)
            VALUES (?, ?, ?, ?)
            """,
            (worker.last_name, worker.first_name, worker.middle_name, worker.position)
        )
        return cursor.lastrowid if cursor else 0

    def update_worker(self, worker: Worker) -> bool:
        """Обновление данных работника"""
        success = self.execute_query(
            """
            UPDATE workers 
            SET last_name = ?, first_name = ?, middle_name = ?, position = ?
            WHERE id = ?
            """,
            (worker.last_name, worker.first_name, worker.middle_name, worker.position, worker.id)
        ) is not None
        return success

    def delete_worker(self, worker_id: int) -> bool:
        """Удаление работника"""
        success = self.execute_query(
            "DELETE FROM workers WHERE id = ?",
            (worker_id,)
        ) is not None
        return success

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
            """
            INSERT INTO work_types (name, price, description)
            VALUES (?, ?, ?)
            """,
            (work_type.name, work_type.price, work_type.description)
        )
        return cursor.lastrowid if cursor else 0

    def update_work_type(self, work_type: WorkType) -> bool:
        """Обновление данных вида работы"""
        success = self.execute_query(
            """
            UPDATE work_types 
            SET name = ?, price = ?, description = ?
            WHERE id = ?
            """,
            (work_type.name, work_type.price, work_type.description, work_type.id)
        ) is not None
        return success

    def delete_work_type(self, work_type_id: int) -> bool:
        """Удаление вида работы"""
        success = self.execute_query(
            "DELETE FROM work_types WHERE id = ?",
            (work_type_id,)
        ) is not None
        return success

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
            """
            INSERT INTO products (product_number, product_type, additional_number, description)
            VALUES (?, ?, ?, ?)
            """,
            (product.product_number, product.product_type, product.additional_number, product.description)
        )
        return cursor.lastrowid if cursor else 0

    def update_product(self, product: Product) -> bool:
        """Обновление данных изделия"""
        success = self.execute_query(
            """
            UPDATE products 
            SET product_number = ?, product_type = ?, additional_number = ?, description = ?
            WHERE id = ?
            """,
            (product.product_number, product.product_type, product.additional_number, product.description, product.id)
        ) is not None
        return success

    def delete_product(self, product_id: int) -> bool:
        """Удаление изделия"""
        success = self.execute_query(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        ) is not None
        return success

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
        cursor = self.execute_query(
            """
            INSERT INTO contracts (contract_number, description, start_date, end_date)
            VALUES (?, ?, ?, ?)
            """,
            (contract.contract_number, contract.description, contract.start_date, contract.end_date)
        )
        return cursor.lastrowid if cursor else 0

    def update_contract(self, contract: Contract) -> bool:
        """Обновление данных контракта"""
        success = self.execute_query(
            """
            UPDATE contracts 
            SET contract_number = ?, description = ?, start_date = ?, end_date = ?
            WHERE id = ?
            """,
            (contract.contract_number, contract.description, contract.start_date, contract.end_date, contract.id)
        ) is not None
        return success

    def delete_contract(self, contract_id: int) -> bool:
        """Удаление контракта"""
        success = self.execute_query(
            "DELETE FROM contracts WHERE id = ?",
            (contract_id,)
        ) is not None
        return success

    # Методы для работы с карточками работ (WorkCards)
    def get_next_card_number(self) -> int:
        """Получение следующего номера карточки"""
        row = self.execute_query_fetchone("SELECT COALESCE(MAX(card_number), 0) + 1 AS next_number FROM work_cards")
        return row['next_number'] if row else 1

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
        """Добавление новой карточки работ с элементами и работниками. Транзакционная операция."""
        try:
            self.connection.execute("BEGIN TRANSACTION")

            # Вставляем карточку работ
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO work_cards (card_number, card_date, product_id, contract_id, total_amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (work_card.card_number, work_card.card_date, work_card.product_id, work_card.contract_id, work_card.total_amount)
            )
            work_card_id = cursor.lastrowid

            # Вставляем элементы карточки (виды работ)
            for item in work_card.items:
                cursor.execute(
                    """
                    INSERT INTO work_card_items (work_card_id, work_type_id, quantity, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (work_card_id, item.work_type_id, item.quantity, item.amount)
                )

            # Вставляем работников карточки
            for worker in work_card.workers:
                cursor.execute(
                    """
                    INSERT INTO work_card_workers (work_card_id, worker_id, amount)
                    VALUES (?, ?, ?)
                    """,
                    (work_card_id, worker.worker_id, worker.amount)
                )

            self.connection.commit()
            return work_card_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Ошибка добавления карточки работ: {e}")
            return 0

    def update_work_card(self, work_card: WorkCard) -> bool:
        """Обновление карточки работ с элементами и работниками. Транзакционная операция."""
        try:
            self.connection.execute("BEGIN TRANSACTION")

            # Обновляем карточку работ
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE work_cards 
                SET card_date = ?, product_id = ?, contract_id = ?, total_amount = ?
                WHERE id = ?
                """,
                (work_card.card_date, work_card.product_id, work_card.contract_id, work_card.total_amount, work_card.id)
            )

            # Удаляем существующие элементы и работников
            cursor.execute("DELETE FROM work_card_items WHERE work_card_id = ?", (work_card.id,))
            cursor.execute("DELETE FROM work_card_workers WHERE work_card_id = ?", (work_card.id,))

            # Вставляем элементы карточки (виды работ)
            for item in work_card.items:
                cursor.execute(
                    """
                    INSERT INTO work_card_items (work_card_id, work_type_id, quantity, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (work_card.id, item.work_type_id, item.quantity, item.amount)
                )

            # Вставляем работников карточки
            for worker in work_card.workers:
                cursor.execute(
                    """
                    INSERT INTO work_card_workers (work_card_id, worker_id, amount)
                    VALUES (?, ?, ?)
                    """,
                    (work_card.id, worker.worker_id, worker.amount)
                )

            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Ошибка обновления карточки работ: {e}")
            return False

    def delete_work_card(self, card_id: int) -> bool:
        """Удаление карточки работ и связанных с ней данных. Транзакционная операция."""
        try:
            self.connection.execute("BEGIN TRANSACTION")

            # Удаляем связанные элементы и работников
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM work_card_items WHERE work_card_id = ?", (card_id,))
            cursor.execute("DELETE FROM work_card_workers WHERE work_card_id = ?", (card_id,))

            # Удаляем саму карточку
            cursor.execute("DELETE FROM work_cards WHERE id = ?", (card_id,))

            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Ошибка удаления карточки работ: {e}")
            return False

    # Методы для формирования отчетов
    def get_report_data(self,
                       worker_id: int = 0,
                       start_date: str = None,
                       end_date: str = None,
                       work_type_id: int = 0,
                       product_id: int = 0,
                       contract_id: int = 0) -> List[Dict[str, Any]]:
        """
        Получение данных для отчета по заданным параметрам.

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
        query, params = get_report_query({
            "worker_id": worker_id,
            "start_date": start_date,
            "end_date": end_date,
            "work_type_id": work_type_id,
            "product_id": product_id,
            "contract_id": contract_id
        })

        return self.execute_query_fetchall(query, params)