"""
Форма для создания отчетов.
Позволяет выбирать период, работников и другие параметры для формирования отчетов.
"""
import os
import tkinter as tk
import webbrowser
from datetime import datetime, date, timedelta
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Tuple

import customtkinter as ctk

from app.gui.autocomplete import AutocompleteCombobox
from app.gui.styles import COLOR_SCHEME, BUTTON_STYLE, FRAME_STYLE, LABEL_STYLE
from app.services.card_service import WorkerService, WorkTypeService, ProductService, ContractService
from app.services.report_service import ReportService

import pandas as pd  # Добавляем импорт pandas
import traceback  # Для подробного вывода ошибок


class ReportForm:
    """
    Форма для создания отчетов по работе сотрудников.
    """

    def __init__(self,
                parent: ctk.CTkFrame,
                report_service: ReportService,
                worker_service: WorkerService,
                work_type_service: WorkTypeService,
                product_service: ProductService,
                contract_service: ContractService):
        """
        Инициализация формы отчетов.

        Args:
            parent: Родительский виджет
            report_service: Сервис для работы с отчетами
            worker_service: Сервис для работы с работниками
            work_type_service: Сервис для работы с видами работ
            product_service: Сервис для работы с изделиями
            contract_service: Сервис для работы с контрактами
        """
        self.parent = parent
        self.report_service = report_service
        self.worker_service = worker_service
        self.work_type_service = work_type_service
        self.product_service = product_service
        self.contract_service = contract_service

        # Создаем интерфейс
        self.setup_ui()

    def setup_ui(self) -> None:
        """Создание интерфейса формы"""
        # Фрейм с фильтрами отчета
        self.filters_frame = ctk.CTkFrame(self.parent, **FRAME_STYLE)
        self.filters_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Заголовок "Параметры отчета"
        filters_label = ctk.CTkLabel(
            self.filters_frame,
            text="Параметры отчета",
            font=("Roboto", 14, "bold"),
            text_color=COLOR_SCHEME["text"]
        )
        filters_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Фрейм с фильтрами в две колонки
        form_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        form_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Первая колонка фильтров
        left_column = ctk.CTkFrame(form_frame, fg_color="transparent")
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Период отчета
        period_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        period_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(period_frame, text="Период:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Выпадающий список с предопределенными периодами
        self.period_combo = ctk.CTkComboBox(
            period_frame,
            values=[
                "Текущий месяц",
                "Прошлый месяц",
                "Текущий квартал",
                "Прошлый квартал",
                "Текущий год",
                "Произвольный период"
            ],
            command=self.on_period_changed
        )
        self.period_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.period_combo.set("Текущий месяц")

        # Фрейм для дат (скрыт по умолчанию)
        self.dates_frame = ctk.CTkFrame(left_column, fg_color="transparent")

        # От даты
        from_date_frame = ctk.CTkFrame(self.dates_frame, fg_color="transparent")
        from_date_frame.pack(fill=tk.X, pady=(0, 5))

        ctk.CTkLabel(from_date_frame, text="От:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Выпадающие списки для даты "от"
        self.from_day = ctk.CTkComboBox(from_date_frame, width=60, values=[str(i) for i in range(1, 32)])
        self.from_day.pack(side=tk.LEFT, padx=(0, 5))

        self.from_month = ctk.CTkComboBox(from_date_frame, width=60, values=[str(i) for i in range(1, 13)])
        self.from_month.pack(side=tk.LEFT, padx=(0, 5))

        self.from_year = ctk.CTkComboBox(from_date_frame, width=80,
                                      values=[str(i) for i in range(2000, 2051)])
        self.from_year.pack(side=tk.LEFT)

        # До даты
        to_date_frame = ctk.CTkFrame(self.dates_frame, fg_color="transparent")
        to_date_frame.pack(fill=tk.X)

        ctk.CTkLabel(to_date_frame, text="До:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Выпадающие списки для даты "до"
        self.to_day = ctk.CTkComboBox(to_date_frame, width=60, values=[str(i) for i in range(1, 32)])
        self.to_day.pack(side=tk.LEFT, padx=(0, 5))

        self.to_month = ctk.CTkComboBox(to_date_frame, width=60, values=[str(i) for i in range(1, 13)])
        self.to_month.pack(side=tk.LEFT, padx=(0, 5))

        self.to_year = ctk.CTkComboBox(to_date_frame, width=80,
                                    values=[str(i) for i in range(2000, 2051)])
        self.to_year.pack(side=tk.LEFT)

        # Устанавливаем текущие даты периода
        self.set_default_period_dates()

        # Работник
        worker_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        worker_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(worker_frame, text="Работник:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для работников
        self.worker_combo = AutocompleteCombobox(
            worker_frame,
            search_function=self.search_workers,
            display_key="full_name",
            width=250
        )
        self.worker_combo.pack(side=tk.LEFT)

        # Вторая колонка фильтров
        right_column = ctk.CTkFrame(form_frame, fg_color="transparent")
        right_column.pack(side=tk.LEFT, fill=tk.Y)

        # Вид работы
        work_type_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        work_type_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(work_type_frame, text="Вид работы:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для видов работ
        self.work_type_combo = AutocompleteCombobox(
            work_type_frame,
            search_function=self.search_work_types,
            display_key="name",
            value_key="id",
            width=250
        )
        self.work_type_combo.pack(side=tk.LEFT)

        # Изделие
        product_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        product_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(product_frame, text="Изделие:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для изделий
        self.product_combo = AutocompleteCombobox(
            product_frame,
            search_function=self.search_products,
            display_key="full_name",
            value_key="id",
            width=250
        )
        self.product_combo.pack(side=tk.LEFT)

        # Контракт
        contract_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        contract_frame.pack(fill=tk.X)

        ctk.CTkLabel(contract_frame, text="Контракт:", **LABEL_STYLE).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для контрактов
        self.contract_combo = AutocompleteCombobox(
            contract_frame,
            search_function=self.search_contracts,
            display_key="contract_number",
            value_key="id",
            width=250
        )
        self.contract_combo.pack(side=tk.LEFT)

        # Чекбоксы для дополнительных данных в отчете
        options_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Переменные для чекбоксов
        self.include_works_count_var = tk.BooleanVar(value=True)
        self.include_products_count_var = tk.BooleanVar(value=True)
        self.include_contracts_count_var = tk.BooleanVar(value=True)

        # Чекбоксы
        include_works_count_cb = ctk.CTkCheckBox(
            options_frame,
            text="Включить количество работ",
            variable=self.include_works_count_var
        )
        include_works_count_cb.pack(side=tk.LEFT, padx=(0, 10))

        include_products_count_cb = ctk.CTkCheckBox(
            options_frame,
            text="Включить количество изделий",
            variable=self.include_products_count_var
        )
        include_products_count_cb.pack(side=tk.LEFT, padx=(0, 10))

        include_contracts_count_cb = ctk.CTkCheckBox(
            options_frame,
            text="Включить количество контрактов",
            variable=self.include_contracts_count_var
        )
        include_contracts_count_cb.pack(side=tk.LEFT)

        # Кнопки для генерации отчетов
        buttons_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        generate_excel_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в Excel",
            command=lambda: self.generate_report("excel"),
            fg_color=COLOR_SCHEME["success"],
            hover_color="#388E3C"
        )
        generate_excel_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_html_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в HTML",
            command=lambda: self.generate_report("html"),
            fg_color=COLOR_SCHEME["primary"],
            hover_color=COLOR_SCHEME["primary_dark"]
        )
        generate_html_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_pdf_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в PDF",
            command=lambda: self.generate_report("pdf"),
            fg_color=COLOR_SCHEME["primary"],
            hover_color=COLOR_SCHEME["primary_dark"]
        )
        generate_pdf_btn.pack(side=tk.LEFT)

        # Фрейм для предварительного просмотра отчета
        self.preview_frame = ctk.CTkFrame(self.parent, **FRAME_STYLE)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        # Заголовок "Предпросмотр отчета"
        preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Предпросмотр отчета",
            font=("Roboto", 14, "bold"),
            text_color=COLOR_SCHEME["text"]
        )
        preview_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Кнопка "Сформировать предпросмотр"
        preview_btn = ctk.CTkButton(
            self.preview_frame,
            text="Сформировать предпросмотр",
            command=self.preview_report,
            **BUTTON_STYLE
        )
        preview_btn.pack(anchor="w", padx=10, pady=(0, 10))

        # Фрейм для таблицы предпросмотра
        table_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Таблица для предпросмотра
        columns = (
            "worker", "date", "work_type", "quantity",
            "amount", "product", "contract"
        )

        self.preview_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Настраиваем заголовки столбцов
        self.preview_table.heading("worker", text="Работник")
        self.preview_table.heading("date", text="Дата")
        self.preview_table.heading("work_type", text="Вид работы")
        self.preview_table.heading("quantity", text="Количество")
        self.preview_table.heading("amount", text="Сумма, руб.")
        self.preview_table.heading("product", text="Изделие")
        self.preview_table.heading("contract", text="Контракт")

        # Настраиваем ширину столбцов
        self.preview_table.column("worker", width=150)
        self.preview_table.column("date", width=100, anchor="center")
        self.preview_table.column("work_type", width=200)
        self.preview_table.column("quantity", width=100, anchor="center")
        self.preview_table.column("amount", width=100, anchor="e")
        self.preview_table.column("product", width=150)
        self.preview_table.column("contract", width=100)

        # Добавляем прокрутку
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.preview_table.yview)
        self.preview_table.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.preview_table.xview)
        self.preview_table.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_table.pack(fill=tk.BOTH, expand=True)

        # Вызываем обработчик изменения периода для установки начальных дат
        self.on_period_changed(self.period_combo.get())

    def search_workers(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск работников для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Dict]: Список работников в формате для автокомплита
        """
        workers = self.worker_service.search_workers(search_text)

        # Преобразуем в формат для автокомплита
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

    def search_work_types(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск видов работ для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Dict]: Список видов работ в формате для автокомплита
        """
        work_types = self.work_type_service.search_work_types(search_text)

        # Преобразуем в формат для автокомплита
        result = [{"id": 0, "name": "Все виды работ"}]  # Опция "Все виды работ"

        for work_type in work_types:
            result.append({
                "id": work_type.id,
                "name": work_type.name
            })

        return result

    def search_products(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск изделий для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            List[Dict]: Список изделий в формате для автокомплита
        """
        products = self.product_service.search_products(search_text)

        # Преобразуем в формат для автокомплита
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
            List[Dict]: Список контрактов в формате для автокомплита
        """
        contracts = self.contract_service.search_contracts(search_text)

        # Преобразуем в формат для автокомплита
        result = [{"id": 0, "contract_number": "Все контракты"}]  # Опция "Все контракты"

        for contract in contracts:
            result.append({
                "id": contract.id,
                "contract_number": contract.contract_number
            })

        return result

    def set_default_period_dates(self) -> None:
        """Установка дат по умолчанию для текущего месяца"""
        today = datetime.now()
        first_day = date(today.year, today.month, 1)

        # Устанавливаем дату "от" - первый день текущего месяца
        self.from_day.set(str(first_day.day))
        self.from_month.set(str(first_day.month))
        self.from_year.set(str(first_day.year))

        # Устанавливаем дату "до" - текущий день
        self.to_day.set(str(today.day))
        self.to_month.set(str(today.month))
        self.to_year.set(str(today.year))

    def on_period_changed(self, selected_period: str) -> None:
        """
        Обработчик изменения периода отчета.

        Args:
            selected_period: Выбранный период
        """
        today = datetime.now()

        if selected_period == "Произвольный период":
            # Показываем фрейм с выбором дат
            self.dates_frame.pack(fill=tk.X, pady=(0, 10))
            return

        # Скрываем фрейм с выбором дат для предопределенных периодов
        self.dates_frame.pack_forget()

        # Устанавливаем даты в зависимости от выбранного периода
        if selected_period == "Текущий месяц":
            first_day = date(today.year, today.month, 1)
            last_day = date(
                today.year + (1 if today.month == 12 else 0),
                1 if today.month == 12 else today.month + 1,
                1
            ) - timedelta(days=1)

        elif selected_period == "Прошлый месяц":
            # Определяем прошлый месяц
            if today.month == 1:
                prev_month = 12
                prev_year = today.year - 1
            else:
                prev_month = today.month - 1
                prev_year = today.year

            first_day = date(prev_year, prev_month, 1)

            # Последний день прошлого месяца
            if prev_month == 12:
                last_day = date(prev_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(prev_year, prev_month + 1, 1) - timedelta(days=1)

        elif selected_period == "Текущий квартал":
            # Определяем текущий квартал
            current_quarter = (today.month - 1) // 3 + 1
            first_month = (current_quarter - 1) * 3 + 1

            first_day = date(today.year, first_month, 1)

            # Последний день квартала
            if current_quarter == 4:
                last_day = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(today.year, first_month + 3, 1) - timedelta(days=1)

        elif selected_period == "Прошлый квартал":
            # Определяем прошлый квартал
            current_quarter = (today.month - 1) // 3 + 1
            prev_quarter = current_quarter - 1 if current_quarter > 1 else 4

            year = today.year if prev_quarter < 4 else today.year - 1
            first_month = (prev_quarter - 1) * 3 + 1

            first_day = date(year, first_month, 1)

            # Последний день прошлого квартала
            if prev_quarter == 4:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, first_month + 3, 1) - timedelta(days=1)

        elif selected_period == "Текущий год":
            first_day = date(today.year, 1, 1)
            last_day = date(today.year, 12, 31)

        else:
            # По умолчанию - текущий месяц
            first_day = date(today.year, today.month, 1)
            last_day = date(
                today.year + (1 if today.month == 12 else 0),
                1 if today.month == 12 else today.month + 1,
                1
            ) - timedelta(days=1)

        # Устанавливаем даты в поля выбора
        self.from_day.set(str(first_day.day))
        self.from_month.set(str(first_day.month))
        self.from_year.set(str(first_day.year))

        self.to_day.set(str(last_day.day))
        self.to_month.set(str(last_day.month))
        self.to_year.set(str(last_day.year))

    def get_report_params(self) -> Tuple[Dict[str, Any], bool]:
        """
        Получение параметров для формирования отчета.
        Незаполненные поля фильтров игнорируются и не включаются в отчет.

        Returns:
            Tuple[Dict[str, Any], bool]: Параметры отчета и флаг валидности
        """
        params = {}

        # Получаем даты
        try:
            if self.period_combo.get() == "Произвольный период":
                from_date = date(
                    int(self.from_year.get()),
                    int(self.from_month.get()),
                    int(self.from_day.get())
                )
                to_date = date(
                    int(self.to_year.get()),
                    int(self.to_month.get()),
                    int(self.to_day.get())
                )

                # Проверяем корректность периода
                if from_date > to_date:
                    messagebox.showwarning("Внимание", "Дата начала не может быть позже даты окончания")
                    return {}, False

                params["start_date"] = from_date.strftime("%Y-%m-%d")
                params["end_date"] = to_date.strftime("%Y-%m-%d")
            else:
                # Для предопределенных периодов даты уже установлены правильно
                from_date = date(
                    int(self.from_year.get()),
                    int(self.from_month.get()),
                    int(self.from_day.get())
                )
                to_date = date(
                    int(self.to_year.get()),
                    int(self.to_month.get()),
                    int(self.to_day.get())
                )

                params["start_date"] = from_date.strftime("%Y-%m-%d")
                params["end_date"] = to_date.strftime("%Y-%m-%d")

        except ValueError:
            messagebox.showwarning("Внимание", "Некорректная дата")
            return {}, False

        # Получаем выбранного работника
        worker_item = self.worker_combo.get_selected_item()
        if worker_item and "id" in worker_item and worker_item["id"] != 0:
            # Добавляем параметр только если выбран конкретный работник (не "Все работники")
            params["worker_id"] = worker_item["id"]

        # Получаем выбранный вид работы
        work_type_item = self.work_type_combo.get_selected_item()
        if work_type_item and "id" in work_type_item and work_type_item["id"] != 0:
            # Добавляем параметр только если выбран конкретный вид работы (не "Все виды работ")
            params["work_type_id"] = work_type_item["id"]

        # Получаем выбранное изделие
        product_item = self.product_combo.get_selected_item()
        if product_item and "id" in product_item and product_item["id"] != 0:
            # Добавляем параметр только если выбрано конкретное изделие (не "Все изделия")
            params["product_id"] = product_item["id"]

        # Получаем выбранный контракт
        contract_item = self.contract_combo.get_selected_item()
        if contract_item and "id" in contract_item and contract_item["id"] != 0:
            # Добавляем параметр только если выбран конкретный контракт (не "Все контракты")
            params["contract_id"] = contract_item["id"]

        # Дополнительные параметры
        # Эти параметры добавляем только если они включены (True)
        if self.include_works_count_var.get():
            params["include_works_count"] = True

        if self.include_products_count_var.get():
            params["include_products_count"] = True

        if self.include_contracts_count_var.get():
            params["include_contracts_count"] = True

        return params, True

    def preview_report(self) -> None:
        """Предварительный просмотр отчета"""
        # Получаем параметры отчета
        params, valid = self.get_report_params()
        if not valid:
            return

        try:
            # Генерируем отчет
            df, summary_data = self.report_service.generate_report(params)  # Передаем params как словарь

            if df.empty:
                messagebox.showinfo("Информация", "Нет данных для отображения по заданным критериям")
                return

            # Очищаем таблицу
            for item in self.preview_table.get_children():
                self.preview_table.delete(item)

            # Печатаем информацию о структуре DataFrame (для отладки)
            print(f"Columns in DataFrame: {df.columns.tolist()}")
            if not df.empty:
                print(f"First row sample: {df.iloc[0].to_dict()}")

            # Заполняем таблицу данными
            for _, row in df.iterrows():
                # Безопасно извлекаем и форматируем данные
                worker = self._safe_get_value(row, "Работник", "")

                # Обработка даты
                date_value = self._safe_get_value(row, "Дата", "")
                formatted_date = self._format_date(date_value)

                work_type = self._safe_get_value(row, "Вид работы", "")
                quantity = self._safe_get_value(row, "Количество", "")

                # Обработка суммы
                amount = self._safe_get_value(row, "Сумма", 0)
                formatted_amount = f"{float(amount):.2f}" if amount is not None else ""

                product = self._safe_get_value(row, "Изделие", "")
                contract = self._safe_get_value(row, "Номер контракта", "")

                # Вставляем обработанные данные в таблицу
                self.preview_table.insert(
                    "", "end",
                    values=(
                        worker,
                        formatted_date,
                        work_type,
                        quantity,
                        formatted_amount,
                        product,
                        contract
                    )
                )

        except Exception as e:
            # Логируем подробную информацию об ошибке
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in preview_report(): {error_details}")

            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")

    def _safe_get_value(self, row, column, default_value):
        """Безопасно извлекает значение из строки DataFrame"""
        try:
            if column in row:
                return row[column] if row[column] is not None else default_value
            return default_value
        except Exception:
            return default_value

    def _format_date(self, date_value):
        """Форматирует значение даты в строку"""
        try:
            from datetime import date, datetime

            if isinstance(date_value, (date, datetime)):
                return date_value.strftime("%d.%m.%Y")
            elif isinstance(date_value, str):
                # Можно добавить дополнительную обработку строковой даты, если нужно
                return date_value
            else:
                return str(date_value) if date_value is not None else ""
        except Exception:
            return str(date_value) if date_value is not None else ""

    def generate_report(self, format_type: str) -> None:
        """
        Генерация отчета в указанном формате.

        Args:
            format_type: Тип формата ("excel", "html", "pdf")
        """
        # Получаем параметры отчета
        params, valid = self.get_report_params()
        if not valid:
            return

        try:
            # Генерируем отчет
            df, summary_data = self.report_service.generate_report(params)  # Передаем params как словарь

            if df.empty:
                messagebox.showinfo("Информация", "Нет данных для отображения по заданным критериям")
                return

            # Выбираем путь для сохранения файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"report_{timestamp}"

            filetypes = []
            if format_type == "excel":
                filetypes = [("Excel files", "*.xlsx")]
                default_filename += ".xlsx"
            elif format_type == "html":
                filetypes = [("HTML files", "*.html")]
                default_filename += ".html"
            elif format_type == "pdf":
                filetypes = [("PDF files", "*.pdf")]
                default_filename += ".pdf"

            # Выводим информацию о диалоге сохранения файла
            print(f"Opening save dialog for {format_type} report with default filename: {default_filename}")

            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=filetypes,
                initialfile=default_filename
            )

            print(f"Selected filename: {filename}")

            if not filename:
                print("User cancelled the save dialog")
                return  # Пользователь отменил сохранение

            # Проверяем доступность директории для записи
            save_dir = os.path.dirname(filename)
            if save_dir and not os.access(save_dir, os.W_OK):
                messagebox.showerror("Ошибка", f"Нет прав для записи в директорию {save_dir}")
                print(f"No write permission for directory: {save_dir}")
                return

            # Экспортируем отчет в выбранный формат
            filepath = ""
            try:
                if format_type == "excel":
                    print("Exporting to Excel...")
                    filepath = self.export_to_excel(df, summary_data, filename)
                elif format_type == "html":
                    print("Exporting to HTML...")
                    filepath = self.export_to_html(df, summary_data, filename)
                elif format_type == "pdf":
                    print("Exporting to PDF...")
                    filepath = self.export_to_pdf(df, summary_data, filename)

                print(f"Export result filepath: {filepath}")
            except Exception as export_error:
                print(f"Export error: {str(export_error)}")
                import traceback
                print(f"Export error details: {traceback.format_exc()}")
                messagebox.showerror("Ошибка экспорта", f"Ошибка при экспорте в {format_type}: {str(export_error)}")
                return

            if filepath and os.path.exists(filepath):
                print(f"Export successful, file created: {filepath}")
                # Спрашиваем, хочет ли пользователь открыть файл
                if messagebox.askyesno("Успех", f"Отчет успешно сохранен в файл {filepath}. Открыть файл?"):
                    # Открываем файл в соответствующей программе
                    try:
                        webbrowser.open(filepath)
                        print(f"Opening file with default application: {filepath}")
                    except Exception as open_error:
                        print(f"Error opening file: {str(open_error)}")
                        messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(open_error)}")
            else:
                error_msg = f"Файл не был создан или не существует: {filepath}"
                print(error_msg)
                messagebox.showerror("Ошибка", error_msg)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Generate report error: {error_details}")
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")

    # Методы экспорта, которые нужно реализовать в классе, если они ещё не реализованы:

    def export_to_excel(self, df, summary_data, filename):
        """
        Экспорт отчета в формат Excel.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с итоговыми данными
            filename: Путь для сохранения файла

        Returns:
            str: Путь к созданному файлу или пустая строка в случае ошибки
        """
        try:
            # Создаем Excel-писателя
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Записываем данные на лист "Данные"
                df.to_excel(writer, sheet_name='Данные', index=False)

                # Создаем лист для итоговых данных, если есть итоговые данные
                if summary_data:
                    summary_df = pd.DataFrame({
                        "Показатель": list(summary_data.keys()),
                        "Значение": list(summary_data.values())
                    })
                    summary_df.to_excel(writer, sheet_name='Итоги', index=False)

            print(f"Excel file successfully created: {filename}")
            return filename
        except Exception as e:
            print(f"Error in export_to_excel: {str(e)}")
            traceback.print_exc()  # Более простой способ печати трассировки
            return ""

    def export_to_html(self, df, summary_data, filename):
        """
        Экспорт отчета в формат HTML.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с итоговыми данными
            filename: Путь для сохранения файла

        Returns:
            str: Путь к созданному файлу или пустая строка в случае ошибки
        """
        try:
            # Создаем HTML-шаблон, используя двойные фигурные скобки {{ }} для CSS
            # и одинарные { } для подстановки переменных
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Отчет по сдельной работе</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .summary {{ margin-top: 30px; }}
                    h1, h2 {{ color: #333; }}
                </style>
            </head>
            <body>
                <h1>Отчет по сдельной работе</h1>
                <div class="data-table">
                    <h2>Данные</h2>
                    {table}
                </div>
                <div class="summary">
                    <h2>Итоги</h2>
                    <table>
                        <tr><th>Показатель</th><th>Значение</th></tr>
                        {summary_rows}
                    </table>
                </div>
            </body>
            </html>
            """

            # Форматируем данные в HTML-таблицу
            table_html = df.to_html(index=False)

            # Форматируем итоговые данные
            summary_rows = ""
            for key, value in summary_data.items():
                summary_rows += f"<tr><td>{key}</td><td>{value}</td></tr>"

            # Заполняем HTML-шаблон данными
            html_content = html_content.format(table=table_html, summary_rows=summary_rows)

            # Записываем HTML в файл
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"HTML file successfully created: {filename}")
            return filename
        except Exception as e:
            print(f"Error in export_to_html: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""

    def export_to_pdf(self, df, summary_data, filename):
        """
        Экспорт отчета в формат PDF с использованием ReportLab.
        Оптимизированная версия с альбомной ориентацией и автоматическим переносом строк.

        Args:
            df: DataFrame с данными отчета
            summary_data: Данные итогов - может быть списком или словарем
            filename: Путь для сохранения файла

        Returns:
            str: Путь к созданному файлу или пустая строка в случае ошибки
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            import os

            # Список возможных шрифтов с поддержкой кириллицы в порядке предпочтения
            cyrillic_fonts = [
                {'name': 'DejaVuSans', 'file': 'DejaVuSans.ttf'},
                {'name': 'Arial', 'file': 'Arial.ttf'},
                {'name': 'Verdana', 'file': 'Verdana.ttf'},
                {'name': 'Tahoma', 'file': 'Tahoma.ttf'}
            ]

            # Путь к папке со шрифтами в вашем приложении
            fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
            if not os.path.exists(fonts_dir):
                os.makedirs(fonts_dir)
                print(f"Created fonts directory: {fonts_dir}")

            # Windows системные шрифты
            windows_fonts_dir = r'C:\Windows\Fonts'

            # Пытаемся найти и зарегистрировать подходящий шрифт
            font_registered = False
            default_font = 'Helvetica'  # Стандартный шрифт в случае неудачи

            for font in cyrillic_fonts:
                # Проверяем в папке приложения
                app_font_path = os.path.join(fonts_dir, font['file'])
                if os.path.exists(app_font_path):
                    pdfmetrics.registerFont(TTFont(font['name'], app_font_path))
                    default_font = font['name']
                    font_registered = True
                    print(f"Using font from app directory: {font['name']}")
                    break

                # Проверяем в системных шрифтах Windows
                if os.path.exists(windows_fonts_dir):
                    sys_font_path = os.path.join(windows_fonts_dir, font['file'])
                    if os.path.exists(sys_font_path):
                        pdfmetrics.registerFont(TTFont(font['name'], sys_font_path))
                        default_font = font['name']
                        font_registered = True
                        print(f"Using system font: {font['name']}")
                        break

            if not font_registered:
                print(
                    "Warning: No suitable font with Cyrillic support found. Using Helvetica. Cyrillic characters may not display correctly.")

            # Создаем стили текста
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='TitleStyle',
                fontName=default_font,
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=20
            ))
            styles.add(ParagraphStyle(
                name='SubtitleStyle',
                fontName=default_font,
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=10
            ))

            # Создаем стиль для ячеек таблицы с переносом слов
            cell_style = ParagraphStyle(
                name='CellStyle',
                fontName=default_font,
                fontSize=8,  # Уменьшаем размер шрифта
                alignment=TA_LEFT,
                wordWrap='CJK'  # Включаем перенос слов
            )

            # Создаем PDF документ в альбомной ориентации с уменьшенными отступами
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(A4),
                leftMargin=20,
                rightMargin=20,
                topMargin=20,
                bottomMargin=20
            )

            # Подготавливаем элементы документа
            elements = []

            # Добавляем заголовок отчета
            title = Paragraph('Отчет по сдельной работе', styles['TitleStyle'])
            elements.append(title)
            elements.append(Spacer(1, 10))

            # Добавляем подзаголовок для данных
            subtitle = Paragraph('Данные', styles['SubtitleStyle'])
            elements.append(subtitle)

            # Получаем ширину доступной области страницы
            page_width, page_height = landscape(A4)
            available_width = page_width - 40  # 20 пунктов с каждой стороны

            # Функция для умного определения ширины колонок на основе содержимого
            def get_smart_col_widths(df, available_width, min_width=30):
                # Получаем длину самого длинного значения в каждой колонке
                col_lengths = {}
                for col in df.columns:
                    # Определяем максимальную длину значения (заголовка или данных)
                    col_str_len = max(len(str(col)), df[col].astype(str).str.len().max())
                    # Устанавливаем ширину пропорционально длине (6 - примерная ширина символа)
                    col_lengths[col] = max(col_str_len * 6, min_width)

                # Определяем сумму всех ширин
                total_width = sum(col_lengths.values())

                # Если сумма всех ширин больше доступной ширины, уменьшаем пропорционально
                if total_width > available_width:
                    scale_factor = available_width / total_width
                    for col in col_lengths:
                        col_lengths[col] = col_lengths[col] * scale_factor

                return [col_lengths[col] for col in df.columns]

            # Получаем умные ширины колонок
            col_widths = get_smart_col_widths(df, available_width)

            # Преобразуем DataFrame в список с Paragraph для поддержки переноса слов
            header = [Paragraph(str(col), cell_style) for col in df.columns]
            data = [header]

            for _, row in df.iterrows():
                row_list = [Paragraph(str(val), cell_style) for val in row.values]
                data.append(row_list)

            # Создаем таблицу данных с расчитанными ширинами колонок
            data_table = Table(data, colWidths=col_widths,
                               repeatRows=1)  # repeatRows=1 повторяет заголовок на каждой странице

            # Стилизуем таблицу данных
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), default_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            data_table.setStyle(table_style)
            elements.append(data_table)
            elements.append(Spacer(1, 20))

            # Добавляем подзаголовок для итогов
            summary_title = Paragraph('Итоги', styles['SubtitleStyle'])
            elements.append(summary_title)

            # Создаем таблицу итогов
            summary_table_data = [['Показатель', 'Значение']]

            # Проверяем тип summary_data и обрабатываем соответствующим образом
            if isinstance(summary_data, dict):
                # Если summary_data - словарь
                for key, value in summary_data.items():
                    summary_table_data.append([str(key), str(value)])
            elif isinstance(summary_data, list):
                # Если summary_data - список
                if len(summary_data) > 0 and all(
                        isinstance(item, (list, tuple)) and len(item) >= 2 for item in summary_data):
                    # Если это список пар [ключ, значение]
                    for item in summary_data:
                        summary_table_data.append([str(item[0]), str(item[1])])
                else:
                    # Если это просто список значений
                    for i, item in enumerate(summary_data):
                        summary_table_data.append([f"Элемент {i + 1}", str(item)])
            else:
                # Если summary_data другого типа, просто отображаем его как строку
                summary_table_data.append(["Итог", str(summary_data)])

            # Преобразуем в Paragraph для поддержки переноса слов
            summary_data_with_paragraphs = []
            for row in summary_table_data:
                summary_data_with_paragraphs.append([Paragraph(str(cell), cell_style) for cell in row])

            # Создаем таблицу итогов
            summary_col_widths = [available_width * 0.7, available_width * 0.3]  # 70% и 30% от доступной ширины
            summary_table = Table(summary_data_with_paragraphs, colWidths=summary_col_widths)

            # Стилизуем таблицу итогов
            summary_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), default_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # Немного увеличиваем шрифт для итогов
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            summary_table.setStyle(summary_style)
            elements.append(summary_table)

            # Строим PDF документ
            doc.build(elements)

            print(f"PDF file successfully created: {filename}")
            return filename
        except Exception as e:
            print(f"Error in export_to_pdf: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""