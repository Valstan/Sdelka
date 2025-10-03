import pytest
from unittest.mock import Mock, patch, MagicMock
from services.work_orders import create_work_order, load_work_order, WorkOrderInput, WorkOrderItemInput, WorkOrderWorkerInput
from db.schema import initialize_schema
from db.sqlite import get_connection
import tempfile
import os
import sqlite3


class TestWorkOrderItems:
    """Тесты для проверки сохранения и загрузки позиций нарядов."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        
        # Создаем тестовую базу данных
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        initialize_schema(self.conn)
        
        # Добавляем тестовые данные
        self._setup_test_data()
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'temp_dir'):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_test_data(self):
        """Создание тестовых данных."""
        # Создаем контракт
        cursor = self.conn.execute(
            "INSERT INTO contracts (code, name) VALUES (?, ?)",
            ("TEST-001", "Тестовый контракт")
        )
        self.contract_id = cursor.lastrowid
        
        # Создаем изделие
        cursor = self.conn.execute(
            "INSERT INTO products (name, product_no) VALUES (?, ?)",
            ("Тестовое изделие", "TEST-001")
        )
        self.product_id = cursor.lastrowid
        
        # Связываем изделие с контрактом
        self.conn.execute(
            "UPDATE products SET contract_id = ? WHERE id = ?",
            (self.contract_id, self.product_id)
        )
        
        # Создаем вид работ
        cursor = self.conn.execute(
            "INSERT INTO job_types (name, unit, price) VALUES (?, ?, ?)",
            ("Тестовая работа", "час", 1000.0)
        )
        self.job_type_id = cursor.lastrowid
        
        # Создаем работника
        cursor = self.conn.execute(
            "INSERT INTO workers (full_name, personnel_no, dept, position) VALUES (?, ?, ?, ?)",
            ("Тестовый Работник", "TEST-001", "Тестовый отдел", "Тестер")
        )
        self.worker_id = cursor.lastrowid
        
        self.conn.commit()
    
    def test_create_work_order_with_items(self):
        """Тест создания наряда с позициями."""
        # Создаем наряд с позициями
        work_order_data = WorkOrderInput(
            date='01.01.2025',
            product_id=None,
            contract_id=self.contract_id,
            items=[
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=2.0
                ),
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=1.5
                )
            ],
            workers=[
                WorkOrderWorkerInput(
                    worker_id=self.worker_id,
                    worker_name="Тестовый Работник",
                    amount=1000.0
                )
            ],
            extra_product_ids=[self.product_id]
        )
        
        # Создаем наряд
        work_order_id = create_work_order(self.conn, work_order_data)
        assert work_order_id is not None
        assert isinstance(work_order_id, int)
        assert work_order_id > 0
        
        # Проверяем, что позиции сохранились
        items_rows = self.conn.execute(
            "SELECT * FROM work_order_items WHERE work_order_id = ?",
            (work_order_id,)
        ).fetchall()
        
        assert len(items_rows) == 2, f"Ожидалось 2 позиции, получено {len(items_rows)}"
        
        # Проверяем первую позицию
        first_item = items_rows[0]
        assert first_item['job_type_id'] == self.job_type_id
        assert first_item['quantity'] == 2.0
        assert first_item['unit_price'] == 1000.0
        assert first_item['line_amount'] == 2000.0
        
        # Проверяем вторую позицию
        second_item = items_rows[1]
        assert second_item['job_type_id'] == self.job_type_id
        assert second_item['quantity'] == 1.5
        assert second_item['unit_price'] == 1000.0
        assert second_item['line_amount'] == 1500.0
    
    def test_load_work_order_with_items(self):
        """Тест загрузки наряда с позициями."""
        # Сначала создаем наряд
        work_order_data = WorkOrderInput(
            number='НО-2025-002',
            date='02.01.2025',
            department='Цех 2',
            description='Тестовый наряд 2',
            items=[
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=3.0
                )
            ],
            workers=[
                WorkOrderWorkerInput(
                    worker_id=self.worker_id,
                    amount=1500.0
                )
            ],
            extra_product_ids=[str(self.product_id)],
            contract_id=self.contract_id
        )
        
        work_order_id = create_work_order(self.conn, work_order_data)
        
        # Загружаем наряд
        loaded_order = load_work_order(self.conn, work_order_id)
        
        # Проверяем, что позиции загрузились
        assert len(loaded_order.items) == 1, f"Ожидалась 1 позиция, получено {len(loaded_order.items)}"
        
        # Проверяем детали позиции
        item = loaded_order.items[0]
        assert item[0] == self.job_type_id  # job_type_id
        assert item[1] == "Тестовая работа"  # job_name
        assert item[2] == 3.0  # quantity
        assert item[3] == 1000.0  # unit_price
        assert item[4] == 3000.0  # line_amount
    
    def test_work_order_items_count(self):
        """Тест подсчета количества позиций в наряде."""
        # Создаем наряд с несколькими позициями
        work_order_data = WorkOrderInput(
            number='НО-2025-003',
            date='03.01.2025',
            department='Цех 3',
            description='Тестовый наряд 3',
            items=[
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=1.0
                ),
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=2.0
                ),
                WorkOrderItemInput(
                    job_type_id=self.job_type_id,
                    quantity=0.5
                )
            ],
            workers=[
                WorkOrderWorkerInput(
                    worker_id=self.worker_id,
                    amount=2000.0
                )
            ],
            extra_product_ids=[str(self.product_id)],
            contract_id=self.contract_id
        )
        
        work_order_id = create_work_order(self.conn, work_order_data)
        
        # Загружаем наряд
        loaded_order = load_work_order(self.conn, work_order_id)
        
        # Проверяем количество позиций
        assert len(loaded_order.items) == 3, f"Ожидалось 3 позиции, получено {len(loaded_order.items)}"
        
        # Проверяем общую сумму
        total_amount = sum(item[4] for item in loaded_order.items)
        expected_total = 1.0 * 1000.0 + 2.0 * 1000.0 + 0.5 * 1000.0
        assert total_amount == expected_total, f"Ожидалась сумма {expected_total}, получено {total_amount}"
    
    def test_empty_work_order_items(self):
        """Тест наряда без позиций (должен вызывать ошибку)."""
        work_order_data = WorkOrderInput(
            number='НО-2025-004',
            date='04.01.2025',
            department='Цех 4',
            description='Наряд без позиций',
            items=[],  # Пустой список позиций
            workers=[
                WorkOrderWorkerInput(
                    worker_id=self.worker_id,
                    worker_name="Тестовый Работник",
                    amount=1000.0
                )
            ],
            extra_product_ids=[str(self.product_id)],
            contract_id=self.contract_id
        )
        
        # Попытка создания наряда без позиций должна вызвать ошибку
        with pytest.raises(ValueError, match="Наряд должен содержать хотя бы одну строку работ"):
            create_work_order(self.conn, work_order_data)
