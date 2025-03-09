import unittest
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

# Импортируйте ваш класс базы данных
from app.db import Database as Database  # замените на вашу структуру импорта

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Создаем временную базу для тестов
        self.test_db_path = "test_database.db"
        self.db = Database(self.test_db_path)
        self.connection = sqlite3.connect(self.test_db_path)

        # Создаем минимальную структуру для тестов
        self.create_test_schema()

    def create_test_schema(self):
        """Создает минимальную схему БД для тестирования"""
        cursor = self.connection.cursor()
        # Создаем таблицы для тестов
        cursor.executescript("""
            -- Создаем таблицу работников
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY,
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT
            );

            -- Создаем таблицу нарядов
            CREATE TABLE IF NOT EXISTS work_cards (
                id INTEGER PRIMARY KEY,
                card_number TEXT,
                card_date TEXT,
                product_id INTEGER,
                contract_id INTEGER
            );

            -- Создаем таблицу элементов наряда
            CREATE TABLE IF NOT EXISTS work_card_items (
                id INTEGER PRIMARY KEY,
                work_card_id INTEGER,
                work_type_id INTEGER,
                quantity REAL,
                amount REAL,
                FOREIGN KEY (work_card_id) REFERENCES work_cards(id)
            );

            -- Создаем таблицу работников по нарядам
            CREATE TABLE IF NOT EXISTS work_card_workers (
                id INTEGER PRIMARY KEY,
                work_card_id INTEGER,
                worker_id INTEGER,
                amount REAL,
                updated_at TEXT,
                FOREIGN KEY (work_card_id) REFERENCES work_cards(id),
                FOREIGN KEY (worker_id) REFERENCES workers(id)
            );

            -- Тестовые данные
            INSERT INTO workers (id, last_name, first_name, middle_name) VALUES
                (1, 'Иванов', 'Иван', 'Иванович'),
                (2, 'Петров', 'Петр', 'Петрович');

            INSERT INTO work_cards (id, card_number, card_date, product_id, contract_id) VALUES
                (1, 'N001', '2023-01-01', 1, 1);

            INSERT INTO work_card_items (id, work_card_id, work_type_id, quantity, amount) VALUES
                (1, 1, 1, 2.0, 1000.0);

            INSERT INTO work_card_workers (id, work_card_id, worker_id, amount, updated_at) VALUES
                (1, 1, 1, 500.0, '2023-01-02'),
                (2, 1, 2, 500.0, '2023-01-02');
        """)
        self.connection.commit()

    def tearDown(self):
        """Закрываем соединение и удаляем тестовую БД"""
        self.connection.close()
        self.db.close()
        if Path(self.test_db_path).exists():
            Path(self.test_db_path).unlink()

    def test_connection(self):
        """Тест подключения к БД"""
        self.assertTrue(self.db.is_connected())

    def test_execute_query_fetch_all(self):
        """Тест выполнения запроса с получением всех результатов"""
        query = "SELECT * FROM workers"
        result = self.db.execute_query_fetch_all(query)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["last_name"], "Иванов")

    def test_execute_query_fetch_one(self):
        """Тест выполнения запроса с получением одного результата"""
        query = "SELECT * FROM workers WHERE id = ?"
        result = self.db.execute_query_fetch_one(query, (1,))
        self.assertIsNotNone(result)
        self.assertEqual(result["last_name"], "Иванов")

    def test_execute_non_query(self):
        """Тест выполнения запроса без возврата результатов"""
        query = "UPDATE workers SET last_name = ? WHERE id = ?"
        self.db.execute_non_query(query, ("Сидоров", 1))

        # Проверяем результат
        result = self.db.execute_query_fetch_one("SELECT * FROM workers WHERE id = ?", (1,))
        self.assertEqual(result["last_name"], "Сидоров")

    def test_transaction(self):
        """Тест работы транзакций"""
        try:
            # Начинаем транзакцию
            self.db.begin_transaction()

            # Выполняем несколько запросов
            self.db.execute_non_query("UPDATE workers SET last_name = ? WHERE id = ?", ("Сидоров", 1))
            self.db.execute_non_query("UPDATE workers SET last_name = ? WHERE id = ?", ("Николаев", 2))

            # Фиксируем транзакцию
            self.db.commit_transaction()

            # Проверяем результаты
            worker1 = self.db.execute_query_fetch_one("SELECT * FROM workers WHERE id = ?", (1,))
            worker2 = self.db.execute_query_fetch_one("SELECT * FROM workers WHERE id = ?", (2,))

            self.assertEqual(worker1["last_name"], "Сидоров")
            self.assertEqual(worker2["last_name"], "Николаев")

        except Exception as e:
            # В случае ошибки откатываем транзакцию
            self.db.rollback_transaction()
            raise

    def test_transaction_rollback(self):
        """Тест отката транзакции"""
        # Запоминаем исходные данные
        worker1_original = self.db.execute_query_fetch_one("SELECT * FROM workers WHERE id = ?", (1,))

        try:
            # Начинаем транзакцию
            self.db.begin_transaction()

            # Выполняем запрос
            self.db.execute_non_query("UPDATE workers SET last_name = ? WHERE id = ?", ("Сидоров", 1))

            # Имитируем ошибку и откатываем транзакцию
            raise Exception("Test exception")

        except Exception:
            # Откатываем транзакцию
            self.db.rollback_transaction()

        # Проверяем, что данные не изменились
        worker1_after = self.db.execute_query_fetch_one("SELECT * FROM workers WHERE id = ?", (1,))
        self.assertEqual(worker1_original["last_name"], worker1_after["last_name"])

if __name__ == "__main__":
    unittest.main()