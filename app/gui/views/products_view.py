from __future__ import annotations

import customtkinter as ctk

from app.gui.views.common import BaseView
from app.services.products_service import ProductsService


class ProductsView(BaseView):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.service = ProductsService()
        self._add_section_title("Изделия")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="new", padx=12, pady=6)

        self.name = ctk.CTkEntry(form, placeholder_text="Название")
        self.sku = ctk.CTkEntry(form, placeholder_text="SKU")
        self.desc = ctk.CTkEntry(form, placeholder_text="Описание")
        add_btn = ctk.CTkButton(form, text="Добавить", command=self._on_add)

        self.name.grid(row=0, column=0, padx=6, pady=6)
        self.sku.grid(row=0, column=1, padx=6, pady=6)
        self.desc.grid(row=0, column=2, padx=6, pady=6)
        add_btn.grid(row=0, column=3, padx=6, pady=6)

        self.listbox = ctk.CTkTextbox(self, height=400)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self._refresh()

    def _on_add(self) -> None:
        self.service.create_product(self.name.get().strip(), self.sku.get().strip() or None, self.desc.get().strip() or None)
        self.name.delete(0, "end")
        self.sku.delete(0, "end")
        self.desc.delete(0, "end")
        self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete("1.0", "end")
        for p in self.service.list_products():
            self.listbox.insert("end", f"{p['id']}: {p['name']} ({p.get('sku','')})\n")