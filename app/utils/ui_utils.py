"""
File: app/utils/ui_utils.py
Настройки и утилиты для работы с интерфейсом.
"""

import os
from pathlib import Path
from typing import Any, Dict
from datetime import date

# Конфигурация UI
UI_SETTINGS = {
    "form_width": 600,
    "form_height": 400,
    "row_height": 28,
    "label_style": {
        "text_color": "#212121",
        "font": ("Roboto", 12)
    },
    "header_style": {
        "text_color": "#1976D2",
        "font": ("Roboto", 16, "bold")
    },
    "button_style": {
        "fg_color": "#1976D2",
        "hover_color": "#0D47A1",
        "text_color": "#FFFFFF",
        "corner_radius": 6,
        "font": ("Roboto", 12),
        "width": 120,
        "height": 30
    },
    "card_frame": {
        "fg_color": "#FFFFFF",
        "corner_radius": 8,
        "border_width": 1,
        "border_color": "#9E9E9E"
    },
    "error_color": "#D32F2F",
    "error_hover": "#B71C1C"
}

# Форматы дат
DATE_FORMATS = {
    "default": "%Y-%m-%d",
    "ui": "%d.%m.%Y",
    "export": "%Y%m%d_%H%M%S"
}

# Директории проекта
DIRECTORIES = {
    "data": Path("data"),
    "backups": Path("backups"),
    "exports": Path("exports"),
    "templates": Path("templates"),
    "logs": Path("logs"),
    "migrations": Path("migrations")
}

# Инициализация директорий
for dir_path in DIRECTORIES.values():
    dir_path.mkdir(exist_ok=True)

# Путь к иконке приложения
ICON_PATH = "resources/app_icon.ico" if os.path.exists("resources/app_icon.ico") else None