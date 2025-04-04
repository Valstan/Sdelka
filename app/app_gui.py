"""
Основной класс GUI приложения.
Реализует главное окно и управление формами.
"""
import logging
import tkinter as tk
from typing import Optional, Callable

import customtkinter as ctk
from tkinter import ttk

from app.config import UI_SETTINGS, APP_TITLE
from app.db_manager import DatabaseManager
from app.card_form import CardForm
from app.report.report_form import ReportForm
from app.services import (
    WorkerService, WorkTypeService,
    ProductService, ContractService,
    CardService, ReportService
)
from app.styles import init_app_styles

logger = logging.getLogger(__name__)


class AppGUI:
    """Класс главного графического интерфейса приложения."""

    def __init__(self, root: ctk.CTk, db_manager: DatabaseManager):
        self.root = root
        self.db_manager = db_manager
        self.current_form: Optional[ttk.Frame] = None

        # Инициализация сервисов
        self._init_services()
        self._setup_ui()
        self._bind_events()

    def _init_services(self) -> None:
        """Инициализация бизнес-логики приложения."""
        self.worker_service = WorkerService(self.db_manager)
        self.work_type_service = WorkTypeService(self.db_manager)
        self.product_service = ProductService(self.db_manager)
        self.contract_service = ContractService(self.db_manager)
        self.card_service = CardService(self.db_manager, self.product_service)
        self.report_service = ReportService(
            self.db_manager,
            self.worker_service,
            self.contract_service,
            self.work_type_service,
            self.product_service
        )

    def _setup_ui(self) -> None:
        """Настройка основных элементов интерфейса."""
        init_app_styles()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Основные фреймы
        self.header_frame = self._create_header_frame()
        self.nav_frame = self._create_navigation_frame()
        self.content_frame = self._create_content_frame()

    def _bind_events(self) -> None:
        """Привязка глобальных горячих клавиш."""
        self.root.bind("<Control-s>", lambda e: self._save_current_form())
        self.root.bind("<Control-q>", lambda e: self._on_close())

    def _create_header_frame(self) -> ctk.CTkFrame:
        """Создание верхней панели с заголовком."""
        frame = ctk.CTkFrame(
            self.root,
            fg_color=UI_SETTINGS['primary_color']
        )
        title_label = ctk.CTkLabel(
            frame,
            text=APP_TITLE,
            font=UI_SETTINGS['header_style']['font'],
            text_color=UI_SETTINGS['header_style']['text_color']
        )
        title_label.pack(side=tk.LEFT, padx=20)
        frame.pack(fill=tk.X, side=tk.TOP, ipady=10)
        return frame

    def _create_navigation_frame(self) -> ctk.CTkFrame:
        """Создание панели навигации."""
        frame = ctk.CTkFrame(self.root, fg_color=UI_SETTINGS['background_color'])

        buttons = [
            ("Карточки работ", self.show_cards_list),
            ("Справочники", self.show_references),
            ("Отчеты", self.show_reports)
        ]

        for text, command in buttons:
            btn = ctk.CTkButton(
                frame,
                text=text,
                command=command,
                **UI_SETTINGS['button_style']
            )
            btn.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        frame.pack(fill=tk.X, side=tk.TOP, ipady=5)
        return frame

    def _create_content_frame(self) -> ctk.CTkFrame:
        """Создание основного контейнера для контента."""
        frame = ctk.CTkFrame(
            self.root,
            fg_color=UI_SETTINGS['background_color']
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return frame

    def _clear_content(self) -> None:
        """Очистка области контента."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_form = None

    def show_cards_list(self) -> None:
        """Отображение списка карточек работ."""
        self._clear_content()
        # Реализация таблицы с карточками...

    def show_references(self) -> None:
        """Отображение справочников."""
        self._clear_content()
        # Реализация вкладок со справочниками...

    def show_reports(self) -> None:
        """Отображение формы отчетов."""
        self._clear_content()
        ReportForm(self.content_frame, self.report_service)

    def _save_current_form(self) -> None:
        """Сохранение данных в текущей активной форме."""
        if isinstance(self.current_form, CardForm):
            self.current_form.save_card()

    def _on_close(self) -> None:
        """Обработчик закрытия приложения."""
        if ctk.messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.db_manager.close()
            self.root.destroy()

    def _show_error(self, message: str) -> None:
        """Отображение сообщения об ошибке."""
        ctk.messagebox.showerror("Ошибка", message)