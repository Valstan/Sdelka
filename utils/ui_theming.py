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