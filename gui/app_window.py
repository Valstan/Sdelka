from __future__ import annotations

import customtkinter as ctk

from gui.forms.workers_form import WorkersForm
from gui.forms.job_types_form import JobTypesForm
from gui.forms.products_form import ProductsForm
from gui.forms.contracts_form import ContractsForm
from gui.forms.work_order_form import WorkOrdersForm
from gui.forms.reports_view import ReportsView
from gui.forms.import_export_view import ImportExportView
from gui.forms.settings_view import SettingsView
from utils.user_prefs import load_prefs
from utils.ui_theming import apply_user_fonts


class AppWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Учет сдельной работы бригад")
        self.geometry("1200x760")
        # Применить пользовательские шрифты
        try:
            prefs = load_prefs()
            apply_user_fonts(self, prefs)
        except Exception:
            pass
        self._build_ui()

    def _build_ui(self) -> None:
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both")

        self.tab_orders = tabview.add("Наряды")
        self.tab_refs = tabview.add("Справочники")
        self.tab_import = tabview.add("Импорт/Экспорт")
        self.tab_reports = tabview.add("Отчеты")
        self.tab_settings = tabview.add("Настройки")

        # Наряды: без прокрутки, всё должно умещаться
        WorkOrdersForm(self.tab_orders).pack(expand=True, fill="both")

        # Подвкладки справочников
        refs_tabs = ctk.CTkTabview(self.tab_refs)
        refs_tabs.pack(expand=True, fill="both", padx=10, pady=10)
        tab_workers = refs_tabs.add("Работники")
        tab_jobs = refs_tabs.add("Виды работ")
        tab_products = refs_tabs.add("Изделия")
        tab_contracts = refs_tabs.add("Контракты")

        workers_sf = ctk.CTkScrollableFrame(tab_workers)
        workers_sf.pack(expand=True, fill="both")
        WorkersForm(workers_sf).pack(expand=True, fill="both")

        jobs_sf = ctk.CTkScrollableFrame(tab_jobs)
        jobs_sf.pack(expand=True, fill="both")
        JobTypesForm(jobs_sf).pack(expand=True, fill="both")

        products_sf = ctk.CTkScrollableFrame(tab_products)
        products_sf.pack(expand=True, fill="both")
        ProductsForm(products_sf).pack(expand=True, fill="both")

        contracts_sf = ctk.CTkScrollableFrame(tab_contracts)
        contracts_sf.pack(expand=True, fill="both")
        ContractsForm(contracts_sf).pack(expand=True, fill="both")

        # Отчеты
        reports_sf = ctk.CTkScrollableFrame(self.tab_reports)
        reports_sf.pack(expand=True, fill="both")
        ReportsView(reports_sf).pack(expand=True, fill="both")

        # Импорт/Экспорт
        import_sf = ctk.CTkScrollableFrame(self.tab_import)
        import_sf.pack(expand=True, fill="both")
        ImportExportView(import_sf).pack(expand=True, fill="both")

        # Настройки
        settings_sf = ctk.CTkScrollableFrame(self.tab_settings)
        settings_sf.pack(expand=True, fill="both")
        SettingsView(settings_sf).pack(expand=True, fill="both")