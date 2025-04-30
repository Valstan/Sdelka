"""
File: app/ui/report_form.py
Форма для генерации отчетов.
"""
import logging
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Callable

from app.core.forms.base_form import BaseForm
from app.core.models.worker import Worker
from app.core.models.product import Product
from app.core.models.contract import Contract
from app.core.models.work_type import WorkType
from app.core.services.report_service import ReportService
from app.core.services.worker_service import WorkerService
from app.core.services.product_service import ProductService
from app.core.services.work_type_service import WorkTypeService
from app.core.services.contract_service import ContractService
from app.core.services.work_card_service import WorkCardService
from app.ui.components.autocomplete_combobox import AutocompleteCombobox
from app.config import UI_SETTINGS
from app.report.report_exporter import ReportExporter

logger = logging.getLogger(__name__)


class ReportForm(BaseForm):
    """
    Форма для генерации отчетов по нарядам.
    Позволяет фильтровать данные по различным критериям и экспортировать результаты.
    """

    def __init__(
        self,
        parent: tk.Widget,
        report_service: ReportService,
        card_service: WorkCardService,
        worker_service: WorkerService,
        product_service: ProductService,
        work_type_service: WorkTypeService,
        contract_service: ContractService,
        on_generate: Optional[Callable] = None
    ):
        """
        Инициализация формы отчета.

        Args:
            parent: Родительский виджет
            report_service: Сервис генерации отчетов
            card_service: Сервис работы с нарядами
            worker_service: Сервис работы с работниками
            product_service: Сервис работы с изделиями
            work_type_service: Сервис работы с видами работ
            contract_service: Сервис работы с контрактами
            on_generate: Callback-функция после генерации отчета
        """
        super().__init__(parent)
        self.report_service = report_service
        self.card_service = card_service
        self.worker_service = worker_service
        self.product_service = product_service
        self.work_type_service = work_type_service
        self.contract_service = contract_service
        self.on_generate = on_generate
        self.report_exporter = ReportExporter()
        self.include_works_count = False
        self.include_products_count = False
        self.include_contracts_count = False
        self.entry_fields = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка интерфейса формы."""
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 1. Период
        period_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        period_frame.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(period_frame, text="Период:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["period"] = ctk.CTkComboBox(
            period_frame,
            values=["Текущий месяц", "Текущий год", "Произвольный период"],
            command=self._on_period_changed
        )
        self.entry_fields["period"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. Произвольный период (скрыт по умолчанию)
        self.custom_period_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.custom_period_frame.pack(fill=tk.X, pady=(0, 15))
        self.custom_period_frame.pack_forget()

        # Дата "от"
        from_frame = ctk.CTkFrame(self.custom_period_frame, fg_color="transparent")
        from_frame.pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkLabel(from_frame, text="От:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["from_day"] = ctk.CTkComboBox(
            from_frame, width=60, values=[f"{i:02d}" for i in range(1, 32)]
        )
        self.entry_fields["from_day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["from_month"] = ctk.CTkComboBox(
            from_frame, width=60, values=[f"{i:02d}" for i in range(1, 13)]
        )
        self.entry_fields["from_month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["from_year"] = ctk.CTkComboBox(
            from_frame, width=80, values=[str(y) for y in range(2000, 2051)]
        )
        self.entry_fields["from_year"].pack(side=tk.LEFT)

        # Дата "до"
        to_frame = ctk.CTkFrame(self.custom_period_frame, fg_color="transparent")
        to_frame.pack(side=tk.LEFT)

        ctk.CTkLabel(to_frame, text="До:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["to_day"] = ctk.CTkComboBox(
            to_frame, width=60, values=[f"{i:02d}" for i in range(1, 32)]
        )
        self.entry_fields["to_day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["to_month"] = ctk.CTkComboBox(
            to_frame, width=60, values=[f"{i:02d}" for i in range(1, 13)]
        )
        self.entry_fields["to_month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["to_year"] = ctk.CTkComboBox(
            to_frame, width=80, values=[str(y) for y in range(2000, 2051)]
        )
        self.entry_fields["to_year"].pack(side=tk.LEFT)

        # 3. Работник
        worker_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        worker_frame.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(worker_frame, text="Работник:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["worker"] = AutocompleteCombobox(
            worker_frame,
            search_function=self.worker_service.find_by_name,
            display_key="short_name",
            select_callback=self._on_worker_selected
        )
        self.entry_fields["worker"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 4. Вид работы
        work_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        work_type_frame.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(work_type_frame, text="Вид работы:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["work_type"] = AutocompleteCombobox(
            work_type_frame,
            search_function=self.work_type_service.find_by_name,
            display_key="get_display_name",
            select_callback=self._on_work_type_selected
        )
        self.entry_fields["work_type"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 5. Изделие
        product_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        product_frame.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(product_frame, text="Изделие:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["product"] = AutocompleteCombobox(
            product_frame,
            search_function=self.product_service.find_by_name,
            display_key="get_display_name",
            select_callback=self._on_product_selected
        )
        self.entry_fields["product"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 6. Контракт
        contract_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        contract_frame.pack(fill=tk.X, pady=(0, 20))

        ctk.CTkLabel(contract_frame, text="Контракт:", **UI_SETTINGS['label_style']).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.entry_fields["contract"] = AutocompleteCombobox(
            contract_frame,
            search_function=self.contract_service.find_by_number,
            display_key="get_display_name",
            select_callback=self._on_contract_selected
        )
        self.entry_fields["contract"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 7. Чекбоксы для статистики
        options_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        options_frame.pack(fill=tk.X, pady=(0, 20))

        # Виды работ
        self.include_works_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame,
            text="Включить количество видов работ",
            variable=self.include_works_var
        ).pack(side=tk.LEFT, padx=5)

        # Изделия
        self.include_products_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame,
            text="Включить количество изделий",
            variable=self.include_products_var
        ).pack(side=tk.LEFT, padx=5)

        # Контракты
        self.include_contracts_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame,
            text="Включить количество контрактов",
            variable=self.include_contracts_var
        ).pack(side=tk.LEFT, padx=5)

        # 8. Кнопки действий
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        self.generate_button = ctk.CTkButton(
            action_frame,
            text="Сформировать",
            command=self._on_generate_report,
            **UI_SETTINGS['button_style']
        )
        self.generate_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.export_button = ctk.CTkButton(
            action_frame,
            text="Экспорт",
            command=self._on_export,
            **UI_SETTINGS['button_style']
        )
        self.export_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="Очистить",
            command=self._on_clear,
            fg_color="#9E9E9E",
            hover_color="#757575",
            **UI_SETTINGS['button_style']
        )
        self.clear_button.pack(side=tk.RIGHT)

        # Привязываем событие Enter к кнопке "Сформировать"
        self.bind("<Return>", lambda event: self._on_generate_report())
        self.bind("<KP_Enter>", lambda event: self._on_generate_report())

        # Загружаем значения по умолчанию
        self._load_default_values()

    def _load_default_values(self) -> None:
        """Загружает значения по умолчанию в поля формы."""
        today = date.today()
        self.entry_fields["from_day"].set(f"{today.day:02d}")
        self.entry_fields["from_month"].set(f"{today.month:02d}")
        self.entry_fields["from_year"].set(str(today.year))
        self.entry_fields["to_day"].set(f"{today.day:02d}")
        self.entry_fields["to_month"].set(f"{today.month:02d}")
        self.entry_fields["to_year"].set(str(today.year))

    def _on_period_changed(self, value: str) -> None:
        """Обработчик изменения периода."""
        if value == "Произвольный период":
            self.custom_period_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        else:
            self.custom_period_frame.pack_forget()
            self._update_dates_by_period(value)

    def _update_dates_by_period(self, period: str) -> None:
        """Обновляет даты в зависимости от выбранного периода."""
        today = date.today()
        if period == "Текущий месяц":
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, self._get_last_day_of_month(today.year, today.month))
        elif period == "Текущий год":
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        else:
            return

        self.entry_fields["from_day"].set(f"{start_date.day:02d}")
        self.entry_fields["from_month"].set(f"{start_date.month:02d}")
        self.entry_fields["from_year"].set(str(start_date.year))
        self.entry_fields["to_day"].set(f"{end_date.day:02d}")
        self.entry_fields["to_month"].set(f"{end_date.month:02d}")
        self.entry_fields["to_year"].set(str(end_date.year))

    def _get_last_day_of_month(self, year: int, month: int) -> int:
        """Возвращает последний день месяца."""
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - date(year, month, 1)).days

    def _on_generate_report(self) -> None:
        """Обработчик события генерации отчета."""
        try:
            # Собираем параметры
            params = self._get_report_params()

            # Генерируем отчет
            df, summary = self.report_service.generate_report(params)

            # Вызываем callback
            if self.on_generate:
                self.on_generate(df, summary)

        except Exception as e:
            logger.error(f"Ошибка при формировании отчета: {e}", exc_info=True)
            self.show_error_message(str(e))

    def _get_report_params(self) -> Dict[str, Any]:
        """Собирает параметры отчета из формы."""
        period = self.entry_fields["period"].get()

        # Общие параметры
        params = {
            "include_works_count": self.include_works_var.get(),
            "include_products_count": self.include_products_var.get(),
            "include_contracts_count": self.include_contracts_var.get()
        }

        # Работник
        worker = self.entry_fields["worker"].selected_item
        if worker:
            if isinstance(worker, dict):
                params["worker_id"] = worker.get("id")
            else:
                params["worker_id"] = worker.id if worker else None

        # Вид работы
        work_type = self.entry_fields["work_type"].selected_item
        if work_type:
            if isinstance(work_type, dict):
                params["work_type_id"] = work_type.get("id")
            else:
                params["work_type_id"] = work_type.id if work_type else None

        # Изделие
        product = self.entry_fields["product"].selected_item
        if product:
            if isinstance(product, dict):
                params["product_id"] = product.get("id")
            else:
                params["product_id"] = product.id if product else None

        # Контракт
        contract = self.entry_fields["contract"].selected_item
        if contract:
            if isinstance(contract, dict):
                params["contract_id"] = contract.get("id")
            else:
                params["contract_id"] = contract.id if contract else None

        # Даты
        if period == "Произвольный период":
            try:
                start_date = date(
                    int(self.entry_fields["from_year"].get()),
                    int(self.entry_fields["from_month"].get()),
                    int(self.entry_fields["from_day"].get())
                )
                end_date = date(
                    int(self.entry_fields["to_year"].get()),
                    int(self.entry_fields["to_month"].get()),
                    int(self.entry_fields["to_day"].get())
                )
                if start_date > end_date:
                    raise ValueError("Дата начала не может быть позже даты окончания")
                params["start_date"] = start_date
                params["end_date"] = end_date
            except ValueError as ve:
                raise ValueError(f"Некорректная дата: {ve}")

        return params

    def _on_export(self) -> None:
        """Обработчик события экспорта отчета."""
        export_window = ctk.CTkToplevel(self)
        export_window.title("Выбор формата экспорта")
        export_window.geometry("300x150")
        export_window.resizable(False, False)

        # Центрируем окно
        x = (export_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (export_window.winfo_screenheight() // 2) - (150 // 2)
        export_window.geometry(f"+{x}+{y}")

        export_frame = ctk.CTkFrame(export_window)
        export_frame.pack(pady=20)

        ctk.CTkLabel(export_frame, text="Формат экспорта:", **UI_SETTINGS['label_style']).pack(pady=5)
        export_format = ctk.CTkComboBox(export_frame, values=["Excel", "PDF", "HTML"])
        export_format.pack(pady=5)

        def _export_data():
            """Выполняет экспорт данных."""
            try:
                # Собираем параметры
                params = self._get_report_params()

                # Генерируем отчет
                df, summary = self.report_service.generate_report(params)

                if df.empty:
                    raise ValueError("Нет данных для экспорта")

                # Экспортируем отчет
                file_path = self.report_exporter.export(df, summary, export_format=export_format.get())

                if file_path:
                    self.show_success_message(f"Отчет успешно экспортирован в {export_format.get()}\nФайл: {file_path}")
                else:
                    raise ValueError("Не удалось экспортировать отчет")

            except Exception as e:
                self.show_error_message(str(e))
            finally:
                export_window.destroy()

        ctk.CTkButton(
            export_frame,
            text="Экспортировать",
            command=_export_data,
            **UI_SETTINGS['button_style']
        ).pack()

    def _on_clear(self) -> None:
        """Обработчик события очистки формы."""
        # Сбрасываем период
        self.entry_fields["period"].set("Текущий месяц")
        self._update_dates_by_period("Текущий месяц")

        # Очищаем автозаполнение
        self.entry_fields["worker"].clear()
        self.entry_fields["work_type"].clear()
        self.entry_fields["product"].clear()
        self.entry_fields["contract"].clear()

        # Сбрасываем чекбоксы
        self.include_works_var.set(False)
        self.include_products_var.set(False)
        self.include_contracts_var.set(False)

        # Вызываем callback, если он есть
        if self.on_generate:
            self.on_generate(pd.DataFrame(), {})

    def _on_worker_selected(self, worker: Dict[str, Any]) -> None:
        """Обработчик выбора работника."""
        if worker:
            params["worker_id"] = worker.get("id")

    def _on_work_type_selected(self, work_type: Dict[str, Any]) -> None:
        """Обработчик выбора вида работы."""
        if work_type:
            params["work_type_id"] = work_type.get("id")

    def _on_product_selected(self, product: Dict[str, Any]) -> None:
        """Обработчик выбора изделия."""
        if product:
            params["product_id"] = product.get("id")

    def _on_contract_selected(self, contract: Dict[str, Any]) -> None:
        """Обработчик выбора контракта."""
        if contract:
            params["contract_id"] = contract.get("id")