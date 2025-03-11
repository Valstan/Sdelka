"""
Основной класс GUI приложения.
Определяет главное окно и управляет взаимодействием между различными формами.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging
from typing import Optional, Dict, Any, List

from app.config import UI_SETTINGS, APP_TITLE, REPORT_SETTINGS
from app.db.db_manager import DatabaseManager
from app.services.card_service import CardService
from app.services.report_service import ReportService
from app.gui.card_form import CardForm
from app.gui.report_form import ReportForm
from app.gui.styles import init_app_styles

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
        self.report_service = ReportService(db_manager)

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
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
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
            hover_color=UI_SETTINGS['error_hover']
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица работников
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "last_name", "first_name", "middle_name", "position")
        workers_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        workers_table.heading("id", text="ID")
        workers_table.heading("last_name", text="Фамилия")
        workers_table.heading("first_name", text="Имя")
        workers_table.heading("middle_name", text="Отчество")
        workers_table.heading("position", text="Должность")

        workers_table.column("id", width=50, anchor="center")
        workers_table.column("last_name", width=150)
        workers_table.column("first_name", width=150)
        workers_table.column("middle_name", width=150)
        workers_table.column("position", width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=workers_table.yview)
        workers_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        workers_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        workers = self.card_service.worker_service.get_all_workers()
        for worker in workers:
            workers_table.insert(
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

# Остальные методы и вспомогательные функции

    def add_worker(self) -> None:
        """Добавление нового работника"""
        # Создание диалогового окна
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Добавление работника")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Фамилия:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        last_name_entry = ctk.CTkEntry(form_frame, width=250)
        last_name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Имя:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        first_name_entry = ctk.CTkEntry(form_frame, width=250)
        first_name_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Отчество:").grid(row=2, column=0, sticky="w", pady=(0, 10))
        middle_name_entry = ctk.CTkEntry(form_frame, width=250)
        middle_name_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Должность:").grid(row=3, column=0, sticky="w", pady=(0, 10))
        position_entry = ctk.CTkEntry(form_frame, width=250)
        position_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_worker():
            if not last_name_entry.get() or not first_name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо заполнить Фамилию и Имя")
                return

            from app.db.models import Worker
            worker = Worker(
                last_name=last_name_entry.get(),
                first_name=first_name_entry.get(),
                middle_name=middle_name_entry.get(),
                position=position_entry.get()
            )

            success, error = self.card_service.worker_service.save_worker(worker)
            if success:
                dialog.destroy()
                self.load_workers_data()
                messagebox.showinfo("Успех", "Работник успешно добавлен")
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить работника: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_worker,
            **UI_SETTINGS['button_style']
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['error_hover']
        )
        cancel_btn.pack(side=tk.RIGHT)

    def edit_selected_worker(self) -> None:
        """Редактирование выбранного работника"""
        selection = self.workers_table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите работника для редактирования")
            return

        item = self.workers_table.item(selection[0])
        worker_id = int(item["values"][0])

        worker = self.card_service.worker_service.get_worker_by_id(worker_id)
        if not worker:
            messagebox.showerror("Ошибка", f"Работник с ID {worker_id} не найден")
            return

        # Создание диалогового окна
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Редактирование работника")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Фамилия:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        last_name_entry = ctk.CTkEntry(form_frame, width=250)
        last_name_entry.insert(0, worker.last_name)
        last_name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Имя:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        first_name_entry = ctk.CTkEntry(form_frame, width=250)
        first_name_entry.insert(0, worker.first_name)
        first_name_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Отчество:").grid(row=2, column=0, sticky="w", pady=(0, 10))
        middle_name_entry = ctk.CTkEntry(form_frame, width=250)
        if worker.middle_name:
            middle_name_entry.insert(0, worker.middle_name)
        middle_name_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Должность:").grid(row=3, column=0, sticky="w", pady=(0, 10))
        position_entry = ctk.CTkEntry(form_frame, width=250)
        if worker.position:
            position_entry.insert(0, worker.position)
        position_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def update_worker():
            if not last_name_entry.get() or not first_name_entry.get():
                messagebox.showwarning("Внимание", "Необходимо заполнить Фамилию и Имя")
                return

            worker.last_name = last_name_entry.get()
            worker.first_name = first_name_entry.get()
            worker.middle_name = middle_name_entry.get() if middle_name_entry.get() else None
            worker.position = position_entry.get() if position_entry.get() else None

            success, error = self.card_service.worker_service.save_worker(worker)
            if success:
                dialog.destroy()
                self.load_workers_data()
                messagebox.showinfo("Успех", "Данные работника успешно обновлены")
            else:
                messagebox.showerror("Ошибка", f"Не удалось обновить данные работника: {error}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Обновить",
            command=update_worker,
            **UI_SETTINGS['button_style']
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['error_hover']
        )
        cancel_btn.pack(side=tk.RIGHT)

    def delete_selected_worker(self) -> None:
        """Удаление выбранного работника"""
        selection = self.workers_table.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите работника для удаления")
            return

        item = self.workers_table.item(selection[0])
        worker_id = int(item["values"][0])

        if messagebox.askyesno("Подтверждение", f"Удалить работника {item['values'][1]} {item['values'][2]}?"):
            success, error = self.card_service.worker_service.delete_worker(worker_id)
            if success:
                self.load_workers_data()
                messagebox.showinfo("Успех", "Работник успешно удален")
            else:
                messagebox.showerror("Ошибка", f"Не удалось удалить работника: {error}")

    def load_workers_data(self) -> None:
        """Загрузка данных о работниках в таблицу"""
        workers = self.card_service.worker_service.get_all_workers()
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

    def setup_work_types_tab(self, tab) -> None:
        """Настройка вкладки "Виды работ" """
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить вид работы",
            command=self.add_work_type,
            **UI_SETTINGS['button_style']
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=self.edit_selected_work_type,
            **UI_SETTINGS['button_style']
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=self.delete_selected_work_type,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['error_hover']
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица видов работ
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "price", "description")
        self.work_types_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.work_types_table.heading("id", text="ID")
        self.work_types_table.heading("name", text="Наименование")
        self.work_types_table.heading("price", text="Цена")
        self.work_types_table.heading("description", text="Описание")

        self.work_types_table.column("id", width=50, anchor="center")
        self.work_types_table.column("name", width=200)
        self.work_types_table.column("price", width=100, anchor="e")
        self.work_types_table.column("description", width=300)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.work_types_table.yview)
        self.work_types_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.work_types_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        work_types = self.card_service.work_type_service.get_all_work_types()
        for work_type in work_types:
            self.work_types_table.insert(
                "", "end",
                values=(
                    work_type.id,
                    work_type.name,
                    work_type.price,
                    work_type.description if work_type.description else ""
                )
            )

    def add_work_type(self) -> None:
        """Добавление нового вида работы"""
        # Реализация добавления вида работы
        pass

    def edit_selected_work_type(self) -> None:
        """Редактирование выбранного вида работы"""
        # Реализация редактирования вида работы
        pass

    def delete_selected_work_type(self) -> None:
        """Удаление выбранного вида работы"""
        # Реализация удаления вида работы
        pass

    def setup_products_tab(self, tab) -> None:
        """Настройка вкладки "Изделия" """
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить изделие",
            command=self.add_product,
            **UI_SETTINGS['button_style']
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=self.edit_selected_product,
            **UI_SETTINGS['button_style']
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=self.delete_selected_product,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['error_hover']
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица изделий
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "product_number", "product_type", "additional_number", "description")
        self.products_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.products_table.heading("id", text="ID")
        self.products_table.heading("product_number", text="Номер")
        self.products_table.heading("product_type", text="Тип")
        self.products_table.heading("additional_number", text="Доп. номер")
        self.products_table.heading("description", text="Описание")

        self.products_table.column("id", width=50, anchor="center")
        self.products_table.column("product_number", width=100)
        self.products_table.column("product_type", width=150)
        self.products_table.column("additional_number", width=100)
        self.products_table.column("description", width=300)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.products_table.yview)
        self.products_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.products_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        products = self.card_service.product_service.get_all_products()
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
        # Реализация добавления изделия
        pass

    def edit_selected_product(self) -> None:
        """Редактирование выбранного изделия"""
        # Реализация редактирования изделия
        pass

    def delete_selected_product(self) -> None:
        """Удаление выбранного изделия"""
        # Реализация удаления изделия
        pass

    def setup_contracts_tab(self, tab) -> None:
        """Настройка вкладки "Контракты" """
        # Кнопки действий
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить контракт",
            command=self.add_contract,
            **UI_SETTINGS['button_style']
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Редактировать",
            command=self.edit_selected_contract,
            **UI_SETTINGS['button_style']
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Удалить",
            command=self.delete_selected_contract,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['error_hover']
        )
        delete_btn.pack(side=tk.LEFT)

        # Таблица контрактов
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True)

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
        self.contracts_table.column("description", width=300)
        self.contracts_table.column("start_date", width=100, anchor="center")
        self.contracts_table.column("end_date", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.contracts_table.yview)
        self.contracts_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.contracts_table.pack(fill=tk.BOTH, expand=True)

        # Загрузка данных
        contracts = self.card_service.contract_service.get_all_contracts()
        for contract in contracts:
            self.contracts_table.insert(
                "", "end",
                values=(
                    contract.id,
                    contract.contract_number,
                    contract.description if contract.description else "",
                    contract.start_date.strftime("%d.%m.%Y") if contract.start_date else "",
                    contract.end_date.strftime("%d.%m.%Y") if contract.end_date else ""
                )
            )

    def add_contract(self) -> None:
        """Добавление нового контракта"""
        # Реализация добавления контракта
        pass

    def edit_selected_contract(self) -> None:
        """Редактирование выбранного контракта"""
        # Реализация редактирования контракта
        pass

    def delete_selected_contract(self) -> None:
        """Удаление выбранного контракта"""
        # Реализация удаления контракта
        pass