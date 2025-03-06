"""
Конфигурационный модуль приложения для учета сдельной работы сотрудников бригад.
Содержит настройки приложения, пути к файлам и другие константы.
"""

import os
from datetime import datetime
import pathlib

# Корневая директория проекта
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# Директория для хранения данных
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Путь к основной базе данных
DATABASE_PATH = os.path.join(DATA_DIR, "brigade.db")

# Функция для создания пути к резервной копии базы данных
def get_backup_db_path():
    """
    Создает путь для резервной копии базы данных с текущей датой и временем в названии.

    Returns:
        str: Полный путь к файлу резервной копии
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(DATA_DIR, f"brigade_backup_{timestamp}.db")

# Настройки приложения
APP_TITLE = "Учет сдельной работы бригад"
APP_VERSION = "1.0.0"
APP_WIDTH = 1200
APP_HEIGHT = 800

# Настройки для отчетов
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Настройки базы данных
DB_TABLES = {
    "workers": "Сотрудники",
    "work_types": "Виды работ",
    "products": "Изделия",
    "contracts": "Контракты",
    "work_cards": "Карточки работ",
    "work_card_items": "Элементы карточек работ",
    "work_card_workers": "Сотрудники в карточках работ"
}