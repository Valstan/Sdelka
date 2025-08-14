from __future__ import annotations

import customtkinter as ctk
import tkinter.font as tkfont

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
        self._tab_font_normal = None
        self._tab_font_active = None
        self._tabview = None
        self._segmented_button = None
        # Применить пользовательские шрифты для остального UI
        try:
            prefs = load_prefs()
            apply_user_fonts(self, prefs)
        except Exception:
            pass
        self._build_ui()

    def _build_ui(self) -> None:
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both")
        self._tabview = tabview

        self.tab_orders = tabview.add("Наряды")
        self.tab_refs = tabview.add("Справочники")
        self.tab_reports = tabview.add("Отчеты")
        self.tab_settings = tabview.add("Настройки")

        # Наряды
        WorkOrdersForm(self.tab_orders).pack(expand=True, fill="both")

        # Справочники (внутренние вкладки)
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

        # Фиксированные шрифты вкладок (не зависят от настроек пользователя)
        self._setup_tab_fonts(self._tabview)
        self._setup_tab_fonts(refs_tabs)
        # Переприменять после изменения пользовательских настроек шрифтов
        try:
            self.bind("<<UIFontsChanged>>", lambda e: [self._setup_tab_fonts(self._tabview), self._setup_tab_fonts(refs_tabs)])
        except Exception:
            pass

    def _setup_tab_fonts(self, tabview: ctk.CTkTabview) -> None:
        try:
            base_family = tkfont.nametofont("TkDefaultFont").cget("family")
        except Exception:
            base_family = "TkDefaultFont"
        normal = tkfont.Font(family=base_family, size=20, weight="normal")
        active = tkfont.Font(family=base_family, size=24, weight="bold")
        seg = getattr(tabview, "_segmented_button", None)
        if seg is None:
            return
        # Применить шрифты и обновлять при переключении
        def apply_fonts():
            current = None
            try:
                current = tabview.get()
            except Exception:
                pass
            buttons = getattr(seg, "_buttons_dict", {})
            for name, btn in buttons.items():
                try:
                    btn.configure(font=active if name == current else normal)
                except Exception:
                    pass
        try:
            seg.bind("<ButtonRelease-1>", lambda e: apply_fonts(), add="+")
            seg.bind("<KeyRelease>", lambda e: apply_fonts(), add="+")
        except Exception:
            pass
        # Начальная установка
        tabview.after(50, apply_fonts)