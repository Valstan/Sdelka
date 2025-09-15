from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from utils.runtime_mode import is_readonly


import logging


def guard_readonly(action: str = "операция") -> bool:
    """Return True if allowed, False if blocked due to readonly. Shows a warning.

    Example:
        if not guard_readonly("сохранение"):
            return
    """
    if is_readonly():
        try:
            messagebox.showwarning(
                "Режим 'Просмотр'",
                f"{action.capitalize()} недоступно в режиме 'Просмотр'.",
            )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        return False
    return True


def disable_when_readonly(*widgets: ctk.CTkBaseClass) -> None:
    """Disable given widgets when readonly mode is active."""
    if is_readonly():
        for w in widgets:
            try:
                w.configure(state="disabled")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
