from __future__ import annotations

import customtkinter as ctk

from app.gui.views.common import BaseView
from app.services.workers_service import WorkersService


class WorkersView(BaseView):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.service = WorkersService()
        self._add_section_title("Работники")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="new", padx=12, pady=6)

        self.last_name = ctk.CTkEntry(form, placeholder_text="Фамилия")
        self.first_name = ctk.CTkEntry(form, placeholder_text="Имя")
        self.middle_name = ctk.CTkEntry(form, placeholder_text="Отчество")
        add_btn = ctk.CTkButton(form, text="Добавить", command=self._on_add)

        self.last_name.grid(row=0, column=0, padx=6, pady=6)
        self.first_name.grid(row=0, column=1, padx=6, pady=6)
        self.middle_name.grid(row=0, column=2, padx=6, pady=6)
        add_btn.grid(row=0, column=3, padx=6, pady=6)

        self.listbox = ctk.CTkTextbox(self, height=400)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self._refresh()

    def _on_add(self) -> None:
        ln = self.last_name.get().strip()
        fn = self.first_name.get().strip()
        mn = self.middle_name.get().strip() or None
        if not ln or not fn:
            return
        self.service.create_worker(last_name=ln, first_name=fn, middle_name=mn)
        self.last_name.delete(0, "end")
        self.first_name.delete(0, "end")
        self.middle_name.delete(0, "end")
        self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete("1.0", "end")
        for w in self.service.list_workers():
            self.listbox.insert("end", f"{w['id']}: {w['last_name']} {w['first_name']}\n")