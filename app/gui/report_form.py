"""
Форма для создания отчетов.
Позволяет выбирать период, работников и другие параметры для формирования отчетов.
"""
import os
import tkinter as tk
from datetime import datetime, date, timedelta
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Tuple

import customtkinter as ctk
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.config import REPORT_SETTINGS, UI_SETTINGS, DATE_FORMATS
from app.db.db_manager import DatabaseManager
from app.gui.autocomplete import AutocompleteCombobox
from app.services.report_service import ReportService
from app.db.models import Worker, WorkType, Product, Contract

logger = logging.getLogger(__name__)

class ReportForm:
    """
    Форма для создания отчетов по работе сотрудников.
    """

    def __init__(self, parent: ctk.CTkFrame, report_service: ReportService):
        """
        Инициализация формы отчетов.

        Args:
            parent: Родительский виджет
            report_service: Сервис для работы с отчетами
        """
        self.parent = parent
        self.report_service = report_service

        # Создаем интерфейс
        self.setup_ui()

    def setup_ui(self) -> None:
        """Создание интерфейса формы"""
        # Фрейм с фильтрами отчета
        self.filters_frame = ctk.CTkFrame(self.parent, **UI_SETTINGS['card_frame'])
        self.filters_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Заголовок "Параметры отчета"
        filters_label = ctk.CTkLabel(
            self.filters_frame,
            text="Параметры отчета",
            font=UI_SETTINGS['header_font'],
            text_color=UI_SETTINGS['text_color']
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

        ctk.CTkLabel(period_frame, text="Период:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

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

        ctk.CTkLabel(from_date_frame, text="От:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Выпадающие списки для даты "от"
        self.from_day = ctk.CTkComboBox(from_date_frame, width=60, values=[str(i) for i in range(1, 32)])
        self.from_day.pack(side=tk.LEFT, padx=(0, 5))

        self.from_month = ctk.CTkComboBox(from_date_frame, width=60, values=[str(i) for i in range(1, 13)])
        self.from_month.pack(side=tk.LEFT, padx=(0, 5))

        self.from_year = ctk.CTkComboBox(from_date_frame, width=80, values=[str(i) for i in range(2000, 2051)])
        self.from_year.pack(side=tk.LEFT)

        # До даты
        to_date_frame = ctk.CTkFrame(self.dates_frame, fg_color="transparent")
        to_date_frame.pack(fill=tk.X)

        ctk.CTkLabel(to_date_frame, text="До:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Выпадающие списки для даты "до"
        self.to_day = ctk.CTkComboBox(to_date_frame, width=60, values=[str(i) for i in range(1, 32)])
        self.to_day.pack(side=tk.LEFT, padx=(0, 5))

        self.to_month = ctk.CTkComboBox(to_date_frame, width=60, values=[str(i) for i in range(1, 13)])
        self.to_month.pack(side=tk.LEFT, padx=(0, 5))

        self.to_year = ctk.CTkComboBox(to_date_frame, width=80, values=[str(i) for i in range(2000, 2051)])
        self.to_year.pack(side=tk.LEFT)

        # Устанавливаем текущие даты периода
        self.set_default_period_dates()

        # Работник
        worker_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        worker_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(worker_frame, text="Работник:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для работников
        self.worker_combo = AutocompleteCombobox(
            worker_frame,
            search_function=self.search_workers,
            display_key="full_name",
            width=300
        )
        self.worker_combo.pack(side=tk.LEFT)

        # Вторая колонка фильтров
        right_column = ctk.CTkFrame(form_frame, fg_color="transparent")
        right_column.pack(side=tk.LEFT, fill=tk.Y)

        # Вид работы
        work_type_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        work_type_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(work_type_frame, text="Вид работы:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для видов работ
        self.work_type_combo = AutocompleteCombobox(
            work_type_frame,
            search_function=self.search_work_types,
            display_key="name",
            width=300
        )
        self.work_type_combo.pack(side=tk.LEFT)

        # Изделие
        product_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        product_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(product_frame, text="Изделие:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для изделий
        self.product_combo = AutocompleteCombobox(
            product_frame,
            search_function=self.search_products,
            display_key="full_name",
            width=300
        )
        self.product_combo.pack(side=tk.LEFT)

        # Контракт
        contract_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        contract_frame.pack(fill=tk.X)

        ctk.CTkLabel(contract_frame, text="Контракт:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        # Автозаполняемый выпадающий список для контрактов
        self.contract_combo = AutocompleteCombobox(
            contract_frame,
            search_function=self.search_contracts,
            display_key="contract_number",
            width=300
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
            **UI_SETTINGS['button_style']
        )
        generate_excel_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_html_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в HTML",
            command=lambda: self.generate_report("html"),
            **UI_SETTINGS['button_style']
        )
        generate_html_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_pdf_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в PDF",
            command=lambda: self.generate_report("pdf"),
            **UI_SETTINGS['button_style']
        )
        generate_pdf_btn.pack(side=tk.LEFT)

        # Фрейм для предварительного просмотра отчета
        preview_frame = ctk.CTkFrame(self.parent, **UI_SETTINGS['card_frame'])
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        # Кнопка "Сформировать предпросмотр"
        preview_btn = ctk.CTkButton(
            preview_frame,
            text="Сформировать предпросмотр",
            command=self.preview_report,
            **UI_SETTINGS['button_style']
        )
        preview_btn.pack(anchor="w", padx=10, pady=(10, 5))

        # Фрейм для таблицы предпросмотра
        table_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
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

    def search_workers(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Поиск работников для автокомплита.

        Args:
            search_text: Текст для поиска

        Returns:
            Список работников в формате для автокомплита
        """
        workers = self.report_service.db.worker_service.search_workers(search_text)

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
            Список видов работ в формате для автокомплита
        """
        work_types = self.report_service.db.work_type_service.search_work_types(search_text)

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
            Список изделий в формате для автокомплита
        """
        products = self.report_service.db.product_service.search_products(search_text)

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
        contracts = self.report_service.db.contract_service.search_contracts(search_text)

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
            last_day = date(today.year, today.month, today.day)

        elif selected_period == "Прошлый месяц":
            if today.month == 1:
                prev_month = 12
                prev_year = today.year - 1
            else:
                prev_month = today.month - 1
                prev_year = today.year

            first_day = date(prev_year, prev_month, 1)
            last_day = date(prev_year, prev_month, 28)  # Базовое значение, будет скорректировано

            # Находим последний день предыдущего месяца
            while True:
                try:
                    last_day = date(prev_year, prev_month, last_day.day + 1)
                except ValueError:
                    break

        elif selected_period == "Текущий квартал":
            current_quarter = (today.month - 1) // 3 + 1
            first_month = (current_quarter - 1) * 3 + 1
            first_day = date(today.year, first_month, 1)

            if current_quarter == 4:
                last_day = date(today.year, 12, 31)
            else:
                last_day = date(today.year, first_month + 2, 28)  # Базовое значение

                # Находим последний день квартала
                while True:
                    try:
                        last_day = date(today.year, first_month + 2, last_day.day + 1)
                    except ValueError:
                        break

        elif selected_period == "Прошлый квартал":
            current_quarter = (today.month - 1) // 3 + 1
            prev_quarter = current_quarter - 1 if current_quarter > 1 else 4

            if prev_quarter == 4:
                prev_year = today.year - 1
                first_month = 10
            else:
                prev_year = today.year
                first_month = (prev_quarter - 1) * 3 + 1

            first_day = date(prev_year, first_month, 1)

            if prev_quarter == 4:
                last_day = date(prev_year, 12, 31)
            else:
                last_day = date(prev_year, first_month + 2, 28)  # Базовое значение

                # Находим последний день квартала
                while True:
                    try:
                        last_day = date(prev_year, first_month + 2, last_day.day + 1)
                    except ValueError:
                        break

        elif selected_period == "Текущий год":
            first_day = date(today.year, 1, 1)
            last_day = date(today.year, 12, 31)

        else:
            # По умолчанию - текущий месяц
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month, today.day)

        # Устанавливаем даты в соответствующие поля
        self.from_day.set(str(first_day.day))
        self.from_month.set(str(first_day.month))
        self.from_year.set(str(first_day.year))

        self.to_day.set(str(last_day.day))
        self.to_month.set(str(last_day.month))
        self.to_year.set(str(last_day.year))

    def preview_report(self) -> None:
        """Предварительный просмотр отчета"""
        # Получаем параметры отчета
        params = self.get_report_params()

        if not params:
            return

        try:
            # Генерируем отчет
            df, summary_data = self.report_service.generate_report(params)

            if df.empty:
                messagebox.showinfo("Информация", "Нет данных для отображения по заданным критериям")
                return

            # Очищаем таблицу предпросмотра
            for item in self.preview_table.get_children():
                self.preview_table.delete(item)

            # Заполняем таблицу данными
            for _, row in df.iterrows():
                self.preview_table.insert(
                    "", "end",
                    values=(
                        row['worker'],
                        row['date'],
                        row['work_type'],
                        row['quantity'],
                        f"{row['amount']:.2f}",
                        row['product'],
                        row['contract']
                    )
                )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")

    def get_report_params(self) -> Optional[Dict[str, Any]]:
        """
        Получение параметров для генерации отчета.

        Returns:
            Словарь с параметрами отчета или None в случае ошибки
        """
        params = {}

        try:
            # Даты
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

                if from_date > to_date:
                    messagebox.showwarning("Внимание", "Дата начала не может быть позже даты окончания")
                    return None

                params['start_date'] = from_date.strftime(DATE_FORMATS['default'])
                params['end_date'] = to_date.strftime(DATE_FORMATS['default'])
            else:
                # Для предопределенных периодов даты уже установлены
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

                params['start_date'] = from_date.strftime(DATE_FORMATS['default'])
                params['end_date'] = to_date.strftime(DATE_FORMATS['default'])

            # Работник
            worker_item = self.worker_combo.get_selected_item()
            if worker_item and worker_item.get('id', 0) != 0:
                params['worker_id'] = worker_item['id']

            # Вид работы
            work_type_item = self.work_type_combo.get_selected_item()
            if work_type_item and work_type_item.get('id', 0) != 0:
                params['work_type_id'] = work_type_item['id']

            # Изделие
            product_item = self.product_combo.get_selected_item()
            if product_item and product_item.get('id', 0) != 0:
                params['product_id'] = product_item['id']

            # Контракт
            contract_item = self.contract_combo.get_selected_item()
            if contract_item and contract_item.get('id', 0) != 0:
                params['contract_id'] = contract_item['id']

            # Дополнительные параметры
            params['include_works_count'] = self.include_works_count_var.get()
            params['include_products_count'] = self.include_products_count_var.get()
            params['include_contracts_count'] = self.include_contracts_count_var.get()

            return params

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить параметры отчета: {str(e)}")
            return None

    def generate_report(self, format_type: str) -> None:
        """
        Генерация отчета в указанном формате.

        Args:
            format_type: Тип формата ("excel", "html", "pdf")
        """
        params = self.get_report_params()
        if not params:
            return

        try:
            # Генерируем данные отчета
            df, summary_data = self.report_service.generate_report(params)

            if df.empty:
                messagebox.showinfo("Информация", "Нет данных для экспорта")
                return

            # Формируем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}"

            if format_type == "excel":
                self.export_to_excel(df, summary_data, filename)
            elif format_type == "html":
                self.export_to_html(df, summary_data, filename)
            elif format_type == "pdf":
                self.export_to_pdf(df, summary_data, filename)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {str(e)}")

    def export_to_excel(self, df: pd.DataFrame, summary_data: Dict[str, Any], filename: str) -> None:
        """
        Экспорт отчета в формат Excel.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с итоговыми данными
            filename: Имя файла без расширения
        """
        try:
            # Полный путь к файлу
            filepath = os.path.join(REPORT_SETTINGS['output_dir'], f"{filename}.xlsx")

            # Создаем объект writer для записи в Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Основные данные
                df.to_excel(writer, sheet_name='Данные', index=False)

                # Дополнительные данные, если запрошены
                if summary_data.get('works_count', 0) > 0:
                    summary_df = pd.DataFrame(summary_data['works_count'])
                    summary_df.to_excel(writer, sheet_name='Виды работ', index=False)

                if summary_data.get('products_count', 0) > 0:
                    summary_df = pd.DataFrame(summary_data['products_count'])
                    summary_df.to_excel(writer, sheet_name='Изделия', index=False)

                if summary_data.get('contracts_count', 0) > 0:
                    summary_df = pd.DataFrame(summary_data['contracts_count'])
                    summary_df.to_excel(writer, sheet_name='Контракты', index=False)

            messagebox.showinfo("Успех", f"Отчет успешно экспортирован в Excel:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать в Excel:\n{str(e)}")

    def export_to_html(self, df: pd.DataFrame, summary_data: Dict[str, Any], filename: str) -> None:
        """
        Экспорт отчета в формат HTML.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с итоговыми данными
            filename: Имя файла без расширения
        """
        try:
            # Полный путь к файлу
            filepath = os.path.join(REPORT_SETTINGS['output_dir'], f"{filename}.html")

            # Формируем HTML-содержимое
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Отчет по работе сотрудников</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2 { color: #444; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>Отчет по работе сотрудников</h1>
                <p>Дата формирования: {date}</p>

                <h2>Основные данные</h2>
                {main_table}
            """.format(
                date=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                main_table=df.to_html(index=False)
            )

            # Добавляем дополнительные таблицы, если есть
            if summary_data.get('works_count', 0) > 0:
                html_content += """
                <h2>Количество выполненных работ</h2>
                {table}
                """.format(table=pd.DataFrame(summary_data['works_count']).to_html(index=False))

            if summary_data.get('products_count', 0) > 0:
                html_content += """
                <h2>Количество изделий</h2>
                {table}
                """.format(table=pd.DataFrame(summary_data['products_count']).to_html(index=False))

            if summary_data.get('contracts_count', 0) > 0:
                html_content += """
                <h2>Количество контрактов</h2>
                {table}
                """.format(table=pd.DataFrame(summary_data['contracts_count']).to_html(index=False))

            # Закрываем HTML-документ
            html_content += """
            </body>
            </html>
            """

            # Записываем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            messagebox.showinfo("Успех", f"Отчет успешно экспортирован в HTML:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать в HTML:\n{str(e)}")

    def export_to_pdf(self, df: pd.DataFrame, summary_data: Dict[str, Any], filename: str) -> None:
        """
        Экспорт отчета в формат PDF.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с итоговыми данными
            filename: Имя файла без расширения
        """
        try:
            # Полный путь к файлу
            filepath = os.path.join(REPORT_SETTINGS['output_dir'], f"{filename}.pdf")

            # Создаем PDF-документ
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
            elements = []

            # Стили для текста
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='TableHeader', fontSize=10, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='TableData', fontSize=9))

            # Заголовок
            elements.append(Paragraph("Отчет по работе сотрудников", styles['Title']))
            elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Основная таблица
            data = [['Работник', 'Дата', 'Вид работы', 'Количество', 'Сумма, руб.', 'Изделие', 'Контракт']]
            for _, row in df.iterrows():
                data.append([
                    Paragraph(str(row['worker']), styles['TableData']),
                    Paragraph(str(row['date']), styles['TableData']),
                    Paragraph(str(row['work_type']), styles['TableData']),
                    Paragraph(str(row['quantity']), styles['TableData']),
                    Paragraph(f"{float(row['amount']):.2f}", styles['TableData']),
                    Paragraph(str(row['product']), styles['TableData']),
                    Paragraph(str(row['contract']), styles['TableData'])
                ])

            # Создаем таблицу
            table = Table(data, colWidths=[100, 80, 150, 80, 80, 100, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

            # Дополнительные данные
            if summary_data.get('works_count', 0) > 0:
                elements.append(Paragraph("Количество выполненных работ", styles['Heading2']))
                # Формируем таблицу с данными о работах
                works_data = [['Вид работы', 'Количество']]
                for work_type, count in summary_data['works_count'].items():
                    works_data.append([Paragraph(str(work_type), styles['TableData']), Paragraph(str(count), styles['TableData'])])
                works_table = Table(works_data, colWidths=[200, 100])
                works_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(works_table)
                elements.append(Spacer(1, 20))

            if summary_data.get('products_count', 0) > 0:
                elements.append(Paragraph("Количество изделий", styles['Heading2']))
                # Формируем таблицу с данными о изделиях
                products_data = [['Изделие', 'Количество']]
                for product, count in summary_data['products_count'].items():
                    products_data.append([Paragraph(str(product), styles['TableData']), Paragraph(str(count), styles['TableData'])])
                products_table = Table(products_data, colWidths=[200, 100])
                products_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(products_table)
                elements.append(Spacer(1, 20))

            if summary_data.get('contracts_count', 0) > 0:
                elements.append(Paragraph("Количество контрактов", styles['Heading2']))
                # Формируем таблицу с данными о контрактах
                contracts_data = [['Контракт', 'Количество']]
                for contract, count in summary_data['contracts_count'].items():
                    contracts_data.append([Paragraph(str(contract), styles['TableData']), Paragraph(str(count), styles['TableData'])])
                contracts_table = Table(contracts_data, colWidths=[200, 100])
                contracts_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(contracts_table)
                elements.append(Spacer(1, 20))

            # Строим PDF-документ
            doc.build(elements)

            messagebox.showinfo("Успех", f"Отчет успешно экспортирован в PDF:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать в PDF:\n{str(e)}")