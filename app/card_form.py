"""
Форма для создания и редактирования карточек работ.
Позволяет добавлять виды работ и работников, а также рассчитывать суммы.
"""
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Callable

import customtkinter as ctk

from app.autocomplete import AutocompleteCombobox
from app.config import UI_SETTINGS
from app.models import WorkCard
from app.services.card_service import CardService


class CardForm:
    """
    Форма для создания и редактирования карточек работ.
    Позволяет добавлять виды работ и работников, а также рассчитывать суммы.
    """

    def __init__(self,
                parent: ctk.CTkFrame,
                card_service: CardService,
                card: WorkCard,
                on_save: Callable[[], None] = None,
                on_cancel: Callable[[], None] = None):
        """
        Инициализация формы карточки работ.

        Args:
            parent: Родительский виджет
            card_service: Сервис для работы с карточками
            card: Карточка работ для редактирования
            on_save: Функция обратного вызова при сохранении
            on_cancel: Функция обратного вызова при отмене
        """
        self.parent = parent
        self.card_service = card_service
        self.card = card
        self.on_save = on_save
        self.on_cancel = on_cancel

        # Создаем интерфейс
        self.setup_ui()

        # Заполняем форму данными карточки
        self.load_card_data()

    def setup_ui(self) -> None:
        """Создание интерфейса формы"""
        # Верхняя часть с общей информацией о карточке
        self.header_frame = ctk.CTkFrame(self.parent, **UI_SETTINGS['card_frame'])
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        # Заголовок формы
        title_text = f"Карточка работ №{self.card.card_number}" if self.card.id else "Новая карточка работ"
        title_label = ctk.CTkLabel(
            self.header_frame,
            text=title_text,
            **UI_SETTINGS['header_style']
        )
        title_label.pack(side=tk.LEFT)

        # Кнопки действий
        self.buttons_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.buttons_frame.pack(side=tk.RIGHT)

        save_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Сохранить",
            command=self.save_card,
            **UI_SETTINGS['button_style']
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Отмена",
            command=self.cancel,
            fg_color=UI_SETTINGS['error_color'],
            hover_color=UI_SETTINGS['button_style']['hover_color']
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Форма с основными полями карточки
        self.form_frame = ctk.CTkFrame(self.parent, **UI_SETTINGS['card_frame'])
        self.form_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # 1-я строка: Номер карточки и дата
        row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row1.pack(fill=tk.X, padx=10, pady=(10, 5))

        ctk.CTkLabel(row1, text="Номер карточки:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.card_number_label = ctk.CTkLabel(
            row1,
            text=str(self.card.card_number),
            font=UI_SETTINGS['default_font']
        )
        self.card_number_label.pack(side=tk.LEFT, padx=(0, 20))

        ctk.CTkLabel(row1, text="Дата:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Фрейм для даты с выпадающими списками
        date_frame = ctk.CTkFrame(row1, fg_color="transparent")
        date_frame.pack(side=tk.LEFT)

        self.day_combo = ctk.CTkComboBox(
            date_frame, width=60, values=[str(i) for i in range(1, 32)]
        )
        self.day_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.month_combo = ctk.CTkComboBox(
            date_frame, width=60, values=[str(i) for i in range(1, 13)]
        )
        self.month_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.year_combo = ctk.CTkComboBox(
            date_frame, width=80, values=[str(i) for i in range(2000, 2051)]
        )
        self.year_combo.pack(side=tk.LEFT)

        # Устанавливаем текущую дату, если это новая карточка
        current_date = self.card.card_date if self.card.card_date else date.today()
        self.day_combo.set(str(current_date.day))
        self.month_combo.set(str(current_date.month))
        self.year_combo.set(str(current_date.year))

        # 2-я строка: Изделие
        row2 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row2.pack(fill=tk.X, padx=10, pady=(0, 10))

        ctk.CTkLabel(row2, text="Изделие:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для изделий
        self.product_combo = AutocompleteCombobox(
            row2,
            search_function=self.search_products,
            display_key="full_name",
            width=300
        )
        self.product_combo.pack(side=tk.LEFT)

        # 3-я строка: Контракт
        row3 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row3.pack(fill=tk.X, padx=10, pady=(0, 10))

        ctk.CTkLabel(row3, text="Контракт:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для контрактов
        self.contract_combo = AutocompleteCombobox(
            row3,
            search_function=self.search_contracts,
            display_key="contract_number",
            width=300
        )
        self.contract_combo.pack(side=tk.LEFT)

        # Разделяем форму на две колонки: виды работ и работники
        split_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        split_frame.pack(fill=tk.BOTH, expand=True)

        # Левая колонка: виды работ
        left_column = ctk.CTkFrame(split_frame, fg_color="transparent")
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Заголовок для видов работ
        work_types_header = ctk.CTkFrame(left_column, fg_color="transparent")
        work_types_header.pack(fill=tk.X, pady=(0, 5))

        ctk.CTkLabel(
            work_types_header,
            text="Виды работ",
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
        ).pack(side=tk.LEFT)

        # Кнопка "Добавить вид работы"
        add_work_btn = ctk.CTkButton(
            work_types_header,
            text="Добавить вид работы",
            command=self.add_work_type,
            **UI_SETTINGS['button_style']
        )
        add_work_btn.pack(side=tk.RIGHT)

        # Таблица для видов работ
        work_types_frame = ctk.CTkFrame(left_column, **UI_SETTINGS['card_frame'])
        work_types_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "quantity", "price", "amount")

        self.work_types_table = ttk.Treeview(
            work_types_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настройка заголовков
        self.work_types_table.heading("id", text="ID")
        self.work_types_table.heading("name", text="Наименование")
        self.work_types_table.heading("quantity", text="Количество")
        self.work_types_table.heading("price", text="Цена")
        self.work_types_table.heading("amount", text="Сумма")

        # Настройка ширин столбцов
        self.work_types_table.column("id", width=50, anchor="center")
        self.work_types_table.column("name", width=200)
        self.work_types_table.column("quantity", width=100, anchor="center")
        self.work_types_table.column("price", width=100, anchor="e")
        self.work_types_table.column("amount", width=100, anchor="e")

        # Добавление прокрутки
        scrollbar = ttk.Scrollbar(work_types_frame, orient=tk.VERTICAL, command=self.work_types_table.yview)
        self.work_types_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.work_types_table.pack(fill=tk.BOTH, expand=True)

        # Правый клик по таблице для удаления вида работы
        self.work_types_table.bind("<Button-3>", self.show_work_type_menu)

        # Правая колонка: работники
        right_column = ctk.CTkFrame(split_frame, fg_color="transparent")
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Заголовок для работников
        workers_header = ctk.CTkFrame(right_column, fg_color="transparent")
        workers_header.pack(fill=tk.X, pady=(0, 5))

        ctk.CTkLabel(
            workers_header,
            text="Работники",
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
        ).pack(side=tk.LEFT)

        # Кнопка "Добавить работника"
        add_worker_btn = ctk.CTkButton(
            workers_header,
            text="Добавить работника",
            command=self.add_worker,
            **UI_SETTINGS['button_style']
        )
        add_worker_btn.pack(side=tk.RIGHT)

        # Таблица для работников
        workers_frame = ctk.CTkFrame(right_column, **UI_SETTINGS['card_frame'])
        workers_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "amount")

        self.workers_table = ttk.Treeview(
            workers_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настройка заголовков
        self.workers_table.heading("id", text="ID")
        self.workers_table.heading("name", text="ФИО")
        self.workers_table.heading("amount", text="Сумма")

        # Настройка ширин столбцов
        self.workers_table.column("id", width=50, anchor="center")
        self.workers_table.column("name", width=250)
        self.workers_table.column("amount", width=100, anchor="e")

        # Добавление прокрутки
        scrollbar = ttk.Scrollbar(workers_frame, orient=tk.VERTICAL, command=self.workers_table.yview)
        self.workers_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.workers_table.pack(fill=tk.BOTH, expand=True)

        # Правый клик по таблице для удаления работника
        self.workers_table.bind("<Button-3>", self.show_worker_menu)

        # Нижняя панель с итоговой суммой
        footer_frame = ctk.CTkFrame(self.parent, **UI_SETTINGS['card_frame'])
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        ctk.CTkLabel(
            footer_frame,
            text="Итоговая сумма:",
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.total_amount_label = ctk.CTkLabel(
            footer_frame,
            text="0.00 руб.",
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
        )
        self.total_amount_label.pack(side=tk.RIGHT, padx=10, pady=10)

    def search_products(self, search_text: str) -> List[Dict[str, Any]]:
        products = self.card_service.product_service.search_products(search_text)
        result = [{"id": 0, "full_name": "Все изделия"}]  # Опция "Все изделия"
        for product in products:
            full_name = f"{product.product_number} {product.product_type}"
            if product.additional_number:
                full_name += f" ({product.additional_number})"
            result.append({
                "id": product.id,
                "full_name": full_name
            })
        return result

    def search_contracts(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск контрактов для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            Список контрактов в формате для автокомплита
        """
        contracts = self.card_service.contract_service.search_contracts(search_text)

        result = [{"id": 0, "contract_number": "Все контракты"}]  # Опция "Все контракты"

        for contract in contracts:
            result.append({
                "id": contract.id,
                "contract_number": contract.contract_number
            })

        return result

    def load_card_data(self) -> None:
        """Загрузка данных карточки в форму"""
        # Устанавливаем изделие, если оно выбрано
        if self.card.product_id:
            product = self.card_service.product_service.get_product_by_id(self.card.product_id)
            if product:
                full_name = f"{product.product_number} {product.product_type}"
                if product.additional_number:
                    full_name += f" ({product.additional_number})"
                self.product_combo.set(full_name)

        # Устанавливаем контракт, если он выбран
        if self.card.contract_id:
            contract = self.card_service.contract_service.get_contract_by_id(self.card.contract_id)
            if contract:
                self.contract_combo.set(contract.contract_number)

        # Загружаем виды работ
        self.load_work_types()

        # Загружаем работников
        self.load_workers()

        # Обновляем итоговую сумму
        self.update_total_amount()

    def load_work_types(self) -> None:
        """Загрузка видов работ карточки в таблицу"""
        # Очищаем таблицу
        for item in self.work_types_table.get_children():
            self.work_types_table.delete(item)

        # Добавляем виды работ из карточки
        for item in self.card.items:
            self.work_types_table.insert(
                "", "end",
                values=(
                    item.work_type_id,
                    item.work_name,
                    item.quantity,
                    f"{item.price:.2f}" if item.price else "0.00",
                    f"{item.amount:.2f}"
                )
            )

    def load_workers(self) -> None:
        """Загрузка работников карточки в таблицу"""
        # Очищаем таблицу
        for item in self.workers_table.get_children():
            self.workers_table.delete(item)

        # Добавляем работников из карточки
        for worker in self.card.workers:
            full_name = f"{worker.last_name} {worker.first_name}"
            if worker.middle_name:
                full_name += f" {worker.middle_name}"

            self.workers_table.insert(
                "", "end",
                values=(
                    worker.worker_id,
                    full_name,
                    f"{worker.amount:.2f}"
                )
            )

    def add_work_type(self) -> None:
        """Добавление вида работы в карточку"""
        # Создание диалогового окна
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Добавление вида работы")
        dialog.geometry("400x200")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Вид работы:").grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Автозаполняемый выпадающий список для видов работ
        work_type_combo = AutocompleteCombobox(
            form_frame,
            search_function=self.search_work_types,
            display_key="name",
            width=250
        )
        work_type_combo.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Количество:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        quantity_entry = ctk.CTkEntry(form_frame, width=250)
        quantity_entry.insert(0, "1")
        quantity_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_work_type():
            # Проверка выбора вида работы
            selected_item = work_type_combo.get_selected_item()
            if not selected_item:
                messagebox.showwarning("Внимание", "Необходимо выбрать вид работы")
                return

            # Проверка количества
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    messagebox.showwarning("Внимание", "Количество должно быть положительным числом")
                    return
            except ValueError:
                messagebox.showwarning("Внимание", "Количество должно быть целым числом")
                return

            # Добавляем вид работы в карточку
            try:
                self.card_service.add_work_item(self.card, selected_item["id"], quantity)

                # Обновляем отображение
                self.load_work_types()
                self.update_total_amount()

                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить вид работы: {str(e)}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить",
            command=save_work_type,
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

    def search_work_types(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск видов работ для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            Список видов работ в формате для автокомплита
        """
        work_types = self.card_service.work_type_service.search_work_types(search_text)

        result = [{"id": 0, "name": "Все виды работ"}]  # Опция "Все виды работ"

        for work_type in work_types:
            result.append({
                "id": work_type.id,
                "name": work_type.name
            })

        return result

    def show_work_type_menu(self, event) -> None:
        """
        Показывает контекстное меню для таблицы видов работ.

        Args:
            event: Событие щелчка правой кнопкой мыши
        """
        # Получаем выбранную строку
        selection = self.work_types_table.selection()
        if not selection:
            return

        # Показываем контекстное меню
        self.work_type_menu.post(event.x_root, event.y_root)

    def remove_work_type(self) -> None:
        """Удаление выбранного вида работы из карточки"""
        # Получаем выбранную строку
        selection = self.work_types_table.selection()
        if not selection:
            return

        # Получаем индекс вида работы в списке
        item_id = int(self.work_types_table.item(selection[0])["values"][0])

        # Находим индекс элемента в списке
        for i, item in enumerate(self.card.items):
            if item.work_type_id == item_id:
                # Удаляем элемент
                del self.card.items[i]
                break

        # Обновляем отображение
        self.load_work_types()
        self.update_total_amount()

    def add_worker(self) -> None:
        """Добавление работника в карточку"""
        # Создание диалогового окна
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Добавление работника")
        dialog.geometry("400x150")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()

        # Делаем окно модальным
        dialog.focus_set()

        # Поля формы
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Работник:").grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Автозаполняемый выпадающий список для работников
        worker_combo = AutocompleteCombobox(
            form_frame,
            search_function=self.search_workers,
            display_key="full_name",
            width=250
        )
        worker_combo.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        def save_worker():
            # Проверка выбора работника
            selected_item = worker_combo.get_selected_item()
            if not selected_item:
                messagebox.showwarning("Внимание", "Необходимо выбрать работника")
                return

            # Добавляем работника в карточку
            try:
                self.card_service.add_worker(self.card, selected_item["id"])

                # Обновляем отображение
                self.load_workers()
                self.update_total_amount()

                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить работника: {str(e)}")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Добавить",
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

    def search_workers(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск работников для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            Список работников в формате для автокомплита
        """
        workers = self.card_service.worker_service.search_workers(search_text)

        result = [{"id": 0, "full_name": "Все работники"}]  # Опция "Все работники"

        for worker in workers:
            full_name = f"{worker.last_name} {worker.first_name}"
            if worker.middle_name:
                full_name += f" {worker.middle_name}"

            result.append({
                "id": worker.id,
                "full_name": full_name
            })

        return result

    def show_worker_menu(self, event) -> None:
        """
        Показывает контекстное меню для таблицы работников.

        Args:
            event: Событие щелчка правой кнопкой мыши
        """
        # Получаем выбранную строку
        selection = self.workers_table.selection()
        if not selection:
            return

        # Показываем контекстное меню
        self.worker_menu.post(event.x_root, event.y_root)

    def remove_worker(self) -> None:
        """Удаление выбранного работника из карточки"""
        # Получаем выбранную строку
        selection = self.workers_table.selection()
        if not selection:
            return

        # Получаем индекс работника в списке
        worker_id = int(self.workers_table.item(selection[0])["values"][0])

        # Находим индекс элемента в списке
        for i, worker in enumerate(self.card.workers):
            if worker.worker_id == worker_id:
                # Удаляем элемент
                del self.card.workers[i]
                break

        # Обновляем отображение
        self.load_workers()
        self.update_total_amount()

    def update_total_amount(self) -> None:
        """Обновление итоговой суммы карточки и распределение между работниками"""
        # Рассчитываем итоговую сумму карточки на основе элементов
        self.card.total_amount = self.card.calculate_total_amount()

        # Обновляем отображение суммы
        self.total_amount_label.configure(text=f"{self.card.total_amount:.2f} руб.")

        # Обновляем суммы работников в таблице
        if self.card.workers:
            worker_amount = self.card.total_amount / len(self.card.workers)
            for _, row in enumerate(self.workers_table.get_children()):
                worker_id = int(self.workers_table.item(row)["values"][0])
                for worker in self.card.workers:
                    if worker.worker_id == worker_id:
                        self.workers_table.item(
                            row,
                            values=(
                                worker_id,
                                self.workers_table.item(row)["values"][1],
                                f"{worker_amount:.2f}"
                            )
                        )
                        break

    def save_card(self) -> None:
        """Сохранение карточки работ"""
        # Проверяем наличие видов работ
        if not self.card.items:
            messagebox.showwarning("Внимание", "Добавьте хотя бы один вид работы")
            return

        # Проверяем наличие работников
        if not self.card.workers:
            messagebox.showwarning("Внимание", "Добавьте хотя бы одного работника")
            return

        # Получаем дату из выпадающих списках
        try:
            card_date = date(
                int(self.year_combo.get()),
                int(self.month_combo.get()),
                int(self.day_combo.get())
            )
            self.card.card_date = card_date
        except ValueError:
            messagebox.showwarning("Внимание", "Некорректная дата")
            return

        # Сохраняем карточку
        try:
            success, error = self.card_service.save_card(self.card)
            if success:
                messagebox.showinfo("Успех", "Карточка успешно сохранена")
                if self.on_save:
                    self.on_save()
            else:
                messagebox.showerror("Ошибка", f"Не удалось сохранить карточку: {error}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить карточку: {str(e)}")

    def cancel(self) -> None:
        """Отмена редактирования карточки"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите отменить редактирование?"):
            if self.on_cancel:
                self.on_cancel()
