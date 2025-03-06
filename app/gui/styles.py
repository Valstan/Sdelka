"""
Модуль содержит стили и настройки внешнего вида для GUI приложения.
"""
import customtkinter as ctk
from typing import Dict, Any

# Цветовая схема приложения
COLOR_SCHEME = {
    "primary": "#1E88E5",       # Основной цвет
    "primary_dark": "#1565C0",  # Темный вариант основного цвета
    "primary_light": "#64B5F6", # Светлый вариант основного цвета
    "secondary": "#FF8F00",     # Дополнительный цвет
    "success": "#4CAF50",       # Цвет успеха
    "warning": "#FFC107",       # Цвет предупреждения
    "error": "#F44336",         # Цвет ошибки
    "text": "#212121",          # Основной цвет текста
    "text_light": "#757575",    # Светлый цвет текста
    "background": "#F5F5F5",    # Фон приложения
    "card": "#FFFFFF",          # Фон карточек
    "border": "#E0E0E0"         # Цвет границ
}

# Общие настройки для заголовков
HEADER_STYLE = {
    "font": ("Roboto", 18, "bold"),
    "fg_color": "transparent",
    "text_color": COLOR_SCHEME["primary"]
}

# Общие настройки для надписей
LABEL_STYLE = {
    "font": ("Roboto", 12),
    "fg_color": "transparent",
    "text_color": COLOR_SCHEME["text"]
}

# Общие настройки для кнопок
BUTTON_STYLE = {
    "font": ("Roboto", 12),
    "fg_color": COLOR_SCHEME["primary"],
    "hover_color": COLOR_SCHEME["primary_dark"],
    "corner_radius": 6,
    "border_width": 0
}

# Настройки для кнопок отмены/удаления
BUTTON_DANGER_STYLE = {
    **BUTTON_STYLE,
    "fg_color": COLOR_SCHEME["error"],
    "hover_color": "#D32F2F"  # Темный красный
}

# Настройки для кнопок подтверждения/сохранения
BUTTON_SUCCESS_STYLE = {
    **BUTTON_STYLE,
    "fg_color": COLOR_SCHEME["success"],
    "hover_color": "#388E3C"  # Темный зеленый
}

# Настройки для полей ввода
ENTRY_STYLE = {
    "font": ("Roboto", 12),
    "fg_color": COLOR_SCHEME["card"],
    "text_color": COLOR_SCHEME["text"],
    "border_color": COLOR_SCHEME["border"],
    "border_width": 1,
    "corner_radius": 6
}

# Настройки для выпадающих списков
COMBOBOX_STYLE = {
    "font": ("Roboto", 12),
    "fg_color": COLOR_SCHEME["card"],
    "text_color": COLOR_SCHEME["text"],
    "dropdown_fg_color": COLOR_SCHEME["card"],
    "dropdown_text_color": COLOR_SCHEME["text"],
    "dropdown_hover_color": COLOR_SCHEME["primary_light"],
    "border_color": COLOR_SCHEME["border"],
    "button_color": COLOR_SCHEME["primary"],
    "button_hover_color": COLOR_SCHEME["primary_dark"],
    "corner_radius": 6,
    "border_width": 1
}

# Настройки для таблиц
TABLE_STYLE = {
    "heading_font": ("Roboto", 12, "bold"),
    "heading_bg": COLOR_SCHEME["primary_light"],
    "heading_fg": COLOR_SCHEME["text"],
    "row_bg_even": COLOR_SCHEME["card"],
    "row_bg_odd": COLOR_SCHEME["background"],
    "row_fg": COLOR_SCHEME["text"],
    "selected_bg": COLOR_SCHEME["primary_light"],
    "selected_fg": COLOR_SCHEME["text"]
}

# Настройки для фреймов
FRAME_STYLE = {
    "fg_color": COLOR_SCHEME["card"],
    "corner_radius": 10,
    "border_width": 1,
    "border_color": COLOR_SCHEME["border"]
}

# Настройки для вкладок
TAB_STYLE = {
    "fg_color": COLOR_SCHEME["background"],
    "text_color": COLOR_SCHEME["text"],
    "hover_color": COLOR_SCHEME["primary_light"],
    "corner_radius": 6
}

# Функция для применения стиля к виджету
def apply_style(widget: ctk.CTkBaseClass, style: Dict[str, Any]) -> None:
    """
    Применяет указанный стиль к виджету.

    Args:
        widget: Виджет для стилизации
        style: Словарь с параметрами стиля
    """
    for key, value in style.items():
        try:
            widget.configure(**{key: value})
        except Exception:
            # Некоторые параметры могут не поддерживаться конкретным виджетом
            pass

# Инициализация стилей для всего приложения
def init_app_styles(appearance_mode: str = "light") -> None:
    """
    Инициализация стилей приложения.

    Args:
        appearance_mode: Режим оформления (light/dark)
    """
    ctk.set_appearance_mode(appearance_mode)
    ctk.set_default_color_theme("blue")  # Базовая тема, которую мы будем кастомизировать