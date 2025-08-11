from __future__ import annotations

import customtkinter as ctk

from app.gui.views.common import BaseView
from app.services.job_types_service import JobTypesService


class JobTypesView(BaseView):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.service = JobTypesService()
        self._add_section_title("Виды работ")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="new", padx=12, pady=6)

        self.name = ctk.CTkEntry(form, placeholder_text="Название")
        self.unit = ctk.CTkEntry(form, placeholder_text="Ед. изм.")
        self.rate = ctk.CTkEntry(form, placeholder_text="Базовая ставка")
        add_btn = ctk.CTkButton(form, text="Добавить", command=self._on_add)

        self.name.grid(row=0, column=0, padx=6, pady=6)
        self.unit.grid(row=0, column=1, padx=6, pady=6)
        self.rate.grid(row=0, column=2, padx=6, pady=6)
        add_btn.grid(row=0, column=3, padx=6, pady=6)

        self.listbox = ctk.CTkTextbox(self, height=400)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self._refresh()

    def _on_add(self) -> None:
        try:
            rate = float(self.rate.get() or 0)
        except ValueError:
            rate = 0.0
        self.service.create_job_type(self.name.get().strip(), self.unit.get().strip(), rate)
        self.name.delete(0, "end")
        self.unit.delete(0, "end")
        self.rate.delete(0, "end")
        self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete("1.0", "end")
        for jt in self.service.list_job_types():
            self.listbox.insert("end", f"{jt['id']}: {jt['name']} ({jt['unit']}) {jt['base_rate']}\n")