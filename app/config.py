"""
Конфигурационный модуль приложения для учета сдельной работы сотрудников бригад.
Содержит настройки приложения, пути к файлам и другие константы.
"""

import os
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(os.getcwd())  # Текущая директория, из которой запущена программа

# Корневая директория проекта
# ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
ROOT_DIR = CURRENT_DIR

# Директория для хранения данных
DATA_DIR = Path(ROOT_DIR) / "data"
DATA_DIR.mkdir(exist_ok=True)  # Создаем директорию, если она не существует

# Путь к основной базе данных
DATABASE_PATH = DATA_DIR / "brigade.db"

# Функция для создания пути к резервной копии базы данных
def get_backup_db_path():
    """
    Создает путь для резервной копии базы данных с текущей датой и временем в названии.

    Returns:
        str: Полный путь к файлу резервной копии
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DATA_DIR / f"brigade_backup_{timestamp}.db"


# Настройки приложения
APP_TITLE = "Учет сдельной работы бригад РМЗ"
APP_VERSION = "1.0.0"
APP_WIDTH = 1200
APP_HEIGHT = 800

# Настройки для отчетов
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)  # Создаем директорию, если она не существует

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
# BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = CURRENT_DIR

# Директория для хранения базы данных
DATA_DIR = Path(BASE_DIR) / "data"
DATA_DIR.mkdir(exist_ok=True)  # Создаем директорию, если она не существует

# Путь к файлу базы данных
DB_PATH = DATA_DIR / "brigade_work.db"

# Директория для хранения логов
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Директория для сохранения отчетов
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Название приложения
APP_NAME = "Учет сдельной работы бригад РМЗ 1.0"

# Настройки для отчетов
REPORT_OPTIONS = {
    "company_name": "АО «МАЛМЫЖСКИЙ РЕМЗАВОД»",
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
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

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

