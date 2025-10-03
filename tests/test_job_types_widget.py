import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from gui.widgets.unified_list_widget import create_job_types_list, ListConfig
from unittest.mock import Mock, patch


def test_job_types_widget():
    """Тест виджета видов работ."""
    # Создаем корневое окно
    root = ctk.CTk()
    root.withdraw()  # Скрываем окно
    
    try:
        # Создаем виджет видов работ
        job_types_widget = create_job_types_list(root)
        
        # Проверяем, что виджет создался
        assert job_types_widget is not None
        
        # Проверяем, что метод get_items_data существует
        assert hasattr(job_types_widget, 'get_items_data')
        
        # Проверяем, что изначально список пустой
        items_data = job_types_widget.get_items_data()
        print(f"Изначальное количество элементов: {len(items_data)}")
        
        # Добавляем тестовый элемент
        job_types_widget.add_item(1, "Тестовая работа")
        
        # Проверяем, что элемент добавился
        items_data = job_types_widget.get_items_data()
        print(f"Количество элементов после добавления: {len(items_data)}")
        print(f"Данные элементов: {items_data}")
        
        # Фильтруем пустые элементы (с пустым именем)
        valid_items = [item for item in items_data if item['name'].strip()]
        print(f"Количество валидных элементов: {len(valid_items)}")
        
        assert len(valid_items) == 1
        assert valid_items[0]['id'] == 1
        assert valid_items[0]['name'] == "Тестовая работа"
        
        print("✅ Тест виджета видов работ прошел успешно!")
        
    finally:
        root.destroy()


if __name__ == "__main__":
    test_job_types_widget()
