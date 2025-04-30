# File: app/ui/work_card_form.py
"""
Форма для создания и редактирования карточек выполненных работ
"""

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple, Callable
from datetime import date
import customtkinter as ctk
from app.core.services.contract_service import ContractService
from app.core.services.product_service import ProductService
from app.core.services.work_card_service import WorkCardService
from app.ui.components.autocomplete import AutocompleteCombobox


class WorkCardForm(ctk.CTkFrame):
    """
    Форма для создания и редактирования карточек работ

    Attributes:
        card_id (Optional[int]): ID карточки для редактирования
        card_service (WorkCardService): Сервис для работы с карточками
        entry_fields (Dict[str, CTkEntry | Combobox]): Словарь полей ввода
        on_save_callback (Callable): Callback-функция после сохранения
    """

    def __init__(self, parent, work_card_service: WorkCardService,
                 product_service=None, contract_service=None, card_id: Optional[int] = None):
        """
        Инициализация формы карточки

        Args:
            parent: Родительский виджет
            work_card_service: Сервис для работы с карточками
            product_service: Сервис для работы с изделиями
            contract_service: Сервис для работы с контрактами
            card_id: ID карточки для редактирования
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        self.card_id = card_id
        self.card_service = work_card_service
        self.product_service = product_service or ProductService(self.card_service.db_path)
        self.contract_service = contract_service or ContractService(self.card_service.db_path)
        self.entry_fields = {}
        self.on_save_callback = None

        # Создаем интерфейс
        self._setup_ui()

        # Загружаем данные если это редактирование
        if card_id:
            self._load_card_data(card_id)
        else:
            self._set_default_values()

    def _setup_ui(self) -> None:
        """Настройка пользовательского интерфейса формы"""
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Первая строка: Номер и дата
        row1 = ctk.CTkFrame(form_frame)
        row1.pack(fill=tk.X, pady=(0, 10))

        # Номер карточки
        ctk.CTkLabel(row1, text="Номер:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["number"] = ctk.CTkEntry(row1)
        self.entry_fields["number"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Дата карточки
        ctk.CTkLabel(row1, text="Дата:", width=40).pack(side=tk.LEFT, padx=(0, 5))
        self._setup_date_selector(row1)

        # Вторая строка: Изделие
        row2 = ctk.CTkFrame(form_frame)
        row2.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row2, text="Изделие:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["product"] = AutocompleteCombobox(
            row2,
            search_function=self.product_service.search_products,
            display_key="full_name"
        )
        self.entry_fields["product"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Третья строка: Контракт
        row3 = ctk.CTkFrame(form_frame)
        row3.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row3, text="Контракт:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["contract"] = AutocompleteCombobox(
            row3,
            search_function=self.contract_service.search_contracts,
            display_key="contract_number"
        )
        self.entry_fields["contract"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Четвертая строка: Общая сумма
        row4 = ctk.CTkFrame(form_frame)
        row4.pack(fill=tk.X, pady=(0, 20))

        ctk.CTkLabel(row4, text="Общая сумма:", width=100).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["total_amount"] = ctk.CTkEntry(row4)
        self.entry_fields["total_amount"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Пятая строка: Управление элементами работы
        items_frame = ctk.CTkFrame(form_frame)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Заголовок раздела
        ctk.CTkLabel(items_frame, text="Элементы работы", font=("Roboto", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Таблица элементов работы
        self.items_table = tk.Frame(items_frame)
        self.items_table.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления элементами
        items_btns = ctk.CTkFrame(items_frame)
        items_btns.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        add_item_btn = ctk.CTkButton(
            items_btns,
            text="Добавить",
            command=self._show_work_type_dialog,
            width=100
        )
        add_item_btn.pack(side=tk.LEFT, padx=(0, 5))

        remove_item_btn = ctk.CTkButton(
            items_btns,
            text="Удалить",
            command=self._remove_selected_item,
            width=100,
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        remove_item_btn.pack(side=tk.LEFT)

        # Шестая строка: Управление работниками
        workers_frame = ctk.CTkFrame(form_frame)
        workers_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Заголовок раздела
        ctk.CTkLabel(workers_frame, text="Работники", font=("Roboto", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Таблица работников
        self.workers_table = tk.Frame(workers_frame)
        self.workers_table.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления работниками
        workers_btns = ctk.CTkFrame(workers_frame)
        workers_btns.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        add_worker_btn = ctk.CTkButton(
            workers_btns,
            text="Добавить",
            command=self._show_worker_selection,
            width=100
        )
        add_worker_btn.pack(side=tk.LEFT, padx=(0, 5))

        remove_worker_btn = ctk.CTkButton(
            workers_btns,
            text="Удалить",
            command=self._remove_selected_worker,
            width=100,
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        remove_worker_btn.pack(side=tk.LEFT)

        # Седьмая строка: Кнопки сохранения
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=self.save,
            width=120
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=self.parent.destroy,
            width=120,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Привязываем событие Enter к кнопке сохранить
        self.bind("<Return>", lambda event: self.save())
        self.bind("<KP_Enter>", lambda event: self.save())

    def _setup_date_selector(self, parent) -> None:
        """Настройка выпадающих списков для выбора даты"""
        date_frame = ctk.CTkFrame(parent)
        date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Разбиваем дату на день, месяц, год
        parts = {
            "day": ctk.CTkComboBox(date_frame, values=[str(i) for i in range(1, 32)], width=60),
            "month": ctk.CTkComboBox(date_frame, values=[str(i) for i in range(1, 13)], width=60),
            "year": ctk.CTkComboBox(date_frame, values=[str(i) for i in range(2000, 2051)], width=80)
        }

        # Сохраняем ссылки на поля
        self.entry_fields["date_day"] = parts["day"]
        self.entry_fields["date_month"] = parts["month"]
        self.entry_fields["date_year"] = parts["year"]

        # Располагаем элементы даты
        for name, combo in parts.items():
            combo.pack(side=tk.LEFT, padx=(0, 5) if name != "year" else 0)

        # Устанавливаем значения по умолчанию
        current_date = date.today()
        parts["day"].set(str(current_date.day))
        parts["month"].set(str(current_date.month))
        parts["year"].set(str(current_date.year))

    def _load_card_data(self, card_id: int) -> None:
        """
        Загружает данные карточки из базы данных

        Args:
            card_id: ID карточки для загрузки
        """
        try:
            self.card = self.card_service.get_work_card_by_id(card_id)

            if not self.card:
                raise ValueError(f"Карточка с ID {card_id} не найдена")

            # Устанавливаем номер карточки
            self.entry_fields["number"].delete(0, tk.END)
            self.entry_fields["number"].insert(0, str(self.card.card_number))

            # Устанавливаем дату
            card_date = self.card.card_date or date.today()
            self.entry_fields["date_day"].set(str(card_date.day))
            self.entry_fields["date_month"].set(str(card_date.month))
            self.entry_fields["date_year"].set(str(card_date.year))

            # Устанавливаем изделие
            if self.card.product:
                self.entry_fields["product"].set(self.card.product.full_name)

            # Устанавливаем контракт
            if self.card.contract:
                self.entry_fields["contract"].set(self.card.contract.contract_number)

            # Устанавливаем общую сумму
            self.entry_fields["total_amount"].delete(0, tk.END)
            self.entry_fields["total_amount"].insert(0, f"{self.card.total_amount:.2f}")

            # Загружаем элементы работы
            self._update_items_table()

            # Загружаем работников
            self._update_workers_table()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных карточки: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные карточки: {str(e)}")

    def _set_default_values(self) -> None:
        """Устанавливает значения по умолчанию для новой карточки"""
        try:
            # Автоматически генерируемый номер
            next_number = self.card_service.get_next_card_number()
            self.entry_fields["number"].delete(0, tk.END)
            self.entry_fields["number"].insert(0, str(next_number))

            # Текущая дата
            today = date.today()
            self.entry_fields["date_day"].set(str(today.day))
            self.entry_fields["date_month"].set(str(today.month))
            self.entry_fields["date_year"].set(str(today.year))

            # Инициализируем пустую карточку
            self.card = self.card_service.create_new_card()

        except Exception as e:
            self.logger.error(f"Ошибка установки значений по умолчанию: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось установить значения по умолчанию: {str(e)}")

    def _validate_date(self) -> date:
        """
        Валидирует и возвращает дату

        Returns:
            Объект даты
        """
        day = self.entry_fields["date_day"].get()
        month = self.entry_fields["date_month"].get()
        year = self.entry_fields["date_year"].get()

        try:
            return date(int(year), int(month), int(day))
        except ValueError as e:
            raise ValueError(f"Некорректная дата: {e}")

    def validate(self) -> bool:
        """
        Валидирует введенные данные

        Returns:
            True если данные корректны, False в противном случае
        """
        try:
            # Проверяем наличие хотя бы одного элемента работы
            if not self.card.items:
                messagebox.showwarning("Предупреждение", "Добавьте хотя бы один элемент работы")
                return False

            # Проверяем наличие хотя бы одного работника
            if not self.card.workers:
                messagebox.showwarning("Предупреждение", "Добавьте хотя бы одного работника")
                return False

            # Проверяем уникальность номера карточки
            number = int(self.entry_fields["number"].get())
            existing = self.card_service.get_work_card_by_number(number)

            if existing and (existing.id != self.card.id if self.card else False):
                messagebox.showwarning("Предупреждение", "Карточка с таким номером уже существует")
                return False

            # Проверяем дату
            try:
                self._validate_date()
            except ValueError as e:
                messagebox.showwarning("Предупреждение", str(e))
                return False

            # Проверяем дополнительные связи
            if not self._validate_relations():
                return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка валидации карточки: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Ошибка при валидации: {str(e)}")
            return False

    def _validate_relations(self) -> bool:
        """
        Валидирует связи с изделием и контрактом

        Returns:
            True если связи корректны, False в противном случае
        """
        # Проверяем изделие
        if self.entry_fields["product"].selected_item:
            product = self.entry_fields["product"].selected_item
            self.card.product_id = product.id if isinstance(product, dict) else product["id"]

        # Проверяем контракт
        if self.entry_fields["contract"].selected_item:
            contract = self.entry_fields["contract"].selected_item
            self.card.contract_id = contract.id if isinstance(contract, dict) else contract["id"]

        return True

    def save(self) -> Tuple[bool, Optional[str]]:
        """
        Сохраняет или обновляет карточку

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        try:
            if not self.validate():
                return False, "Данные карточки некорректны"

            # Устанавливаем дату карточки
            self.card.card_date = self._validate_date()

            # Сохраняем карточку
            if self.card.id:
                result = self.card_service.update_work_card(self.card)
            else:
                result = self.card_service.save_card(self.card)

            success, message = result

            if success:
                messagebox.showinfo("Успех", "Карточка успешно сохранена")
                if self.on_save_callback:
                    self.on_save_callback()
            else:
                messagebox.showerror("Ошибка", message)

            return result

        except Exception as e:
            self.logger.error(f"Ошибка сохранения карточки: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось сохранить карточку: {str(e)}")
            return False, f"Ошибка сохранения карточки: {str(e)}"

    def _update_items_table(self) -> None:
        """Обновляет таблицу элементов работы"""
        try:
            for widget in self.items_table.winfo_children():
                widget.destroy()

            headers = ["ID", "Наименование", "Цена", "Количество", "Сумма"]
            for col, header in enumerate(headers):
                tk.Label(self.items_table, text=header, relief=tk.RIDGE, width=20).grid(
                    row=0, column=col, sticky="ew")

            if not self.card or not self.card.items:
                return

            for row_idx, item in enumerate(self.card.items):
                item_data = [
                    item.id,
                    item.work_name,
                    f"{item.price:.2f}",
                    item.quantity,
                    f"{item.amount:.2f}"
                ]

                for col_idx, value in enumerate(item_data):
                    tk.Label(self.items_table, text=value, relief=tk.RIDGE, width=20).grid(
                        row=row_idx + 1, column=col_idx, sticky="ew")

        except Exception as e:
            self.logger.error(f"Ошибка обновления таблицы элементов: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось обновить таблицу элементов: {str(e)}")

    def _update_workers_table(self) -> None:
        """Обновляет таблицу работников"""
        try:
            for widget in self.workers_table.winfo_children():
                widget.destroy()

            headers = ["ID", "ФИО", "Сумма"]
            for col, header in enumerate(headers):
                tk.Label(self.workers_table, text=header, relief=tk.RIDGE, width=20).grid(
                    row=0, column=col, sticky="ew")

            if not self.card or not self.card.workers:
                return

            # Получаем текущую сумму для каждого работника
            total_amount = self.card.total_amount
            worker_count = len(self.card.workers) or 1

            for row_idx, worker in enumerate(self.card.workers):
                worker_amount = total_amount / worker_count
                worker_data = [
                    worker.worker_id,
                    worker.full_name(),
                    f"{worker_amount:.2f}"
                ]

                for col_idx, value in enumerate(worker_data):
                    tk.Label(self.workers_table, text=value, relief=tk.RIDGE, width=20).grid(
                        row=row_idx + 1, column=col_idx, sticky="ew")

        except Exception as e:
            self.logger.error(f"Ошибка обновления таблицы работников: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось обновить таблицу работников: {str(e)}")

    def _show_work_type_dialog(self) -> None:
        """Показывает диалоговое окно для выбора вида работы"""
        dialog = tk.Toplevel(self)
        dialog.title("Добавить вид работы")
        dialog.geometry("500x300")

        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Поиск вида работы
        search_frame = ctk.CTkFrame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        work_type_search = AutocompleteCombobox(
            search_frame,
            search_function=self.card_service.get_all_work_types,
            display_key="name"
        )
        work_type_search.pack(fill=tk.X, expand=True)

        # Количество
        quantity_frame = ctk.CTkFrame(dialog)
        quantity_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(quantity_frame, text="Количество:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        quantity_entry = ctk.CTkEntry(quantity_frame)
        quantity_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки действия
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_work_type():
            """Сохраняет выбранный вид работы"""
            selected_item = work_type_search.selected_item
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите вид работы")
                return

            try:
                quantity = float(quantity_entry.get().replace(',', '.'))
                if quantity <= 0:
                    raise ValueError("Количество должно быть положительным числом")

                # Получаем ID вида работы
                work_type_id = selected_item.id if isinstance(selected_item, dict) else selected_item["id"]

                # Добавляем элемент работы
                success, error = self.card_service.add_work_item(self.card, work_type_id, quantity)

                if success:
                    self._update_items_table()
                    self._update_total_amount()
                    dialog.destroy()
                    self._update_workers_table()
                else:
                    messagebox.showerror("Ошибка", error)

            except ValueError as ve:
                messagebox.showwarning("Предупреждение", str(ve))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить",
            command=save_work_type,
            width=100
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            width=100,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Фокусируем окно
        dialog.grab_set()
        self.wait_window(dialog)

    def _show_worker_selection(self) -> None:
        """Показывает диалог для выбора работника"""
        dialog = tk.Toplevel(self)
        dialog.title("Выбор работника")
        dialog.geometry("500x300")

        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Поиск работника
        search_frame = ctk.CTkFrame(dialog)
        search_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        worker_search = AutocompleteCombobox(
            search_frame,
            search_function=self.card_service.get_all_workers,
            display_key="full_name"
        )
        worker_search.pack(fill=tk.BOTH, expand=True)

        # Кнопки действия
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_worker():
            """Сохраняет выбранного работника"""
            selected_item = worker_search.selected_item
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите работника")
                return

            # Получаем ID работника
            worker_id = selected_item.id if isinstance(selected_item, dict) else selected_item["id"]

            # Проверяем, нет ли уже этого работника в списке
            if any(w.worker_id == worker_id for w in self.card.workers):
                messagebox.showwarning("Предупреждение", "Этот работник уже добавлен")
                return

            # Добавляем работника
            success, error = self.card_service.add_worker(self.card, worker_id)

            if success:
                self._update_workers_table()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", error)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить",
            command=save_worker,
            width=100
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            width=100,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Фокусируем окно
        dialog.grab_set()
        self.wait_window(dialog)

    def _remove_selected_item(self) -> None:
        """Удаляет выбранный элемент работы"""
        selection = self.items_table.grid_slaves(row=len(self.card.items), column=0)
        if not selection:
            return

        if not messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот элемент?"):
            return

        item_id = int(selection[0].cget("text"))

        # Удаляем элемент
        success, error = self.card_service.remove_work_item(self.card, item_id)

        if success:
            self._update_items_table()
            self._update_total_amount()
            self._update_workers_table()
        else:
            messagebox.showerror("Ошибка", error)

    def _remove_selected_worker(self) -> None:
        """Удаляет выбранного работника"""
        selection = self.workers_table.grid_slaves(row=len(self.card.workers), column=0)
        if not selection:
            return

        if not messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этого работника?"):
            return

        worker_id = int(selection[0].cget("text"))

        # Удаляем работника
        success, error = self.card_service.remove_worker(self.card, worker_id)

        if success:
            self._update_workers_table()
            self._update_total_amount()
        else:
            messagebox.showerror("Ошибка", error)

    def _update_total_amount(self) -> None:
        """Обновляет общую сумму карточки"""
        try:
            # Пересчитываем общую сумму
            new_total = sum(item.amount for item in self.card.items)
            self.card.total_amount = new_total

            # Обновляем поле общей суммы
            self.entry_fields["total_amount"].delete(0, tk.END)
            self.entry_fields["total_amount"].insert(0, f"{new_total:.2f}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления общей суммы: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось обновить общую сумму: {str(e)}")

    def set_on_save(self, callback: Callable) -> None:
        """
        Устанавливает callback-функцию, которая будет вызвана после сохранения

        Args:
            callback: Callback-функция без аргументов
        """
        self.on_save_callback = callback

    def clear(self) -> None:
        """Очищает все поля формы"""
        for field in self.entry_fields.values():
            if isinstance(field, ctk.CTkComboBox):
                field.set("")
            elif hasattr(field, "delete"):
                field.delete(0, tk.END)

        # Очищаем таблицы
        for table in [self.items_table, self.workers_table]:
            for widget in table.winfo_children():
                widget.destroy()

        # Сбрасываем карточку
        self.card = self.card_service.create_new_card()