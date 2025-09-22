"""
Патчи для CustomTkinter для предотвращения ошибок с недействительными именами команд canvas.
"""

import logging
import tkinter as tk
from typing import Any

logger = logging.getLogger(__name__)


def patch_customtkinter():
    """Применяет патчи к CustomTkinter для предотвращения ошибок canvas."""
    try:
        import customtkinter as ctk
        
        # Патчим базовый класс для безопасной отрисовки
        original_draw = ctk.CTkBaseClass._draw
        
        def safe_draw(self, *args, **kwargs):
            try:
                return original_draw(self, *args, **kwargs)
            except tk.TclError as e:
                error_msg = str(e)
                if "invalid command name" in error_msg or "can't invoke" in error_msg:
                    logger.debug(f"Ignored TclError in _draw: {error_msg}")
                    return
                else:
                    raise e
        
        ctk.CTkBaseClass._draw = safe_draw
        
        # Патчим метод _update_dimensions_event
        if hasattr(ctk.CTkBaseClass, '_update_dimensions_event'):
            original_update_dimensions = ctk.CTkBaseClass._update_dimensions_event
            
            def safe_update_dimensions(self, *args, **kwargs):
                try:
                    return original_update_dimensions(self, *args, **kwargs)
                except tk.TclError as e:
                    error_msg = str(e)
                    if "invalid command name" in error_msg or "can't invoke" in error_msg:
                        logger.debug(f"Ignored TclError in _update_dimensions_event: {error_msg}")
                        return
                    else:
                        raise e
            
            ctk.CTkBaseClass._update_dimensions_event = safe_update_dimensions
        
        logger.info("CustomTkinter patches applied successfully")
        
    except Exception as e:
        logger.warning(f"Failed to apply CustomTkinter patches: {e}")


def patch_tkinter_canvas():
    """Патчим методы canvas для предотвращения ошибок."""
    try:
        # Патчим методы canvas
        original_canvas_find = tk.Canvas.find_withtag
        
        def safe_find_withtag(self, tagOrId):
            try:
                return original_canvas_find(self, tagOrId)
            except tk.TclError as e:
                error_msg = str(e)
                if "invalid command name" in error_msg:
                    logger.debug(f"Ignored TclError in find_withtag: {error_msg}")
                    return ()
                else:
                    raise e
        
        tk.Canvas.find_withtag = safe_find_withtag
        
        # Патчим delete метод
        original_canvas_delete = tk.Canvas.delete
        
        def safe_canvas_delete(self, *args):
            try:
                return original_canvas_delete(self, *args)
            except tk.TclError as e:
                error_msg = str(e)
                if "invalid command name" in error_msg:
                    logger.debug(f"Ignored TclError in canvas delete: {error_msg}")
                    return
                else:
                    raise e
        
        tk.Canvas.delete = safe_canvas_delete
        
        logger.info("Tkinter Canvas patches applied successfully")
        
    except Exception as e:
        logger.warning(f"Failed to apply Tkinter Canvas patches: {e}")


def apply_all_patches():
    """Применяет все доступные патчи."""
    patch_customtkinter()
    patch_tkinter_canvas()
