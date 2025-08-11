from __future__ import annotations

import customtkinter as ctk

from app.gui.views.common import BaseView
from app.services.contracts_service import ContractsService


class ContractsView(BaseView):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.service = ContractsService()
        self._add_section_title("Контракты")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="new", padx=12, pady=6)

        self.number = ctk.CTkEntry(form, placeholder_text="Номер контракта")
        self.customer = ctk.CTkEntry(form, placeholder_text="Заказчик")
        self.start_date = ctk.CTkEntry(form, placeholder_text="Дата начала YYYY-MM-DD")
        add_btn = ctk.CTkButton(form, text="Добавить", command=self._on_add)

        self.number.grid(row=0, column=0, padx=6, pady=6)
        self.customer.grid(row=0, column=1, padx=6, pady=6)
        self.start_date.grid(row=0, column=2, padx=6, pady=6)
        add_btn.grid(row=0, column=3, padx=6, pady=6)

        self.listbox = ctk.CTkTextbox(self, height=400)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self._refresh()

    def _on_add(self) -> None:
        self.service.create_contract(self.number.get().strip(), self.customer.get().strip(), self.start_date.get().strip())
        self.number.delete(0, "end")
        self.customer.delete(0, "end")
        self.start_date.delete(0, "end")
        self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete("1.0", "end")
        for c in self.service.list_contracts():
            self.listbox.insert("end", f"{c['id']}: {c['contract_number']} {c['customer']} {c['start_date']}\n")