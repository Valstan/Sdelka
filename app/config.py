"""
Конфигурационный модуль приложения для учета сдельной работы сотрудников.
Содержит настройки приложения, пути к файлам и другим ресурсам.
"""
import os
from pathlib import Path

# Основные настройки приложения
APP_TITLE = "Учет сдельной работы бригад РМЗ"
APP_VERSION = "1.0.0"
APP_WIDTH = 1200
APP_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Тема интерфейса (light, dark, system)
APP_THEME = 'dark'

# Настройки базы данных
DB_SETTINGS = {
    'database_path': 'data/sdelka_base.db',
    'create_backup_on_start': True
}

# Настройки отчетов
REPORT_SETTINGS = {
    'output_dir': 'data/reports',
    'default_filename_prefix': 'report',
    'supported_formats': ['excel', 'html', 'pdf']
}

# Настройки логирования
LOGGING_SETTINGS = {
    'log_dir': 'data/logs',
    'log_file_prefix': 'app_log',
    'log_level': 'INFO'
}

# Пути к директориям
DIRECTORIES = {
    'base': Path(os.getcwd()),
    'data': Path(os.getcwd()) / "data",
    'reports': Path(os.getcwd()) / "data" / "reports",
    'logs': Path(os.getcwd()) / "data" / "logs",
    'backups': Path(os.getcwd()) / "data" / "backups"
}

# Настройки для работы с датами
DATE_FORMATS = {
    'default': '%Y-%m-%d',
    'display': '%d.%m.%Y',
    'log': '%Y%m%d_%H%M%S'
}

# Настройки интерфейса
UI_SETTINGS = {
    'default_font': ('Roboto', 12),
    'header_font': ('Roboto', 12),
    'primary_color': '#1976D2',
    'primary_dark': '#0D47A1',
    'primary_light': '#BBDEFB',
    'secondary_color': '#FF9800',
    'secondary_dark': '#F57C00',
    'background_color': '#F5F5F5',
    'card_color': '#FFFFFF',
    'text_color': '#212121',
    'text_secondary': '#757575',
    'error_color': '#F44336',
    'success_color': '#4CAF50',
    'warning_color': '#FFC107',
    'button_style': {
        'fg_color': '#1976D2',
        'hover_color': '#0D47A1',
        'corner_radius': 6,
        'font': ('Roboto', 12),
        'text_color': '#FFFFFF'
    },
    'card_frame': {
        'fg_color': '#FFFFFF',
        'corner_radius': 8,
        'border_width': 1,
        'border_color': '#9E9E9E'
    },
    'header_style': {
        'text_color': '#1976D2',
        'font': ('Roboto', 16, 'bold')
    },
    'label_style': {
        'text_color': '#212121',
        'font': ('Roboto', 12)
    },
    'table_style': {
        'row_height': 28,
        'font': ('Roboto', 10),
        'header_font': ('Roboto', 11, 'bold'),
        'selected_color': '#BBDEFB'
    }
}

# Инициализация директорий
for dir_path in DIRECTORIES.values():
    dir_path.mkdir(exist_ok=True)
