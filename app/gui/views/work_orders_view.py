from __future__ import annotations

import customtkinter as ctk

from app.gui.views.common import BaseView
from app.services.contracts_service import ContractsService
from app.services.job_types_service import JobTypesService
from app.services.products_service import ProductsService
from app.services.work_orders_service import WorkOrdersService
from app.services.workers_service import WorkersService


class WorkOrdersView(BaseView):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.service = WorkOrdersService()
        self.workers_service = WorkersService()
        self.job_types_service = JobTypesService()
        self.contracts_service = ContractsService()
        self.products_service = ProductsService()

        self._add_section_title("Наряды")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="new", padx=12, pady=6)

        # Dropdown sources
        self._reload_sources()

        self.contract_var = ctk.StringVar()
        self.worker_var = ctk.StringVar()
        self.job_type_var = ctk.StringVar()
        self.product_var = ctk.StringVar()

        self.contract_menu = ctk.CTkOptionMenu(form, values=self.contract_names, variable=self.contract_var)
        self.worker_menu = ctk.CTkOptionMenu(form, values=self.worker_names, variable=self.worker_var)
        self.job_type_menu = ctk.CTkOptionMenu(form, values=self.job_type_names, variable=self.job_type_var)
        self.product_menu = ctk.CTkOptionMenu(form, values=["-"] + self.product_names, variable=self.product_var)

        self.date = ctk.CTkEntry(form, placeholder_text="Дата YYYY-MM-DD")
        self.quantity = ctk.CTkEntry(form, placeholder_text="Количество")
        self.rate = ctk.CTkEntry(form, placeholder_text="Ставка")
        add_btn = ctk.CTkButton(form, text="Добавить", command=self._on_add)
        reload_btn = ctk.CTkButton(form, text="Обновить списки", command=self._on_reload)

        widgets = [
            self.contract_menu,
            self.worker_menu,
            self.job_type_menu,
            self.product_menu,
            self.date,
            self.quantity,
            self.rate,
            add_btn,
            reload_btn,
        ]
        for idx, widget in enumerate(widgets):
            widget.grid(row=0, column=idx, padx=4, pady=6)

        self.listbox = ctk.CTkTextbox(self, height=400)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self._refresh()

    def _reload_sources(self) -> None:
        self.workers = self.workers_service.list_workers(active_only=True)
        self.worker_names = [f"{w['id']} — {w['last_name']} {w['first_name']}" for w in self.workers]
        self.worker_index = {name: w["id"] for name, w in zip(self.worker_names, self.workers, strict=False)}

        self.job_types = self.job_types_service.list_job_types()
        self.job_type_names = [f"{jt['id']} — {jt['name']} ({jt['unit']})" for jt in self.job_types]
        self.job_type_index = {name: jt["id"] for name, jt in zip(self.job_type_names, self.job_types, strict=False)}

        self.contracts = self.contracts_service.list_contracts()
        self.contract_names = [f"{c['id']} — {c['contract_number']}" for c in self.contracts]
        self.contract_index = {name: c["id"] for name, c in zip(self.contract_names, self.contracts, strict=False)}

        self.products = self.products_service.list_products()
        self.product_names = [f"{p['id']} — {p['name']}" for p in self.products]
        self.product_index = {name: p["id"] for name, p in zip(self.product_names, self.products, strict=False)}

    def _on_reload(self) -> None:
        self._reload_sources()
        self.contract_menu.configure(values=self.contract_names)
        self.worker_menu.configure(values=self.worker_names)
        self.job_type_menu.configure(values=self.job_type_names)
        self.product_menu.configure(values=["-"] + self.product_names)

    def _on_add(self) -> None:
        try:
            contract_id = self.contract_index.get(self.contract_var.get())
            worker_id = self.worker_index.get(self.worker_var.get())
            job_type_id = self.job_type_index.get(self.job_type_var.get())
            product_id = self.product_index.get(self.product_var.get()) if self.product_var.get() != "-" else None
            quantity = float(self.quantity.get())
            rate = float(self.rate.get())
        except Exception:
            return
        if not contract_id or not worker_id or not job_type_id:
            return
        self.service.create_work_order(
            contract_id=contract_id,
            worker_id=worker_id,
            job_type_id=job_type_id,
            product_id=product_id,
            date=self.date.get().strip(),
            quantity=quantity,
            unit_rate=rate,
        )
        for widget in [self.date, self.quantity, self.rate]:
            widget.delete(0, "end")
        self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete("1.0", "end")
        for wo in self.service.list_work_orders():
            self.listbox.insert(
                "end",
                f"{wo['id']}: C{wo['contract_id']} W{wo['worker_id']} J{wo['job_type_id']} {wo['date']} qty={wo['quantity']} amt={wo['amount']}\n",
            )