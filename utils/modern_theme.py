"""
Современная тема для CustomTkinter
Убирает разноцветные фоны и окантовки, делает интерфейс более чистым и современным
"""

from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
import logging

logger = logging.getLogger(__name__)

# Современная цветовая схема
MODERN_COLORS = {
    # Основные цвета
    "bg_primary": "#f8f9fa",      # Очень светло-серый фон
    "bg_secondary": "#ffffff",    # Белый фон
    "bg_tertiary": "#e9ecef",     # Светло-серый для выделения
    
    # Текст
    "text_primary": "#212529",    # Темно-серый текст
    "text_secondary": "#6c757d",  # Серый текст
    "text_muted": "#adb5bd",      # Приглушенный текст
    
    # Акценты
    "accent_primary": "#0d6efd",   # Синий
    "accent_success": "#198754",   # Зеленый
    "accent_warning": "#ffc107",   # Желтый
    "accent_danger": "#dc3545",    # Красный
    "accent_info": "#0dcaf0",      # Голубой
    
    # Границы
    "border_light": "#dee2e6",    # Светлая граница
    "border_medium": "#ced4da",   # Средняя граница
    "border_dark": "#adb5bd",     # Темная граница
    
    # Тени и эффекты
    "shadow_light": "#00000010",  # Легкая тень
    "shadow_medium": "#00000020", # Средняя тень
    "shadow_dark": "#00000030",   # Темная тень
    
    # Hover эффекты
    "hover_light": "#f8f9fa",     # Легкий hover
    "hover_medium": "#e9ecef",    # Средний hover
    "hover_dark": "#dee2e6",      # Темный hover
}

# Настройки для разных типов виджетов
WIDGET_STYLES = {
    "button": {
        "fg_color": MODERN_COLORS["bg_secondary"],
        "hover_color": MODERN_COLORS["hover_medium"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 6,
        "text_color": MODERN_COLORS["text_primary"],
    },
    "button_primary": {
        "fg_color": MODERN_COLORS["accent_primary"],
        "hover_color": "#0b5ed7",
        "border_color": MODERN_COLORS["accent_primary"],
        "border_width": 1,
        "corner_radius": 6,
        "text_color": "#ffffff",
    },
    "button_success": {
        "fg_color": MODERN_COLORS["accent_success"],
        "hover_color": "#157347",
        "border_color": MODERN_COLORS["accent_success"],
        "border_width": 1,
        "corner_radius": 6,
        "text_color": "#ffffff",
    },
    "button_danger": {
        "fg_color": MODERN_COLORS["accent_danger"],
        "hover_color": "#b02a37",
        "border_color": MODERN_COLORS["accent_danger"],
        "border_width": 1,
        "corner_radius": 6,
        "text_color": "#ffffff",
    },
    "entry": {
        "fg_color": MODERN_COLORS["bg_secondary"],
        "border_color": MODERN_COLORS["border_medium"],
        "border_width": 1,
        "corner_radius": 6,
        "text_color": MODERN_COLORS["text_primary"],
        "placeholder_text_color": MODERN_COLORS["text_muted"],
    },
    "frame": {
        "fg_color": MODERN_COLORS["bg_secondary"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 8,
    },
    "frame_secondary": {
        "fg_color": MODERN_COLORS["bg_tertiary"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 8,
    },
    "label": {
        "text_color": MODERN_COLORS["text_primary"],
        "fg_color": "transparent",
    },
    "label_secondary": {
        "text_color": MODERN_COLORS["text_secondary"],
        "fg_color": "transparent",
    },
    "label_muted": {
        "text_color": MODERN_COLORS["text_muted"],
        "fg_color": "transparent",
    },
    "tabview": {
        "fg_color": MODERN_COLORS["bg_secondary"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 8,
    },
    "scrollable_frame": {
        "fg_color": MODERN_COLORS["bg_secondary"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 8,
    },
    "progressbar": {
        "fg_color": MODERN_COLORS["accent_primary"],
        "progress_color": MODERN_COLORS["accent_success"],
        "border_color": MODERN_COLORS["border_light"],
        "border_width": 1,
        "corner_radius": 6,
    },
}


def apply_modern_theme():
    """Применить современную тему к приложению"""
    try:
        # Устанавливаем светлую тему
        ctk.set_appearance_mode("light")
        
        # Устанавливаем современную цветовую схему
        ctk.set_default_color_theme("blue")
        
        logger.info("Современная тема применена успешно")
        
    except Exception as exc:
        logger.exception("Ошибка применения современной темы: %s", exc)


def get_widget_style(widget_type: str) -> dict:
    """Получить стиль для указанного типа виджета"""
    return WIDGET_STYLES.get(widget_type, {}).copy()


def configure_widget_style(widget, style_type: str) -> None:
    """Настроить стиль виджета"""
    try:
        style = get_widget_style(style_type)
        if style and hasattr(widget, 'configure'):
            widget.configure(**style)
    except Exception as exc:
        logger.exception("Ошибка настройки стиля виджета: %s", exc)


def create_modern_button(parent, text: str, style_type: str = "button", **kwargs) -> ctk.CTkButton:
    """Создать кнопку с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkButton(parent, text=text, **style)


def create_modern_entry(parent, style_type: str = "entry", **kwargs) -> ctk.CTkEntry:
    """Создать поле ввода с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkEntry(parent, **style)


def create_modern_frame(parent, style_type: str = "frame", **kwargs) -> ctk.CTkFrame:
    """Создать фрейм с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkFrame(parent, **style)


def create_modern_label(parent, text: str, style_type: str = "label", **kwargs) -> ctk.CTkLabel:
    """Создать метку с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkLabel(parent, text=text, **style)


def create_modern_tabview(parent, style_type: str = "tabview", **kwargs) -> ctk.CTkTabview:
    """Создать tabview с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkTabview(parent, **style)


def create_modern_scrollable_frame(parent, style_type: str = "scrollable_frame", **kwargs) -> ctk.CTkScrollableFrame:
    """Создать прокручиваемый фрейм с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkScrollableFrame(parent, **style)


def create_modern_progressbar(parent, style_type: str = "progressbar", **kwargs) -> ctk.CTkProgressBar:
    """Создать прогресс-бар с современным стилем"""
    style = get_widget_style(style_type)
    style.update(kwargs)
    return ctk.CTkProgressBar(parent, **style)


def get_color(color_name: str) -> str:
    """Получить цвет по имени"""
    return MODERN_COLORS.get(color_name, "#000000")


def apply_modern_style_to_existing_widget(widget, style_type: str) -> None:
    """Применить современный стиль к существующему виджету"""
    try:
        style = get_widget_style(style_type)
        
        # Убираем прозрачные цвета
        if "fg_color" in style and style["fg_color"] == "transparent":
            del style["fg_color"]
            
        if style and hasattr(widget, 'configure'):
            widget.configure(**style)
            
    except Exception as exc:
        logger.exception("Ошибка применения стиля к существующему виджету: %s", exc)
