from __future__ import annotations

import datetime as dt
import customtkinter as ctk
from tkcalendar import Calendar

from config.settings import CONFIG


class DatePicker(ctk.CTkToplevel):
    def __init__(self, master, initial: str | None, on_pick, anchor: ctk.CTkEntry | None = None, close_on_focus_out: bool = True):
        super().__init__(master)
        self.title("Выбор даты")
        self.resizable(False, False)
        self.on_pick = on_pick
        self.attributes("-topmost", True)
        self.overrideredirect(True)  # без системной рамки для эффекта выпадающего меню

        # Parse initial date
        selected_date = None
        if initial:
            try:
                day, month, year = map(int, initial.split("."))
                selected_date = dt.date(year, month, day)
            except Exception:
                selected_date = dt.date.today()
        else:
            selected_date = dt.date.today()

        self.calendar = Calendar(
            self,
            selectmode="day",
            year=selected_date.year,
            month=selected_date.month,
            day=selected_date.day,
            date_pattern="dd.mm.yyyy",
            locale="ru_RU",
        )
        self.calendar.pack(padx=1, pady=1)

        if anchor is not None:
            try:
                x = anchor.winfo_rootx()
                y = anchor.winfo_rooty() + anchor.winfo_height()
                self.geometry(f"+{x}+{y}")
            except Exception:
                pass

        if close_on_focus_out:
            self.bind("<FocusOut>", lambda e: self.destroy())

        # Перехватываем клики вне окна
        self.grab_set()

        # Клик по дате
        self.calendar.bind("<<CalendarSelected>>", self._on_select)

    def _on_select(self, _evt=None):
        date_str = self.calendar.get_date()  # already dd.mm.yyyy
        self.on_pick(date_str)
        self.destroy()