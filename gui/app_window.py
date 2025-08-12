from __future__ import annotations

import customtkinter as ctk

from gui.forms.workers_form import WorkersForm


class AppWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Учет сдельной работы бригад")
        self.geometry("1100x700")
        self._build_ui()

    def _build_ui(self) -> None:
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both")

        self.tab_orders = tabview.add("Наряды")
        self.tab_refs = tabview.add("Справочники")
        self.tab_import = tabview.add("Импорт/Экспорт")
        self.tab_reports = tabview.add("Отчеты")
        self.tab_settings = tabview.add("Настройки")

        # Заглушки контента
        ctk.CTkLabel(self.tab_orders, text="Форма нарядов (в разработке)").pack(pady=20)

        # Подвкладки справочников
        refs_tabs = ctk.CTkTabview(self.tab_refs)
        refs_tabs.pack(expand=True, fill="both", padx=10, pady=10)
        tab_workers = refs_tabs.add("Работники")
        refs_tabs.add("Виды работ")
        refs_tabs.add("Изделия")
        refs_tabs.add("Контракты")

        WorkersForm(tab_workers).pack(expand=True, fill="both")

        ctk.CTkLabel(self.tab_import, text="Импорт/Экспорт (в разработке)").pack(pady=20)
        ctk.CTkLabel(self.tab_reports, text="Отчеты (в разработке)").pack(pady=20)
        ctk.CTkLabel(self.tab_settings, text="Настройки (в разработке)").pack(pady=20)