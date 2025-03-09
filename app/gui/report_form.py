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
        if worker_item and "id" in worker_item:
            params["worker_id"] = worker_item["id"]
        else:
            params["worker_id"] = 0  # Все работники

        # Получаем выбранный вид работы
        work_type_item = self.work_type_combo.get_selected_item()
        if work_type_item and "id" in work_type_item:
            params["work_type_id"] = work_type_item["id"]
        else:
            params["work_type_id"] = 0  # Все виды работ

        # Получаем выбранное изделие
        product_item = self.product_combo.get_selected_item()
        if product_item and "id" in product_item:
            params["product_id"] = product_item["id"]
        else:
            params["product_id"] = 0  # Все изделия

        # Получаем выбранный контракт
        contract_item = self.contract_combo.get_selected_item()
        if contract_item and "id" in contract_item:
            params["contract_id"] = contract_item["id"]
        else:
            params["contract_id"] = 0  # Все контракты

        # Дополнительные параметры
        params["include_works_count"] = self.include_works_count_var.get()
        params["include_products_count"] = self.include_products_count_var.get()
        params["include_contracts_count"] = self.include_contracts_count_var.get()

        return params, True

    def preview_report(self) -> None:
        """Предварительный просмотр отчета"""
        # Получаем параметры отчета
        params, valid = self.get_report_params()
        if not valid:
            return

        try:
            # Генерируем отчет
            df, summary_data = self.report_service.generate_report(**params)

            if df.empty:
                messagebox.showinfo("Информация", "Нет данных для отображения по заданным критериям")
                return

            # Очищаем таблицу
            for item in self.preview_table.get_children():
                self.preview_table.delete(item)

            # Заполняем таблицу данными
            for _, row in df.iterrows():
                self.preview_table.insert(
                    "", "end",
                    values=(
                        row.get("Работник", ""),
                        row.get("Дата", "").strftime("%d.%m.%Y") if isinstance(row.get("Дата"), date) else row.get(
                            "Дата", ""),
                        row.get("Вид работы", ""),
                        row.get("Количество", ""),
                        f"{row.get('Сумма', 0):.2f}" if row.get("Сумма") is not None else "",
                        row.get("Изделие", ""),
                        row.get("Номер контракта", "")
                    )
                )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")

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
            df, summary_data = self.report_service.generate_report(**params)

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

            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=filetypes,
                initialfile=default_filename
            )

            if not filename:
                return  # Пользователь отменил сохранение

            # Экспортируем отчет в выбранный формат
            filepath = ""
            if format_type == "excel":
                filepath = self.report_service.export_to_excel(df, summary_data, filename)
            elif format_type == "html":
                filepath = self.report_service.export_to_html(df, summary_data, filename)
            elif format_type == "pdf":
                filepath = self.report_service.export_to_pdf(df, summary_data, filename)

            if filepath:
                # Спрашиваем, хочет ли пользователь открыть файл
                if messagebox.askyesno("Успех", f"Отчет успешно сохранен в файл {filepath}. Открыть файл?"):
                    # Открываем файл в соответствующей программе
                    if os.path.exists(filepath):
                        webbrowser.open(filepath)
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать отчет")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")
