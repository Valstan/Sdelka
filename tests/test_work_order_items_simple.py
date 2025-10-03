#!/usr/bin/env python3
"""
Простой тест для проверки сохранения и загрузки позиций наряда
"""

import sys
import os
import sqlite3
import tempfile

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work_orders import create_work_order, load_work_order, WorkOrderInput, WorkOrderItemInput, WorkOrderWorkerInput
from db.schema import initialize_schema


def test_work_order_items_save_and_load():
    """Простой тест для проверки сохранения и загрузки позиций нарядов."""
    # Создаем временную базу данных
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    
    try:
        # Создаем тестовую базу данных
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        initialize_schema(conn)
        
        # Создаем тестовые данные
        # Контракт
        cursor = conn.execute(
            "INSERT INTO contracts (code, name) VALUES (?, ?)",
            ("TEST-001", "Тестовый контракт")
        )
        contract_id = cursor.lastrowid
        
        # Изделие
        cursor = conn.execute(
            "INSERT INTO products (name, product_no) VALUES (?, ?)",
            ("Тестовое изделие", "TEST-001")
        )
        product_id = cursor.lastrowid
        
        # Связываем изделие с контрактом
        conn.execute(
            "UPDATE products SET contract_id = ? WHERE id = ?",
            (contract_id, product_id)
        )
        
        # Вид работ
        cursor = conn.execute(
            "INSERT INTO job_types (name, unit, price) VALUES (?, ?, ?)",
            ("Тестовая работа", "час", 1000.0)
        )
        job_type_id = cursor.lastrowid
        
        # Работник
        cursor = conn.execute(
            "INSERT INTO workers (full_name, personnel_no, dept, position) VALUES (?, ?, ?, ?)",
            ("Тестовый Работник", "TEST-001", "Тестовый отдел", "Тестер")
        )
        worker_id = cursor.lastrowid
        
        conn.commit()
        
        # Создаем наряд с позициями
        work_order_data = WorkOrderInput(
            date='01.01.2025',
            product_id=None,
            contract_id=contract_id,
            items=[
                WorkOrderItemInput(
                    job_type_id=job_type_id,
                    quantity=2.0
                ),
                WorkOrderItemInput(
                    job_type_id=job_type_id,
                    quantity=1.5
                )
            ],
            workers=[
                WorkOrderWorkerInput(
                    worker_id=worker_id,
                    worker_name="Тестовый Работник",
                    amount=1000.0
                )
            ],
            extra_product_ids=[product_id]
        )
        
        # Создаем наряд
        work_order_id = create_work_order(conn, work_order_data)
        assert work_order_id is not None
        assert isinstance(work_order_id, int)
        assert work_order_id > 0
        
        # Проверяем, что позиции сохранились в базе данных
        items_rows = conn.execute(
            "SELECT * FROM work_order_items WHERE work_order_id = ?",
            (work_order_id,)
        ).fetchall()
        
        print(f"Количество позиций в БД: {len(items_rows)}")
        for i, item in enumerate(items_rows):
            print(f"Позиция {i+1}: job_type_id={item['job_type_id']}, quantity={item['quantity']}, line_amount={item['line_amount']}")
        
        assert len(items_rows) == 2, f"Ожидалось 2 позиции, получено {len(items_rows)}"
        
        # Проверяем первую позицию
        first_item = items_rows[0]
        assert first_item['job_type_id'] == job_type_id
        assert first_item['quantity'] == 2.0
        assert first_item['unit_price'] == 1000.0
        assert first_item['line_amount'] == 2000.0
        
        # Проверяем вторую позицию
        second_item = items_rows[1]
        assert second_item['job_type_id'] == job_type_id
        assert second_item['quantity'] == 1.5
        assert second_item['unit_price'] == 1000.0
        assert second_item['line_amount'] == 1500.0
        
        # Загружаем наряд и проверяем, что позиции загрузились
        loaded_order = load_work_order(conn, work_order_id)
        
        print(f"Количество позиций в загруженном наряде: {len(loaded_order.items)}")
        for i, item in enumerate(loaded_order.items):
            print(f"Загруженная позиция {i+1}: job_type_id={item[0]}, job_name={item[1]}, quantity={item[2]}, line_amount={item[4]}")
        
        assert len(loaded_order.items) == 2, f"Ожидалось 2 позиции в загруженном наряде, получено {len(loaded_order.items)}"
        
        # Проверяем детали первой позиции
        first_loaded_item = loaded_order.items[0]
        assert first_loaded_item[0] == job_type_id  # job_type_id
        assert first_loaded_item[1] == "Тестовая работа"  # job_name
        assert first_loaded_item[2] == 2.0  # quantity
        assert first_loaded_item[3] == 1000.0  # unit_price
        assert first_loaded_item[4] == 2000.0  # line_amount
        
        # Проверяем детали второй позиции
        second_loaded_item = loaded_order.items[1]
        assert second_loaded_item[0] == job_type_id  # job_type_id
        assert second_loaded_item[1] == "Тестовая работа"  # job_name
        assert second_loaded_item[2] == 1.5  # quantity
        assert second_loaded_item[3] == 1000.0  # unit_price
        assert second_loaded_item[4] == 1500.0  # line_amount
        
        print("✅ Тест прошел успешно! Позиции сохраняются и загружаются правильно.")
        
    finally:
        # Очистка
        if 'conn' in locals():
            conn.close()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_work_order_items_save_and_load()
