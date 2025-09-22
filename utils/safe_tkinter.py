"""
Утилиты для безопасной работы с Tkinter и CustomTkinter виджетами.
Обрабатывает ошибки, связанные с недействительными именами команд canvas.
"""

import logging
import tkinter as tk
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_widget_operation(func: Callable[..., T], *args, **kwargs) -> T | None:
    """
    Безопасно выполняет операцию с виджетом, игнорируя TclError с недействительными именами команд.
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        **kwargs: Ключевые аргументы функции
        
    Returns:
        Результат функции или None в случае ошибки
    """
    try:
        return func(*args, **kwargs)
    except tk.TclError as e:
        error_msg = str(e)
        if "invalid command name" in error_msg:
            logger.debug(f"Ignored TclError (invalid command): {error_msg}")
            return None
        elif "can't invoke" in error_msg:
            logger.debug(f"Ignored TclError (can't invoke): {error_msg}")
            return None
        else:
            logger.warning(f"TclError not handled: {error_msg}")
            raise e
    except Exception as e:
        logger.error(f"Unexpected error in widget operation: {e}")
        raise e


def safe_configure(widget: Any, **kwargs) -> bool:
    """
    Безопасно конфигурирует виджет CustomTkinter.
    
    Args:
        widget: Виджет для конфигурации
        **kwargs: Параметры конфигурации
        
    Returns:
        True если конфигурация успешна, False иначе
    """
    try:
        widget.configure(**kwargs)
        return True
    except tk.TclError as e:
        error_msg = str(e)
        if "invalid command name" in error_msg or "can't invoke" in error_msg:
            logger.debug(f"Ignored TclError in configure: {error_msg}")
            return False
        else:
            logger.warning(f"TclError in configure: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in configure: {e}")
        return False


def safe_draw(widget: Any) -> bool:
    """
    Безопасно вызывает метод _draw виджета CustomTkinter.
    
    Args:
        widget: Виджет для отрисовки
        
    Returns:
        True если отрисовка успешна, False иначе
    """
    if not hasattr(widget, '_draw'):
        return False
        
    return safe_widget_operation(widget._draw) is not None


def safe_pack(widget: Any, **kwargs) -> bool:
    """
    Безопасно упаковывает виджет.
    
    Args:
        widget: Виджет для упаковки
        **kwargs: Параметры pack
        
    Returns:
        True если упаковка успешна, False иначе
    """
    return safe_widget_operation(widget.pack, **kwargs) is not None


def safe_grid(widget: Any, **kwargs) -> bool:
    """
    Безопасно размещает виджет в сетке.
    
    Args:
        widget: Виджет для размещения
        **kwargs: Параметры grid
        
    Returns:
        True если размещение успешно, False иначе
    """
    return safe_widget_operation(widget.grid, **kwargs) is not None


def safe_place(widget: Any, **kwargs) -> bool:
    """
    Безопасно размещает виджет в абсолютных координатах.
    
    Args:
        widget: Виджет для размещения
        **kwargs: Параметры place
        
    Returns:
        True если размещение успешно, False иначе
    """
    return safe_widget_operation(widget.place, **kwargs) is not None


def safe_destroy(widget: Any) -> bool:
    """
    Безопасно уничтожает виджет.
    
    Args:
        widget: Виджет для уничтожения
        
    Returns:
        True если уничтожение успешно, False иначе
    """
    if widget is None:
        return True
        
    try:
        widget.destroy()
        return True
    except tk.TclError as e:
        error_msg = str(e)
        if "invalid command name" in error_msg or "can't invoke" in error_msg:
            logger.debug(f"Ignored TclError in destroy: {error_msg}")
            return False
        else:
            logger.warning(f"TclError in destroy: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in destroy: {e}")
        return False
