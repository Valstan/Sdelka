"""
Основной класс GUI приложения.
Определяет главное окно и управляет взаимодействием между различными формами.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging
from typing import Optional, Dict, Any, List

from app.db.db_manager import DatabaseManager
from app.services.card_service import CardService, WorkerService, WorkTypeService, ProductService, ContractService
from app.services.report_service import ReportService
from app.gui.styles import init_app_styles, COLOR_SCHEME, FRAME_STYLE, BUTTON_STYLE, HEADER_STYLE
from app.gui.card_form import CardForm
from app.gui.report_form import ReportForm

logger = logging.getLogger(__name__)

class AppGUI:
    """
    Основной класс графического интерфейса приложения.
    Создает главное окно и управляет навигацией между различными экранами.
    """

    def __init__(self, root: ctk.CTk, db_manager: DatabaseManager):
        """
        Инициализация главного окна приложения.

        Args:
            root: Корневой виджет Tkinter
            db_manager: Менеджер базы данных
        """
        self.root = root
        self.db_manager = db_manager

        # Инициализация сервисов
        self.card_service = CardService(db_manager)
        self.worker_service = WorkerService(db_manager)
        self.work_type_service = WorkTypeService(db_manager)
        self.product_service = ProductService(db_manager)
        self.contract_service = ContractService(db_manager)
        self.report_service = ReportService(db_manager)

        # Инициализация стилей
        init_app_styles()

        # Создание основных контейнеров интерфейса
        self.setup_ui()

        # Текущая открытая форма
        self.current_form = None

        # Отображаем начальный экран - список карточек
        self.show_cards_list()

    def setup_ui(self) -> None:
        """Настройка основных элементов интерфейса"""
        # Настраиваем основное окно
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Создаем верхнюю панель с заголовком и кнопками
        self.header_frame = ctk.CTkFrame(self.root, fg_color=COLOR_SCHEME["primary"])
        self.header_frame.pack(fill=tk.X, side=tk.TOP, ipady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Учет сдельной работы бригад",
            font=("Roboto", 20, "bold"),
            text_color="white"
        )
        self.title_label.pack(side=tk.LEFT, padx=20)

        # Создаем панель с кнопками навигации
        self.nav_frame = ctk.CTkFrame(self.root, fg_color=COLOR_SCHEME["background"])
        self.nav_frame.pack(fill=tk.X, side=tk.TOP, ipady=5)

        # Кнопка "Карточки работ"
        self.cards_btn = ctk.CTkButton(
            self.nav_frame,
            text="Карточки работ",
            command=self.show_cards_list,
            **BUTTON_STYLE
        )
        self.cards_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Кнопка "Справочники"
        self.refs_btn = ctk.CTkButton(
            self.nav_frame,
            text="Справочники",
            command=self.show_references,
            **BUTTON_STYLE
        )
        self.refs_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Кнопка "Отчеты"
        self.reports_btn = ctk.CTkButton(
            self.nav_frame,
            text="Отчеты",
            command=self.show_reports,
            **BUTTON_STYLE
        )
        self.reports_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Основной контейнер для содержимого
        self.content_frame = ctk.CTkFrame(self.root, fg_color=COLOR_SCHEME["background"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def clear_content(self) -> None:
        """Очистка области содержимого"""
        # Уничтожаем все виджеты в области содержимого
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Сбрасываем ссылку на текущую форму
        self.current_form = None

    def show_cards_list(self) -> None:
        """Отображение списка карточек работ"""
        self.clear_content()

        # Создаем заголовок
        header = ctk.CTkLabel(
            self.content_frame,
            text="Список карточек работ",
            **HEADER_STYLE
        )
        header.pack(pady=(0, 10), anchor="w")

        # Создаем фрейм с кнопками
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопка "Создать карточку"
        create_btn = ctk.CTkButton(
            btn_frame,
            text="Создать карточку",
            command=self.create_new_card,
            **BUTTON_STYLE
        )
        create_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Создаем фрейм для таблицы
        table_frame = ctk.CTkFrame(self.content_frame, **FRAME_STYLE)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем таблицу для списка карточек
        columns = (
            "number", "date", "product", "contract",
            "workers_count", "total_amount"
        )

        self.cards_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настраиваем заголовки столбцов
        self.cards_table.heading("number", text="№ карточки")
        self.cards_table.heading("date", text="Дата")
        self.cards_table.heading("product", text="Изделие")
        self.cards_table.heading("contract", text="Контракт")
        self.cards_table.heading("workers_count", text="Кол-во работников")
        self.cards_table.heading("total_amount", text="Сумма, руб.")

        # Настраиваем ширину столбцов
        self.cards_table.column("number", width=100, anchor="center")
        self.cards_table.column("date", width=100, anchor="center")
        self.cards_table.column("product", width=250)
        self.cards_table.column("contract", width=150)
        self.cards_table.column("workers_count", width=150, anchor="center")
        self.cards_table.column("total_amount", width=150, anchor="e")

        # Добавляем прокрутку
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.cards_table.yview)
        self.cards_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cards_table.pack(fill=tk.BOTH, expand=True)

        # Привязываем двойной клик для открытия карточки
        self.cards_table.bind("<Double-1>", self.on_card_double_click)

        # Загружаем список карточек из БД
        self.load_cards_list()

    def load_cards_list(self) -> None:
        """Загрузка списка карточек из базы данных"""
        # Очищаем таблицу
        for item in self.cards_table.get_children():
            self.cards_table.delete(item)

        # Получаем список карточек из БД
        cards = self.card_service.get_all_cards()

        # Добавляем карточки в таблицу
        for card in cards:
            # Получаем полную информацию о карточке, включая работников
            full_card = self.card_service.get_card(card.id)

            # Формируем строку для изделия
            product_text = f"{card.product_number} {card.product_type}" if card.product_number else "-"

            # Вставляем строку в таблицу
            self.cards_table.insert(
                "", "end",
                values=(
                    card.card_number,
                    card.card_date.strftime("%d.%m.%Y") if card.card_date else "-",
                    product_text,
                    card.contract_number if card.contract_number else "-",
                    len(full_card.workers) if full_card else 0,
                    f"{card.total_amount:.2f}"
                ),
                tags=(str(card.id),)
            )

    def on_card_double_click(self, event) -> None:
        """Обработчик двойного клика по карточке в таблице"""
        # Получаем выбранный элемент
        selection = self.cards_table.selection()
        if not selection:
            return

        # Получаем ID карточки из тега
        item = self.cards_table.item(selection[0])
        card_id = int(item["tags"][0])

        # Открываем форму редактирования карточки
        self.edit_card(card_id)

    def create_new_card(self) -> None:
        """Создание новой карточки работ"""
        # Создаем новую карточку через сервис
        card = self.card_service.create_new_card()

        # Отображаем форму карточки
        self.clear_content()
        self.current_form = CardForm(
            self.content_frame,
            self.card_service,
            self.worker_service,
            self.work_type_service,
            self.product_service,
            self.contract_service,
            card,
            on_save=self.on_card_saved,
            on_cancel=self.show_cards_list
        )

    def edit_card(self, card_id: int) -> None:
        """
        Редактирование существующей карточки.

        Args:
            card_id: ID карточки для редактирования
        """
        # Получаем карточку из БД
        card = self.card_service.get_card(card_id)
        if not card:
            messagebox.showerror("Ошибка", f"Карточка с ID {card_id} не найдена")
            return

        # Отображаем форму карточки
        self.clear_content()
        self.current_form = CardForm(
            self.content_frame,
            self.card_service,
            self.worker_service,
            self.work_type_service,
            self.product_service,
            self.contract_service,
            card,
            on_save=self.on_card_saved,
            on_cancel=self.show_cards_list
        )

    def on_card_saved(self) -> None:
        """Обработчик события сохранения карточки"""
        # Возвращаемся к списку карточек и обновляем его
        self.show_cards_list()

    def show_references(self) -> None:
        """Отображение справочников"""
        self.clear_content()

        # Создаем заголовок
        header = ctk.CTkLabel(
            self.content_frame,
            text="Справочники",
            **HEADER_STYLE
        )
        header.pack(pady=(0, 10), anchor="w")

        # Создаем фрейм с вкладками для справочников
        tab_view = ctk.CTkTabview(self.content_frame)
        tab_view.pack(fill=tk.BOTH, expand=True)

        # Создаем вкладки для каждого справочника
        tab_workers = tab_view.add("Работники")
        tab_work_types = tab_view.add("Виды работ")
        tab_products = tab_view.add("Изделия")
        tab_contracts = tab_view.add("Контракты")

        # Настраиваем внешний вид вкладок
        for tab in [tab_workers, tab_work_types, tab_products, tab_contracts]:
            tab.configure(fg_color=COLOR_SCHEME["card"])

        # Заполняем каждую вкладку соответствующими данными
        self.setup_workers_tab(tab_workers)
        self.setup_work_types_tab(tab_work_types)
        self.setup_products_tab(tab_products)
        self.setup_contracts_tab(tab_contracts)

    def setup_workers_tab(self, tab) -> None:
        """
        Настройка содержимого вкладки "Работники".

        Args:
            tab: Вкладка для настройки
        """
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(10, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить работника",
            command=self.add_worker,
            **BUTTON_STYLE
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=lambda: self.edit_worker(self.workers_table),
            **BUTTON_STYLE
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=lambda: self.delete_worker(self.workers_table),
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица работников
        table_frame = ctk.CTkFrame(tab, **FRAME_STYLE)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "last_name", "first_name", "middle_name", "position")

        self.workers_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.workers_table.heading("id", text="ID")
        self.workers_table.heading("last_name", text="Фамилия")
        self.workers_table.heading("first_name", text="Имя")
        self.workers_table.heading("middle_name", text="Отчество")
        self.workers_table.heading("position", text="Должность")

        self.workers_table.column("id", width=50, anchor="center")
        self.workers_table.column("last_name", width=150)
        self.workers_table.column("first_name", width=150)
        self.workers_table.column("middle_name", width=150)
        self.workers_table.column("position", width=150)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.workers_table.yview)
        self.workers_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.workers_table.pack(fill=tk.BOTH, expand=True)

        # Загружаем данные
        self.load_workers_data()

        # Привязываем двойной клик для редактирования
        self.workers_table.bind("<Double-1>", lambda e: self.edit_worker(self.workers_table))

    def load_workers_data(self) -> None:
        """Загрузка данных работников в таблицу"""
        # Очищаем таблицу
        for item in self.workers_table.get_children():
            self.workers_table.delete(item)

        # Получаем список работников
        workers = self.worker_service.get_all_workers()

        # Добавляем в таблицу
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
        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Добавление работника")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Фамилия:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        last_name_entry = ctk.CTkEntry(form_frame, width=250)
        last_name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Имя:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        first_name_entry = ctk.CTkEntry(form_frame, width=250)
        first_name_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Отчество:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        middle_name_entry = ctk.CTkEntry(form_frame, width=250)
        middle_name_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Должность:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        position_entry = ctk.CTkEntry(form_frame, width=250)
        position_entry.grid(row=3, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_worker():
            # Проверка обязательных полей
            if not last_name_entry.get() or not first_name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо заполнить фамилию и имя")
                return

            # Создаем объект работника и сохраняем
            from app.db.models import Worker
            worker = Worker(
                last_name=last_name_entry.get(),
                first_name=first_name_entry.get(),
                middle_name=middle_name_entry.get() if middle_name_entry.get() else None,
                position=position_entry.get() if position_entry.get() else None
            )

            success, error = self.worker_service.save_worker(worker)
            if success:
                dialog.destroy()
                self.load_workers_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Работник успешно добавлен")
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить работника: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_worker,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def edit_worker(self, table) -> None:
        """
        Редактирование выбранного работника.

        Args:
            table: Таблица с работниками
        """
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите работника для редактирования")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        worker_id = int(values[0])

        # Получаем данные работника из БД
        worker = self.worker_service.db.get_worker_by_id(worker_id)
        if not worker:
            messagebox.showerror("Ошибка", f"Работник с ID {worker_id} не найден")
            return

        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Редактирование работника")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Фамилия:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        last_name_entry = ctk.CTkEntry(form_frame, width=250)
        last_name_entry.insert(0, worker.last_name)
        last_name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Имя:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        first_name_entry = ctk.CTkEntry(form_frame, width=250)
        first_name_entry.insert(0, worker.first_name)
        first_name_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Отчество:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        middle_name_entry = ctk.CTkEntry(form_frame, width=250)
        if worker.middle_name:
            middle_name_entry.insert(0, worker.middle_name)
        middle_name_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Должность:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        position_entry = ctk.CTkEntry(form_frame, width=250)
        if worker.position:
            position_entry.insert(0, worker.position)
        position_entry.grid(row=3, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_worker_changes():
            # Проверка обязательных полей
            if not last_name_entry.get() or not first_name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо заполнить фамилию и имя")
                return

            # Обновляем объект работника
            worker.last_name = last_name_entry.get()
            worker.first_name = first_name_entry.get()
            worker.middle_name = middle_name_entry.get() if middle_name_entry.get() else None
            worker.position = position_entry.get() if position_entry.get() else None

            success, error = self.worker_service.save_worker(worker)
            if success:
                dialog.destroy()
                self.load_workers_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Данные работника успешно обновлены")
            else:
                messagebox.showerror("Ошибка", f"Не удалось обновить данные работника: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_worker_changes,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def delete_worker(self, table) -> None:
        """
        Удаление выбранного работника.

        Args:
            table: Таблица с работниками
        """
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите работника для удаления")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        worker_id = int(values[0])
        worker_name = f"{values[1]} {values[2]}"

        # Подтверждение удаления
        if not messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить работника {worker_name}?"):
            return

        # Удаляем работника
        success, error = self.worker_service.delete_worker(worker_id)
        if success:
            self.load_workers_data()  # Обновляем таблицу
            messagebox.showinfo("Успех", f"Работник {worker_name} успешно удален")
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить работника: {error}")

    def setup_work_types_tab(self, tab) -> None:
        """Настройка вкладки 'Виды работ'"""
        # Аналогично setup_workers_tab, но для видов работ
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(10, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить вид работы",
            command=self.add_work_type,
            **BUTTON_STYLE
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=lambda: self.edit_work_type(self.work_types_table),
            **BUTTON_STYLE
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=lambda: self.delete_work_type(self.work_types_table),
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица видов работ
        table_frame = ctk.CTkFrame(tab, **FRAME_STYLE)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "name", "price", "description")

        self.work_types_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.work_types_table.heading("id", text="ID")
        self.work_types_table.heading("name", text="Наименование")
        self.work_types_table.heading("price", text="Цена, руб.")
        self.work_types_table.heading("description", text="Описание")

        self.work_types_table.column("id", width=50, anchor="center")
        self.work_types_table.column("name", width=300)
        self.work_types_table.column("price", width=100, anchor="e")
        self.work_types_table.column("description", width=300)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.work_types_table.yview)
        self.work_types_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.work_types_table.pack(fill=tk.BOTH, expand=True)

        # Загружаем данные
        self.load_work_types_data()

        # Привязываем двойной клик для редактирования
        self.work_types_table.bind("<Double-1>", lambda e: self.edit_work_type(self.work_types_table))

    def load_work_types_data(self) -> None:
        """Загрузка данных видов работ в таблицу"""
        # Очищаем таблицу
        for item in self.work_types_table.get_children():
            self.work_types_table.delete(item)

        # Получаем список видов работ
        work_types = self.work_type_service.get_all_work_types()

        # Добавляем в таблицу
        for work_type in work_types:
            self.work_types_table.insert(
                "", "end",
                values=(
                    work_type.id,
                    work_type.name,
                    f"{work_type.price:.2f}",
                    work_type.description if work_type.description else ""
                )
            )

    def add_work_type(self) -> None:
        """Добавление нового вида работы"""
        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Добавление вида работы")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Наименование:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(form_frame, width=250)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Цена, руб.:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        price_entry = ctk.CTkEntry(form_frame, width=250)
        price_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Описание:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        description_entry = ctk.CTkTextbox(form_frame, width=250, height=100)
        description_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_work_type():
            # Проверка обязательных полей
            if not name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо указать наименование")
                return

            try:
                price = float(price_entry.get())
                if price <= 0:
                    messagebox.showwarning("Внимание", "Цена должна быть положительным числом")
                    return
            except ValueError:
                messagebox.showwarning("Внимание", "Цена должна быть числом")
                return

            # Создаем объект вида работы и сохраняем
            from app.db.models import WorkType
            work_type = WorkType(
                name=name_entry.get(),
                price=price,
                description=description_entry.get("1.0", tk.END).strip() or None
            )

            success, error = self.work_type_service.save_work_type(work_type)
            if success:
                dialog.destroy()
                self.load_work_types_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Вид работы успешно добавлен")
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить вид работы: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_work_type,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def edit_work_type(self, table) -> None:
        """Редактирование выбранного вида работы"""
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите вид работы для редактирования")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        work_type_id = int(values[0])

        # Получаем данные вида работы из БД
        work_type = self.work_type_service.db.get_work_type_by_id(work_type_id)
        if not work_type:
            messagebox.showerror("Ошибка", f"Вид работы с ID {work_type_id} не найден")
            return

        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Редактирование вида работы")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Наименование:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(form_frame, width=250)
        name_entry.insert(0, work_type.name)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Цена, руб.:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        price_entry = ctk.CTkEntry(form_frame, width=250)
        price_entry.insert(0, str(work_type.price))
        price_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Описание:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        description_entry = ctk.CTkTextbox(form_frame, width=250, height=100)
        if work_type.description:
            description_entry.insert("1.0", work_type.description)
        description_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_work_type_changes():
            # Проверка обязательных полей
            if not name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо указать наименование")
                return

            try:
                price = float(price_entry.get())
                if price <= 0:
                    messagebox.showwarning("Внимание", "Цена должна быть положительным числом")
                    return
            except ValueError:
                messagebox.showwarning("Внимание", "Цена должна быть числом")
                return

            # Обновляем объект вида работы
            work_type.name = name_entry.get()
            work_type.price = price
            work_type.description = description_entry.get("1.0", tk.END).strip() or None

            success, error = self.work_type_service.save_work_type(work_type)
            if success:
                dialog.destroy()
                self.load_work_types_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Данные вида работы успешно обновлены")
            else:
                messagebox.showerror("Ошибка", f"Не удалось обновить данные вида работы: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_work_type_changes,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def delete_work_type(self, table) -> None:
        """Удаление выбранного вида работы"""
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите вид работы для удаления")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        work_type_id = int(values[0])
        work_type_name = values[1]

        # Подтверждение удаления
        if not messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить вид работы '{work_type_name}'?"):
            return

        # Удаляем вид работы
        success, error = self.work_type_service.delete_work_type(work_type_id)
        if success:
            self.load_work_types_data()  # Обновляем таблицу
            messagebox.showinfo("Успех", f"Вид работы '{work_type_name}' успешно удален")
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить вид работы: {error}")

    def setup_products_tab(self, tab) -> None:
        """Настройка вкладки 'Изделия'"""
        # Аналогично предыдущим вкладкам
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(10, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить изделие",
            command=self.add_product,
            **BUTTON_STYLE
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=lambda: self.edit_product(self.products_table),
            **BUTTON_STYLE
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=lambda: self.delete_product(self.products_table),
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица изделий
        table_frame = ctk.CTkFrame(tab, **FRAME_STYLE)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "product_number", "product_type", "additional_number", "description")

        self.products_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.products_table.heading("id", text="ID")
        self.products_table.heading("product_number", text="Номер изделия")
        self.products_table.heading("product_type", text="Тип изделия")
        self.products_table.heading("additional_number", text="Доп. номер")
        self.products_table.heading("description", text="Описание")

        self.products_table.column("id", width=50, anchor="center")
        self.products_table.column("product_number", width=150)
        self.products_table.column("product_type", width=150)
        self.products_table.column("additional_number", width=150)
        self.products_table.column("description", width=250)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.products_table.yview)
        self.products_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.products_table.pack(fill=tk.BOTH, expand=True)

        # Загружаем данные
        self.load_products_data()

        # Привязываем двойной клик для редактирования
        self.products_table.bind("<Double-1>", lambda e: self.edit_product(self.products_table))

    def load_products_data(self) -> None:
        """Загрузка данных изделий в таблицу"""
        # Очищаем таблицу
        for item in self.products_table.get_children():
            self.products_table.delete(item)

        # Получаем список изделий
        products = self.product_service.get_all_products()

        # Добавляем в таблицу
        for product in products:
            self.products_table.insert(
                "", "end",
                values=(
                    product.id,
                    product.product_number,
                    product.product_type,
                    product.additional_number if product.additional_number else "",
                    product.description if product.description else ""
                )
            )

    def add_product(self) -> None:
        """Добавление нового изделия"""
        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Добавление изделия")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Номер изделия:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        number_entry = ctk.CTkEntry(form_frame, width=250)
        number_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Тип изделия:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        type_entry = ctk.CTkEntry(form_frame, width=250)
        type_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Доп. номер:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        additional_entry = ctk.CTkEntry(form_frame, width=250)
        additional_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Описание:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        description_entry = ctk.CTkTextbox(form_frame, width=250, height=80)
        description_entry.grid(row=3, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_product():
            # Проверка обязательных полей
            if not number_entry.get() or not type_entry.get():
                messagebox.showwarning("Внимание", "Необходимо указать номер и тип изделия")
                return

            # Создаем объект изделия и сохраняем
            from app.db.models import Product
            product = Product(
                product_number=number_entry.get(),
                product_type=type_entry.get(),
                additional_number=additional_entry.get() if additional_entry.get() else None,
                description=description_entry.get("1.0", tk.END).strip() or None
            )

            success, error = self.product_service.save_product(product)
            if success:
                dialog.destroy()
                self.load_products_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Изделие успешно добавлено")
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить изделие: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_product,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def edit_product(self, table) -> None:
        """Редактирование выбранного изделия"""
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите изделие для редактирования")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        product_id = int(values[0])

        # Получаем данные изделия из БД
        product = self.product_service.db.get_product_by_id(product_id)
        if not product:
            messagebox.showerror("Ошибка", f"Изделие с ID {product_id} не найдено")
            return

        # Создаем диалоговое окно
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Редактирование изделия")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Номер изделия:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        number_entry = ctk.CTkEntry(form_frame, width=250)
        number_entry.insert(0, product.product_number)
        number_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Тип изделия:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        type_entry = ctk.CTkEntry(form_frame, width=250)
        type_entry.insert(0, product.product_type)
        type_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Доп. номер:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        additional_entry = ctk.CTkEntry(form_frame, width=250)
        if product.additional_number:
            additional_entry.insert(0, product.additional_number)
        additional_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(form_frame, text="Описание:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        description_entry = ctk.CTkTextbox(form_frame, width=250, height=80)
        if product.description:
            description_entry.insert("1.0", product.description)
        description_entry.grid(row=3, column=1, sticky="ew", pady=(0, 5))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_product_changes():
            # Проверка обязательных полей
            if not number_entry.get() or not type_entry.get():
                messagebox.showwarning("Внимание", "Необходимо указать номер и тип изделия")
                return

            # Обновляем объект изделия
            product.product_number = number_entry.get()
            product.product_type = type_entry.get()
            product.additional_number = additional_entry.get() if additional_entry.get() else None
            product.description = description_entry.get("1.0", tk.END).strip() or None

            success, error = self.product_service.save_product(product)
            if success:
                dialog.destroy()
                self.load_products_data()  # Обновляем таблицу
                messagebox.showinfo("Успех", "Данные изделия успешно обновлены")
            else:
                messagebox.showerror("Ошибка", f"Не удалось обновить данные изделия: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_product_changes,
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        cancel_btn.pack(side=tk.RIGHT)

    def delete_product(self, table) -> None:
        """Удаление выбранного изделия"""
        # Получаем выбранную строку
        selection = table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите изделие для удаления")
            return

        # Получаем данные из выбранной строки
        item = table.item(selection[0])
        values = item["values"]
        product_id = int(values[0])
        product_name = f"{values[1]} {values[2]}"

        # Подтверждение удаления
        if not messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить изделие '{product_name}'?"):
            return

        # Удаляем изделие
        success, error = self.product_service.delete_product(product_id)
        if success:
            self.load_products_data()  # Обновляем таблицу
            messagebox.showinfo("Успех", f"Изделие '{product_name}' успешно удалено")
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить изделие: {error}")

    def setup_contracts_tab(self, tab) -> None:
        """Настройка вкладки 'Контракты'"""
        # Аналогично предыдущим вкладкам
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(10, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить контракт",
            command=self.add_contract,
            **BUTTON_STYLE
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=lambda: self.edit_contract(self.contracts_table),
            **BUTTON_STYLE
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=lambda: self.delete_contract(self.contracts_table),
            fg_color=COLOR_SCHEME["error"],
            hover_color="#D32F2F"
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица контрактов
        table_frame = ctk.CTkFrame(tab, **FRAME_STYLE)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "contract_number", "description", "start_date", "end_date")

        self.contracts_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.contracts_table.heading("id", text="ID")
        self.contracts_table.heading("contract_number", text="Номер контракта")
        self.contracts_table.heading("description", text="Описание")
        self.contracts_table.heading("start_date", text="Дата начала")
        self.contracts_table.heading("end_date", text="Дата окончания")

        self.contracts_table.column("id", width=50, anchor="center")
        self.contracts_table.column("contract_number", width=150)
        self.contracts_table.column("description", width=250)
        self.contracts_table.column("start_date", width=100, anchor="center")
        self.contracts_table.column("end_date", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.contracts_table.yview)
        self.contracts_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.contracts_table.pack(fill=tk.BOTH, expand=True)

        # Загружаем данные
        self.load_contracts_data()

        # Привязываем двойной клик для редактирования
        self.contracts_table.bind("<Double-1>", lambda e: self.edit_contract(self.contracts_table))