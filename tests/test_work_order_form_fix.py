#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы с отображением позиций в наряде
"""

import sys
import os
import sqlite3
import tempfile
from unittest.mock import Mock, patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work_orders import create_work_order, load_work_order
from services.work_orders import WorkOrderInput, WorkOrderItemInput, WorkOrderWorkerInput
from db import queries as q
from db.schema import initialize_schema


def test_work_order_items_fix():
    """Тест исправления проблемы с позициями в наряде"""
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        # Инициализируем схему
        conn = sqlite3.connect(db_path)
        initialize_schema(conn)
        conn.commit()
        
        # Добавляем тестовые данные
        cursor = conn.execute("INSERT INTO contracts (code, name) VALUES (?, ?)", ("TEST-001", "Тестовый контракт"))
        contract_id = cursor.lastrowid
        
        cursor = conn.execute("INSERT INTO job_types (name, unit, price) VALUES (?, ?, ?)", ("Тестовая работа", "шт", 100.0))
        job_type_id = cursor.lastrowid
        
        cursor = conn.execute("INSERT INTO products (product_no, name) VALUES (?, ?)", ("P001", "Тестовое изделие"))
        product_id = cursor.lastrowid
        
        cursor = conn.execute("INSERT INTO workers (full_name, personnel_no) VALUES (?, ?)", ("Тестовый работник", "W001"))
        worker_id = cursor.lastrowid
        
        conn.commit()
        
        # Создаем наряд с позициями
        work_order_data = WorkOrderInput(
            date="01.01.2025",
            contract_id=contract_id,
            product_id=product_id,
            items=[
                WorkOrderItemInput(
                    job_type_id=job_type_id,
                    quantity=2.0
                )
            ],
            workers=[
                WorkOrderWorkerInput(
                    worker_id=worker_id,
                    worker_name="Тестовый работник",
                    amount=200.0
                )
            ],
            extra_product_ids=[product_id]
        )
        
        # Создаем наряд
        work_order_id = create_work_order(conn, work_order_data)
        print(f"✅ Создан наряд с ID: {work_order_id}")
        
        # Загружаем наряд
        loaded_order = load_work_order(conn, work_order_id)
        print(f"✅ Загружен наряд с {len(loaded_order.items)} позициями")
        
        # Проверяем, что позиции загружены корректно
        assert len(loaded_order.items) == 1, f"Ожидалось 1 позиция, получено {len(loaded_order.items)}"
        
        item = loaded_order.items[0]
        assert item[0] == job_type_id, f"Неправильный ID вида работ: {item[0]} != {job_type_id}"
        assert item[1] == "Тестовая работа", f"Неправильное название: {item[1]}"
        assert item[2] == 2.0, f"Неправильное количество: {item[2]}"
        assert item[3] == 100.0, f"Неправильная цена: {item[3]}"
        assert item[4] == 200.0, f"Неправильная сумма: {item[4]}"
        
        print("✅ Все проверки пройдены!")
        print(f"   - Количество позиций: {len(loaded_order.items)}")
        print(f"   - Название работы: {item[1]}")
        print(f"   - Количество: {item[2]}")
        print(f"   - Цена: {item[3]}")
        print(f"   - Сумма: {item[4]}")
        
    finally:
        conn.close()
        os.unlink(db_path)


if __name__ == "__main__":
    test_work_order_items_fix()
