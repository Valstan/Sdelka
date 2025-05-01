"""
File: app/ui/main_app_gui.py
Основной графический интерфейс приложения с навигацией между разделами.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import date, datetime
import logging
import os
import sys

from app.core.models.worker import Worker
from app.core.models.contract import Contract
from app.core.models.product import Product
from app.core.models.work_type import WorkType
from app.core.models.work_card import WorkCard
from app.core.services.work_card_service import WorkCardsService
from app.core.services.report_manager import ReportManager
from app.ui.work_card_form import WorkCardForm
from app.ui.worker_form import WorkerForm
from app.ui.contract_form import ContractForm
from app.ui.product_form import ProductForm
from app.ui.work_type_form import WorkTypeForm
from app.ui.report_preview import ReportPreview
from app.config import UI_SETTINGS, DIRECTORIES
from app.config import APP_TITLE, APP_WIDTH, APP_HEIGHT

logger = logging.getLogger(__name__)


class AppGUI:
    """
    Основной GUI класс для бухгалтерской программы.
    Реализует навигацию между разделами и интеграцию с сервисами.
    """

    def __init__(self, root: tk.Tk, db_manager: 'DatabaseManager'):
        """
        Инициализация основного интерфейса.

        Args:
            root: Основное окно приложения
            db_manager: Менеджер базы данных
        """
        self.root = root
        self.db_manager = db_manager
        self.card_service = WorkCardsService(db_manager)
        self.report_manager = ReportManager(root, db_manager, self.card_service)
        self.current_form = None
        self._setup_root()
        self._setup_menu()
        self._setup_content()
        self._load_default_form()
        self._bind_events()

    def _setup_root(self) -> None:
        """Настройка основного окна."""
        self.root.title(APP_TITLE)
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Центрируем окно
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (APP_WIDTH // 2)
        y = (screen_height // 2) - (APP_HEIGHT // 2)
        self.root.geometry(f"+{x}+{y}")

        # Устанавливаем стиль
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

    def _setup_menu(self) -> None:
        """Настройка меню приложения."""
        menu_bar = ctk.CTkFrame(self.root, fg_color="#F5F5F5", height=40)
        menu_bar.pack(fill=tk.X, side=tk.TOP)

        # Кнопки навигации
        nav_buttons = [
            ("Работники", self.show_workers_form),
            ("Изделия", self.show_products_form),
            ("Контракты", self.show_contracts_form),
            ("Виды работ", self.show_work_types_form),
            ("Карточки", self.show_cards_form),
            ("Отчеты", self.report_manager.show_report_form)
        ]

        for text, command in nav_buttons:
            btn = ctk.CTkButton(
                menu_bar,
                text=text,
                command=command,
                **UI_SETTINGS['button_style']
            )
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def _setup_content(self) -> None:
        """Настройка контентной области."""
        self.content_frame = ctk.CTkFrame(self.root, fg_color="white")
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=10, pady=10)

    def _load_default_form(self) -> None:
        """Загружает форму по умолчанию."""
        self.show_cards_form()

    def _bind_events(self) -> None:
        """Привязывает глобальные события."""
        self.root.bind("<Control-q>", lambda e: self._on_close())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_workers_form(self) -> None:
        """Отображает форму управления работниками."""
        self._clear_content()
        WorkerForm(self.content_frame, self.card_service.worker_service, on_save=self._refresh_data)

    def show_products_form(self) -> None:
        """Отображает форму управления изделиями."""
        self._clear_content()
        ProductForm(self.content_frame, self.card_service.product_service, on_save=self._refresh_data)

    def show_contracts_form(self) -> None:
        """Отображает форму управления контрактами."""
        self._clear_content()
        ContractForm(self.content_frame, self.card_service.contract_service, on_save=self._refresh_data)

    def show_work_types_form(self) -> None:
        """Отображает форму управления типами работ."""
        self._clear_content()
        WorkTypeForm(self.content_frame, self.card_service.work_type_service, on_save=self._refresh_data)

    def show_cards_form(self) -> None:
        """Отображает форму управления карточками работ."""
        self._clear_content()
        WorkCardForm(self.content_frame, self.card_service, on_save=self._refresh_data)

    def _refresh_data(self) -> None:
        """Обновляет данные в текущей форме."""
        if self.current_form:
            self.current_form.refresh_data()

    def _clear_content(self) -> None:
        """Очищает контентную область."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _on_close(self) -> None:
        """Обработчик закрытия приложения."""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            try:
                self.db_manager.close()
                self.root.destroy()
                sys.exit(0)
            except Exception as e:
                logger.error(f"Ошибка закрытия приложения: {e}", exc_info=True)
                sys.exit(1)