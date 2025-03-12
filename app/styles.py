"""
Стили для GUI приложения.
Определяет цветовую схему и стили виджетов.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Цветовая схема приложения
COLOR_SCHEME = {
    "primary": "#1976D2",         # Основной цвет
    "primary_dark": "#0D47A1",    # Темный вариант основного цвета
    "primary_light": "#BBDEFB",   # Светлый вариант основного цвета
    "secondary": "#FF9800",       # Дополнительный цвет
    "secondary_dark": "#F57C00",  # Темный вариант дополнительного цвета
    "background": "#F5F5F5",      # Фон приложения
    "card": "#FFFFFF",            # Фон карточек и форм
    "text": "#212121",            # Основной цвет текста
    "text_secondary": "#757575",  # Вторичный цвет текста
    "error": "#F44336",           # Цвет ошибок
    "success": "#4CAF50",         # Цвет успеха
    "warning": "#FFC107",         # Цвет предупреждений
    "black": "#000000",           # Чёрный
    "white": "#FFFFFF",           # Белый
    "gray": "#9E9E9E"             # Серый
}

# Стили для кнопок
BUTTON_STYLE = {
    "fg_color": COLOR_SCHEME["primary"],
    "hover_color": COLOR_SCHEME["primary_dark"],
    "corner_radius": 6,
    "font": ("Roboto", 12),
    "text_color": COLOR_SCHEME["white"]
}

# Стили для текстовых полей
ENTRY_STYLE = {
    "fg_color": COLOR_SCHEME["white"],
    "border_color": COLOR_SCHEME["primary_light"],
    "corner_radius": 6,
    "font": ("Roboto", 12)
}

# Стили для фреймов
FRAME_STYLE = {
    "fg_color": COLOR_SCHEME["card"],
    "corner_radius": 8,
    "border_width": 1,
    "border_color": COLOR_SCHEME["gray"]
}

# Стили для меток
LABEL_STYLE = {
    "text_color": COLOR_SCHEME["text"],
    "font": ("Roboto", 12)
}

# Стили для заголовков
HEADER_STYLE = {
    "text_color": COLOR_SCHEME["primary"],
    "font": ("Roboto", 16, "bold")
}

def init_app_styles():
    """
    Инициализация стилей приложения.
    Настраивает стили для CustomTkinter и ttk виджетов.
    """
    # Настройка темы для CustomTkinter
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Настройка стилей для ttk виджетов (таблицы, прокрутки)
    style = ttk.Style()

    # Стиль для Treeview (таблиц)
    style.configure(
        "Treeview",
        background=COLOR_SCHEME["card"],
        foreground=COLOR_SCHEME["text"],
        rowheight=28,
        fieldbackground=COLOR_SCHEME["card"],
        font=("Roboto", 10)
    )

    # Стиль для заголовков Treeview
    style.configure(
        "Treeview.Heading",
        background=COLOR_SCHEME["primary_light"],
        foreground=COLOR_SCHEME["text"],
        font=("Roboto", 11, "bold")
    )

    # Стиль для выделенных строк
    style.map(
        "Treeview",
        background=[("selected", COLOR_SCHEME["primary_light"])],
        foreground=[("selected", COLOR_SCHEME["primary_dark"])]
    )

    # Стиль для полос прокрутки
    style.configure(
        "Vertical.TScrollbar",
        background=COLOR_SCHEME["card"],
        arrowcolor=COLOR_SCHEME["primary"],
        bordercolor=COLOR_SCHEME["background"],
        troughcolor=COLOR_SCHEME["background"]
    )

    style.configure(
        "Horizontal.TScrollbar",
        background=COLOR_SCHEME["card"],
        arrowcolor=COLOR_SCHEME["primary"],
        bordercolor=COLOR_SCHEME["background"],
        troughcolor=COLOR_SCHEME["background"]
    )
