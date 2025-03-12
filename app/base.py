"""
Базовые классы и утилиты для проекта.
"""
from typing import Dict, Any, List, Optional


class BaseService:
    """Базовый класс сервиса с общими методами"""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_all(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение всех записей из таблицы"""
        query = f"SELECT * FROM {table_name}"
        return self.db.execute_query_fetchall(query)

    def get_by_id(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Получение записи по ID"""
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        result = self.db.execute_query_fetchone(query, (record_id,))
        return result

    def add_record(self, table_name: str, data: Dict[str, Any]) -> int:
        """Добавление новой записи в таблицу"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor = self.db.execute_query(query, tuple(data.values()))
        return cursor.lastrowid if cursor else 0

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Обновление записи в таблице"""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        success = self.db.execute_query(query, tuple(data.values()) + (record_id,))
        return success is not None

    def delete_record(self, table_name: str, record_id: int) -> bool:
        """Удаление записи из таблицы"""
        query = f"DELETE FROM {table_name} WHERE id = ?"
        success = self.db.execute_query(query, (record_id,))
        return success is not None


class BaseForm:
    """Базовый класс для форм"""

    def __init__(self, parent, service):
        self.parent = parent
        self.service = service
        self.setup_ui()

    def setup_ui(self):
        """Абстрактный метод для настройки интерфейса"""
        raise NotImplementedError("Подклассы должны реализовать метод setup_ui")

    def clear(self):
        """Очистка данных в форме"""
        pass

    def save(self):
        """Сохранение данных из формы"""
        pass


class BaseDialog:
    """Базовый класс для диалоговых окон"""

    def __init__(self, parent):
        self.parent = parent
        self.dialog = None

    def show(self):
        """Показ диалогового окна"""
        self.create_dialog()
        self.dialog.wait_window()

    def create_dialog(self):
        """Абстрактный метод для создания диалогового окна"""
        raise NotImplementedError("Подклассы должны реализовать метод create_dialog")

    def validate(self) -> bool:
        """Валидация данных в диалоге"""
        return True

    def on_ok(self):
        """Обработка нажатия кнопки OK"""
        pass

    def on_cancel(self):
        """Обработка нажатия кнопки Отмена"""
        self.dialog.destroy()
