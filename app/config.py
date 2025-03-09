"""
Конфигурационный модуль приложения для учета сдельной работы сотрудников бригад.
Содержит настройки приложения, пути к файлам и другие константы.
"""

import os
from datetime import datetime
import pathlib
from pathlib import Path

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

"""
Конфигурационный файл приложения.
Содержит настройки путей, параметров базы данных и других глобальных параметров.
"""

# Базовая директория проекта
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Директория для хранения базы данных
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Путь к файлу базы данных
DB_PATH = os.path.join(DATA_DIR, 'brigade_work.db')

# Директория для хранения логов
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Директория для сохранения отчетов
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Название приложения
APP_NAME = "Учет сдельной работы бригад"

# Настройки для отчетов
REPORT_OPTIONS = {
    "company_name": "ООО «Предприятие»",
    "report_title": "Отчет по сдельной работе",
    "report_footer": f"© {APP_NAME} v{APP_VERSION}"
}

# Параметры интерфейса
GUI_SETTINGS = {
    "default_window_width": 1200,
    "default_window_height": 800,
    "min_window_width": 800,
    "min_window_height": 600
}

# Директория для резервных копий
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Тема приложения (light, dark, system)
APP_THEME = 'light'

"""
Формирование имени файла для резервной копии базы данных.
Включает дату и время для уникальности.
str: Имя файла резервной копии (без пути)
"""
# Формируем имя файла с текущей датой и временем
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
def get_backup_filename() -> str:
    """
    Создает имя файла для резервной копии с текущей датой и временем.

    Returns:
        str: Имя файла для резервной копии
    """
    current_time = datetime.now()
    return f"backup_{current_time.strftime('%Y%m%d_%H%M%S')}.db"

