from __future__ import annotations

import datetime as dt
import customtkinter as ctk
from tkcalendar import Calendar

from config.settings import CONFIG


class DatePicker(ctk.CTkToplevel):
    def __init__(self, master, initial: str | None, on_pick):
        super().__init__(master)
        self.title("Выбор даты")
        self.resizable(False, False)
        self.on_pick = on_pick
        self.attributes("-topmost", True)

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
        self.calendar.pack(padx=10, pady=10)

        btns = ctk.CTkFrame(self)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btns, text="ОК", command=self._ok).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Отмена", command=self._cancel).pack(side="left", padx=5)

    def _ok(self):
        date_str = self.calendar.get_date()  # already dd.mm.yyyy
        self.on_pick(date_str)
        self.destroy()

    def _cancel(self):
        self.destroy()