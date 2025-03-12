"""
Основной класс GUI приложения.
Определяет главное окно и управляет взаимодействием между различными формами.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging

from app.config import UI_SETTINGS, APP_TITLE
from app.db_manager import DatabaseManager
from app.services.card_service import CardService
from app.models import WorkCard
from app.services.report_service import ReportService
from app.card_form import CardForm
from app.report.report_form import ReportForm
from app.services.services import WorkerService, WorkTypeService, ProductService, ContractService
from app.styles import init_app_styles

logger = logging.getLogger(__name__)


class AppGUI:
    def __init__(self, root: ctk.CTk, db_manager: DatabaseManager):
        self.root = root
        self.db_manager = db_manager

        # Инициализация сервисов
        self.worker_service = WorkerService(db_manager)
        self.work_type_service = WorkTypeService(db_manager)
        self.product_service = ProductService(db_manager)
        self.contract_service = ContractService(db_manager)
        self.card_service = CardService(db_manager, product_service=self.product_service)
        self.report_service = ReportService(
            db_manager,
            worker_service=self.worker_service,
            contract_service=self.contract_service,
            work_type_service=self.work_type_service,
            product_service=self.product_service
        )

        # Инициализация стилей
        init_app_styles()

        # Настройка главного окна
        self.setup_main_window()

        # Настройка интерфейса
        self.setup_ui()

        # Текущая открытая форма
        self.current_form = None

    def setup_main_window(self) -> None:
        """Настройка главного окна приложения"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self) -> None:
        """Настройка основных элементов интерфейса"""
        # Верхняя панель с заголовком и кнопками навигации
        self.create_header_frame()

        # Основной контейнер для содержимого
        self.create_content_frame()

    def create_header_frame(self) -> None:
        """Создание верхней панели с заголовком и кнопками навигации"""
        header_frame = ctk.CTkFrame(self.root, fg_color=UI_SETTINGS['primary_color'])
        header_frame.pack(fill=tk.X, side=tk.TOP, ipady=10)

        # Заголовок приложения
        title_label = ctk.CTkLabel(
            header_frame,
            text=APP_TITLE,
            font=UI_SETTINGS['header_style']['font'],
            text_color=UI_SETTINGS['header_style']['text_color']
        )
        title_label.pack(side=tk.LEFT, padx=20)

        # Кнопки навигации
        nav_frame = ctk.CTkFrame(self.root, fg_color=UI_SETTINGS['background_color'])
        nav_frame.pack(fill=tk.X, side=tk.TOP, ipady=5)

        # Кнопка "Карточки работ"
        cards_btn = ctk.CTkButton(
            nav_frame,
            text="Карточки работ",
            command=self.show_cards_list,
            **UI_SETTINGS['button_style']
        )
        cards_btn.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Кнопка "Справочники"
        refs_btn = ctk.CTkButton(
            nav_frame,
            text="Справочники",
            command=self.show_references,
            **UI_SETTINGS['button_style']
        )
        refs_btn.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Кнопка "Отчеты"
        reports_btn = ctk.CTkButton(
            nav_frame,
            text="Отчеты",
            command=self.show_reports,
            **UI_SETTINGS['button_style']
        )
        reports_btn.pack(side=tk.LEFT, padx=(0, 10), pady=5)

    def create_content_frame(self) -> None:
        """Создание основного контейнера для содержимого"""
        self.content_frame = ctk.CTkFrame(self.root, fg_color=UI_SETTINGS['background_color'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def clear_content(self) -> None:
        """Очистка области содержимого"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_form = None

    def show_cards_list(self) -> None:
        """Отображение списка карточек работ"""
        self.clear_content()

        # Заголовок
        header = ctk.CTkLabel(
            self.content_frame,
            text="Список карточек работ",
            **UI_SETTINGS['header_style']
        )
        header.pack(pady=(0, 10), anchor="w")

        # Кнопка "Создать карточку"
        create_btn = ctk.CTkButton(
            self.content_frame,
            text="Создать карточку",
            command=self.create_new_card,
            **UI_SETTINGS['button_style']
        )
        create_btn.pack(pady=(0, 10))

        # Таблица с карточками
        self.create_cards_table()

    def create_cards_table(self) -> None:
        """Создание таблицы с карточками работ"""
        table_frame = ctk.CTkFrame(self.content_frame, **UI_SETTINGS['card_frame'])
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Настройка таблицы
        columns = ("id", "number", "date", "product", "contract", "total_amount")
        self.cards_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настройка заголовков
        self.cards_table.heading("id", text="ID")
        self.cards_table.heading("number", text="Номер")
        self.cards_table.heading("date", text="Дата")
        self.cards_table.heading("product", text="Изделие")
        self.cards_table.heading("contract", text="Контракт")
        self.cards_table.heading("total_amount", text="Сумма")

        # Настройка ширин столбцов
        self.cards_table.column("id", width=50, anchor="center")
        self.cards_table.column("number", width=100, anchor="center")
        self.cards_table.column("date", width=100, anchor="center")
        self.cards_table.column("product", width=200)
        self.cards_table.column("contract", width=150)
        self.cards_table.column("total_amount", width=100, anchor="e")

        # Добавление прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.cards_table.yview)
        self.cards_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cards_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        self.load_cards_data()

        # Привязка события двойного клика
        self.cards_table.bind("<Double-1>", self.on_card_double_click)

    def load_cards_data(self) -> None:
        """Загрузка данных карточек из базы данных"""
        cards = self.card_service.get_all_cards()
        for card in cards:
            self.cards_table.insert(
                "", "end",
                values=(
                    card.id,
                    card.card_number,
                    card.formatted_date,
                    card.product_name,
                    card.contract_number,
                    f"{card.total_amount:.2f}"
                )
            )

    def on_card_double_click(self, event) -> None:
        """Обработчик события двойного клика по карточке"""
        selection = self.cards_table.selection()
        if not selection:
            return

        item = self.cards_table.item(selection[0])
        card_id = int(item["values"][0])
        self.edit_card(card_id)

    def create_new_card(self) -> None:
        """Создание новой карточки работ"""
        card = self.card_service.create_new_card()
        self.show_card_form(card)

    def edit_card(self, card_id: int) -> None:
        """Редактирование существующей карточки"""
        card = self.card_service.get_card(card_id)
        if card:
            self.show_card_form(card)
        else:
            messagebox.showerror("Ошибка", f"Карточка с ID {card_id} не найдена")

    def show_card_form(self, card: WorkCard) -> None:
        """Отображение формы карточки работ"""
        self.clear_content()
        self.current_form = CardForm(
            self.content_frame,
            self.card_service,
            card,
            on_save=self.after_card_save,
            on_cancel=self.show_cards_list
        )

    def after_card_save(self) -> None:
        """Действия после сохранения карточки"""
        self.show_cards_list()

    def show_references(self) -> None:
        """Отображение справочников"""
        self.clear_content()

        # Заголовок
        header = ctk.CTkLabel(
            self.content_frame,
            text="Справочники",
            **UI_SETTINGS['header_style']
        )
        header.pack(pady=(0, 10), anchor="w")

        # Вкладки для справочников
        tab_view = ctk.CTkTabview(self.content_frame)
        tab_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка "Работники"
        workers_tab = tab_view.add("Работники")
        self.setup_workers_tab(workers_tab)

        # Вкладка "Виды работ"
        work_types_tab = tab_view.add("Виды работ")
        self.setup_work_types_tab(work_types_tab)

        # Вкладка "Изделия"
        products_tab = tab_view.add("Изделия")
        self.setup_products_tab(products_tab)

        # Вкладка "Контракты"
        contracts_tab = tab_view.add("Контракты")
        self.setup_contracts_tab(contracts_tab)

    def setup_workers_tab(self, tab) -> None:
        """Настройка вкладки "Работники" """
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить работника",
            command=self.add_worker,
            **UI_SETTINGS['button_style']
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=self.edit_selected_worker,
            **UI_SETTINGS['button_style']
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=self.delete_selected_worker,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['button_style']['hover_color']
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица работников
        table_frame = ctk.CTkFrame(tab, **UI_SETTINGS['card_frame'])
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "last_name", "first_name", "middle_name", "position")
        self.workers_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настройка заголовков
        self.workers_table.heading("id", text="ID")
        self.workers_table.heading("last_name", text="Фамилия")
        self.workers_table.heading("first_name", text="Имя")
        self.workers_table.heading("middle_name", text="Отчество")
        self.workers_table.heading("position", text="Должность")

        # Настройка ширин столбцов
        self.workers_table.column("id", width=50, anchor="center")
        self.workers_table.column("last_name", width=150)
        self.workers_table.column("first_name", width=150)
        self.workers_table.column("middle_name", width=150)
        self.workers_table.column("position", width=200)

        # Добавление прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.workers_table.yview)
        self.workers_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.workers_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        workers = self.worker_service.get_all_workers()
        for worker in workers:
            self.workers_table.insert(
                "", "end",
                values=(
                    worker.id,
                    worker.last_name,
                    worker.first_name,
                    worker.middle_name if worker.middle_name else "",
                    worker.position if worker.position else ""
                )
            )

    def add_worker(self) -> None:
        """Добавление нового работника"""
        # Реализация добавления работника
        pass

    def edit_selected_worker(self) -> None:
        """Редактирование выбранного работника"""
        # Реализация редактирования работника
        pass

    def delete_selected_worker(self) -> None:
        """Удаление выбранного работника"""
        # Реализация удаления работника
        pass

    def setup_work_types_tab(self, tab) -> None:
        """Настройка вкладки "Виды работ" """
        # Аналогично настройке вкладки "Работники"
        pass

    def setup_products_tab(self, tab) -> None:
        """Настройка вкладки "Изделия" """
        # Аналогично настройке вкладки "Работники"
        pass

    def setup_contracts_tab(self, tab) -> None:
        """Настройка вкладки "Контракты" """
        # Аналогично настройке вкладки "Работники"
        pass

    def show_reports(self) -> None:
        """Отображение формы для создания отчетов"""
        self.clear_content()
        ReportForm(self.content_frame, self.report_service)

    def on_close(self) -> None:
        """Обработчик закрытия приложения"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите закрыть приложение?"):
            self.root.destroy()
