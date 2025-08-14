from __future__ import annotations

import customtkinter as ctk

from gui.forms.workers_form import WorkersForm
from gui.forms.job_types_form import JobTypesForm
from gui.forms.products_form import ProductsForm
from gui.forms.contracts_form import ContractsForm
from gui.forms.work_order_form import WorkOrdersForm
from gui.forms.reports_view import ReportsView
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

        WorkersForm(tab_workers).pack(expand=True, fill="both")
        JobTypesForm(tab_jobs).pack(expand=True, fill="both")
        ProductsForm(tab_products).pack(expand=True, fill="both")
        ContractsForm(tab_contracts).pack(expand=True, fill="both")

        # Отчеты
        ReportsView(self.tab_reports).pack(expand=True, fill="both")

        # Настройки
        SettingsView(self.tab_settings).pack(expand=True, fill="both")