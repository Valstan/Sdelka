from __future__ import annotations

import customtkinter as ctk


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
        ctk.CTkLabel(self.tab_refs, text="Справочники (в разработке)").pack(pady=20)
        ctk.CTkLabel(self.tab_import, text="Импорт/Экспорт (в разработке)").pack(pady=20)
        ctk.CTkLabel(self.tab_reports, text="Отчеты (в разработке)").pack(pady=20)
        ctk.CTkLabel(self.tab_settings, text="Настройки (в разработке)").pack(pady=20)