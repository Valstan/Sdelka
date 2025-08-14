from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import customtkinter as ctk

from utils.user_prefs import UserPrefs


def apply_user_fonts(root: tk.Misc, prefs: UserPrefs) -> None:
    # Настройка базовых шрифтов Tk
    try:
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                f = tkfont.nametofont(name)
                f.configure(size=prefs.ui_font_size)
            except Exception:
                pass
    except Exception:
        pass

    # Настройка Treeview
    try:
        style = ttk.Style(root)
        # Фон/тема не меняем, только шрифты/высоту строки
        list_font = tkfont.Font(size=prefs.list_font_size)
        heading_font = tkfont.Font(size=max(prefs.ui_font_size, prefs.list_font_size), weight="bold")
        row_h = int(prefs.list_font_size * 1.8)
        style.configure("Treeview", font=list_font, rowheight=row_h)
        style.configure("Treeview.Heading", font=heading_font)
    except Exception:
        pass

    # Масштабирование CTk
    try:
        scale = max(0.6, prefs.ui_font_size / 12.0)
        ctk.set_widget_scaling(scale)
    except Exception:
        pass

    # Компактный layout для больших шрифтов
    try:
        compact_layout(root, prefs)
    except Exception:
        pass

    # Уведомить подписчиков, что шрифты/масштаб изменились
    try:
        root.event_generate("<<UIFontsChanged>>", when="tail")
    except Exception:
        pass


def compact_layout(root: tk.Misc, prefs: UserPrefs) -> None:
    """Уменьшает внешние/внутренние отступы для pack/grid пропорционально размеру шрифта.
    База: ui_font_size=12 -> factor=1.0, больше шрифт -> factor<1.0. Отступы не увеличиваем.
    """
    factor = min(1.0, 12.0 / max(1.0, float(prefs.ui_font_size)))

    def adjust_widget(widget: tk.Misc):
        # pack
        try:
            info = widget.pack_info()
            # Сохраняем оригиналы один раз
            if not hasattr(widget, "_orig_pack_padx"):
                widget._orig_pack_padx = int(info.get("padx", 0)) if str(info.get("padx", "")).isdigit() else info.get("padx", 0)
            if not hasattr(widget, "_orig_pack_pady"):
                widget._orig_pack_pady = int(info.get("pady", 0)) if str(info.get("pady", "")).isdigit() else info.get("pady", 0)
            ox = widget._orig_pack_padx
            oy = widget._orig_pack_pady
            nx = int(ox * factor) if isinstance(ox, int) else ox
            ny = int(oy * factor) if isinstance(oy, int) else oy
            widget.pack_configure(padx=nx, pady=ny)
        except Exception:
            pass
        # grid
        try:
            info = widget.grid_info()
            if info:
                if not hasattr(widget, "_orig_grid_padx"):
                    widget._orig_grid_padx = int(info.get("padx", 0)) if str(info.get("padx", "")).isdigit() else info.get("padx", 0)
                if not hasattr(widget, "_orig_grid_pady"):
                    widget._orig_grid_pady = int(info.get("pady", 0)) if str(info.get("pady", "")).isdigit() else info.get("pady", 0)
                ox = widget._orig_grid_padx
                oy = widget._orig_grid_pady
                nx = int(ox * factor) if isinstance(ox, int) else ox
                ny = int(oy * factor) if isinstance(oy, int) else oy
                widget.grid_configure(padx=nx, pady=ny)
        except Exception:
            pass
        # Рекурсия
        try:
            for child in widget.winfo_children():
                adjust_widget(child)
        except Exception:
            pass

    adjust_widget(root)