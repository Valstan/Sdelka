from __future__ import annotations

import customtkinter as ctk

from app.gui.views.workers_view import WorkersView
from app.gui.views.job_types_view import JobTypesView
from app.gui.views.contracts_view import ContractsView
from app.gui.views.products_view import ProductsView
from app.gui.views.work_orders_view import WorkOrdersView
from app.gui.views.reports_view import ReportsView


class MainApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Учет сдельной работы")
        self.geometry("1100x700")

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True)

        workers_tab = tabview.add("Работники")
        job_types_tab = tabview.add("Виды работ")
        products_tab = tabview.add("Изделия")
        contracts_tab = tabview.add("Контракты")
        work_orders_tab = tabview.add("Наряды")
        reports_tab = tabview.add("Отчеты")

        WorkersView(workers_tab).pack(fill="both", expand=True)
        JobTypesView(job_types_tab).pack(fill="both", expand=True)
        ProductsView(products_tab).pack(fill="both", expand=True)
        ContractsView(contracts_tab).pack(fill="both", expand=True)
        WorkOrdersView(work_orders_tab).pack(fill="both", expand=True)
        ReportsView(reports_tab).pack(fill="both", expand=True)


def run_app() -> None:  # pragma: no cover - interactive
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = MainApp()
    app.mainloop()