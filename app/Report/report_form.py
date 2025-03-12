"""
Форма для создания отчетов.
Позволяет выбирать период, работников и другие параметры для формирования отчетов.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime, date

from typing import List, Dict, Any, Tuple, Optional

from app.Report.report_generator import ReportGenerator
from app.Report.report_exporter import ReportExporter
from app.Report.report_preview import ReportPreview
from app.Report.report_params import ReportParams
from app.config import REPORT_SETTINGS, UI_SETTINGS, DATE_FORMATS
from app.db_manager import DatabaseManager
from app.autocomplete import AutocompleteCombobox
from app.Report.report_service import ReportService
from app.models import Worker, WorkType, Product, Contract

logger = logging.getLogger(__name__)

class ReportForm:
    def __init__(self, parent: ctk.CTkFrame, report_service: ReportService):
        self.parent = parent
        self.report_service = report_service

        # Инициализация компонентов отчета
        self.generator = ReportGenerator(report_service)
        self.exporter = ReportExporter(REPORT_SETTINGS)
        self.preview_component = ReportPreview(parent)

        # Настройка интерфейса
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
            command=lambda: self.export_report("excel"),
            **UI_SETTINGS['button_style']
        )
        generate_excel_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_html_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в HTML",
            command=lambda: self.export_report("html"),
            **UI_SETTINGS['button_style']
        )
        generate_html_btn.pack(side=tk.LEFT, padx=(0, 10))

        generate_pdf_btn = ctk.CTkButton(
            buttons_frame,
            text="Экспорт в PDF",
            command=lambda: self.export_report("pdf"),
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

    def search_workers(self, search_text: str) -> List[Dict[str, Any]]:
        return self.report_service.worker_service.search_workers(search_text)

    def search_work_types(self, search_text: str) -> List[Dict[str, Any]]:
        return self.report_service.work_type_service.search_work_types(search_text)

    def search_products(self, search_text: str) -> List[Dict[str, Any]]:
        return self.report_service.product_service.search_products(search_text)

    def search_contracts(self, search_text: str) -> List[Dict[str, Any]]:
        return self.report_service.contract_service.search_contracts(search_text)

    def set_default_period_dates(self) -> None:
        today = datetime.now()
        first_day = date(today.year, today.month, 1)
        self.from_day.set(str(first_day.day))
        self.from_month.set(str(first_day.month))
        self.from_year.set(str(first_day.year))
        self.to_day.set(str(today.day))
        self.to_month.set(str(today.month))
        self.to_year.set(str(today.year))

    def on_period_changed(self, selected_period: str) -> None:
        today = datetime.now()
        if selected_period == "Произвольный период":
            self.dates_frame.pack(fill=tk.X, pady=(0, 10))
            return
        self.dates_frame.pack_forget()
        # Логика установки дат для предопределенных периодов

    def preview_report(self) -> None:
        params = ReportParams.get_params(self)
        if not params:
            return
        df = self.generator.generate(params)
        if df is not None:
            self.preview_component.preview(df)

    def export_report(self, format_type: str) -> None:
        params = ReportParams.get_params(self)
        if not params:
            return
        df = self.generator.generate(params)
        if df is not None:
            self.exporter.export(df, format_type)

    def get_report_params(self) -> Optional[Dict[str, Any]]:
        # Логика получения параметров отчета
        pass
