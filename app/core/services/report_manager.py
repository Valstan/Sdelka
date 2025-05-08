"""
File: app/core/services/report_manager.py
Менеджер отчетов с фильтрацией, экспортами и навигацией.
"""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from datetime import date, datetime
from typing import Any, Dict
import logging
import pandas as pd

from app.core.services.report_service import ReportService
from app.report.report_exporter import ReportExporter
from app.report.report_form import ReportForm
from app.ui.report_preview import ReportPreview
from app.utils.ui_utils import UI_SETTINGS, DATE_FORMATS
from app.utils.ui_utils import DIRECTORIES

logger = logging.getLogger(__name__)


class ReportManager:
    """
    Класс для управления отчетами и навигацией между ними.
    Поддерживает фильтрацию, экспорт и просмотр.
    """

    def __init__(
        self,
        parent: tk.Widget,
        report_service: ReportService,
        export_dir: str = DIRECTORIES
    ):
        """
        Инициализация менеджера отчетов.

        Args:
            parent: Родительский виджет
            report_service: Сервис для генерации отчетов
            export_dir: Директория для экспорта
        """
        self.parent = parent
        self.report_service = report_service
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.current_df = None
        self.current_summary = None
        self.preview_frame = None
        self.form = None
        self.exporter = ReportExporter()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка интерфейса формы и предпросмотра."""
        # Фрейм для формы
        form_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        form_container.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Форма отчета
        self.form = ReportForm(
            form_container,
            report_service=self.report_service,
            on_generate=self.display_report
        )

        # Фрейм для предпросмотра
        preview_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        preview_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Предпросмотр отчета
        self.preview_frame = ReportPreview(preview_container, on_export=self.export_report)

    def display_report(self, df: pd.DataFrame, summary: Dict[str, Any]) -> None:
        """
        Отображает данные отчета в таблице.

        Args:
            df: DataFrame с данными
            summary: Сводная информация
        """
        self.current_df = df
        self.current_summary = summary
        self.preview_frame.display_report(df, summary)

    def generate_report(self) -> None:
        """Генерирует отчет на основе фильтров формы."""
        try:
            # Получаем параметры
            params = self.form.get_report_params()

            # Проверяем параметры
            if not params:
                return

            # Генерируем отчет
            df, summary = self.report_service.generate_report(params)

            # Отображаем результат
            self.display_report(df, summary)

        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось сгенерировать отчет: {str(e)}")

    def export_report(self) -> None:
        """Экспортирует текущий отчет."""
        if self.current_df is None or self.current_df.empty:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
            return

        try:
            # Открываем диалог выбора формата
            export_window = ctk.CTkToplevel(self.parent)
            export_window.title("Выбор формата")
            export_window.geometry("300x150")
            export_window.resizable(False, False)

            # Центрируем окно
            x = (self.parent.winfo_screenwidth() // 2) - (300 // 2)
            y = (self.parent.winfo_screenheight() // 2) - (150 // 2)
            export_window.geometry(f"+{x}+{y}")

            # Выбор формата
            export_frame = ctk.CTkFrame(export_window)
            export_frame.pack(pady=20)

            ctk.CTkLabel(export_frame, text="Формат экспорта:", **UI_SETTINGS['label_style']).pack(pady=5)
            export_format = ctk.CTkComboBox(export_frame, values=["Excel", "PDF", "HTML"])
            export_format.pack(pady=5)

            def _on_export():
                """Обработчик события экспорта."""
                try:
                    format_ = export_format.get().lower()
                    file_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_}"
                    file_path = self.export_dir / file_name

                    # Экспортируем
                    success = self.exporter.export(self.current_df, self.current_summary, file_path, format_)

                    if success:
                        messagebox.showinfo("Успех", f"Отчет успешно экспортирован\n{file_path}")
                        export_window.destroy()
                    else:
                        raise Exception("Не удалось экспортировать отчет")

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось экспортировать отчет: {str(e)}")

            # Кнопка экспорта
            export_btn = ctk.CTkButton(export_frame, text="Экспортировать", command=_on_export)
            export_btn.pack()

        except Exception as e:
            logger.error(f"Ошибка экспорта отчета: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось открыть диалог экспорта: {str(e)}")

    def apply_filters(self) -> None:
        """Применяет фильтры к отчету."""
        try:
            # Получаем параметры из формы
            params = self.form.get_report_params()

            # Обновляем данные
            if self.current_df is not None:
                df = self._apply_filters_to_df(params)
                self.display_report(df, self._calculate_filtered_summary(df, params))

        except Exception as e:
            logger.error(f"Ошибка применения фильтров: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось применить фильтры: {str(e)}")

    def _apply_filters_to_df(self, params: Dict[str, Any]) -> pd.DataFrame:
        """Применяет фильтры к DataFrame."""
        df = self.current_df.copy()

        # Фильтр по дате
        if "start_date" in params and "end_date" in params:
            df = df[(df["card_date"] >= params["start_date"]) & (df["card_date"] <= params["end_date"])]

        # Фильтр по работнику
        if "worker_id" in params:
            df = df[df["worker_id"] == params["worker_id"]]

        # Фильтр по виду работы
        if "work_type_id" in params:
            df = df[df["work_type_id"] == params["work_type_id"]]

        # Фильтр по изделию
        if "product_id" in params:
            df = df[df["product_id"] == params["product_id"]]

        # Фильтр по контракту
        if "contract_id" in params:
            df = df[df["contract_id"] == params["contract_id"]]

        return df

    def _calculate_filtered_summary(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитывает сводную статистику для отфильтрованных данных."""
        summary = {
            "total_amount": df["amount"].sum() if "amount" in df.columns else 0.0,
            "total_cards": df["id"].nunique() if "id" in df.columns else 0,
            "total_workers": df["worker_id"].nunique() if "worker_id" in df.columns else 0,
            "total_products": df["product_id"].nunique() if "product_id" in df.columns else 0,
            "total_contracts": df["contract_id"].nunique() if "contract_id" in df.columns else 0,
            "works_count": df["work_type_id"].nunique() if "work_type_id" in df.columns else 0,
            "total_quantity": df["quantity"].sum() if "quantity" in df.columns else 0,
            "start_date": params.get("start_date").strftime(DATE_FORMATS['ui']) if params.get("start_date") else "",
            "end_date": params.get("end_date").strftime(DATE_FORMATS['ui']) if params.get("end_date") else ""
        }

        # Условия включения
        if not params.get("include_works_count", False):
            summary.pop("works_count", None)
        if not params.get("include_products_count", False):
            summary.pop("total_products", None)
        if not params.get("include_contracts_count", False):
            summary.pop("total_contracts", None)

        return summary

    def navigate_previous(self) -> None:
        """Переход к предыдущему отчету."""
        if self.current_df is not None and not self.current_df.empty:
            # Получаем предыдущий период
            current_start = self.current_summary.get("start_date")
            if current_start:
                start_date = datetime.strptime(current_start, DATE_FORMATS['ui']).date()
                end_date = start_date.replace(day=1)
                if start_date.month == 1:
                    end_date = end_date.replace(year=start_date.year - 1, month=12)
                else:
                    end_date = end_date.replace(month=start_date.month - 1)

                # Обновляем форму
                self.form.entry_fields["from_year"].set(str(end_date.year))
                self.form.entry_fields["from_month"].set(f"{end_date.month:02d}")
                self.form.entry_fields["from_day"].set("01")
                self.form.entry_fields["to_year"].set(str(end_date.year))
                self.form.entry_fields["to_month"].set(f"{end_date.month:02d}")
                self.form.entry_fields["to_day"].set(f"{self.form._get_last_day_of_month(end_date.year, end_date.month):02d}")

                # Генерируем новый отчет
                self.generate_report()

    def navigate_next(self) -> None:
        """Переход к следующему отчету."""
        if self.current_df is not None and not self.current_df.empty:
            # Получаем текущий период
            current_end = self.current_summary.get("end_date")
            if current_end:
                end_date = datetime.strptime(current_end, DATE_FORMATS['ui']).date()
                next_date = end_date.replace(day=1) + pd.DateOffset(months=1)
                next_date = next_date.date()

                # Обновляем форму
                self.form.entry_fields["from_year"].set(str(next_date.year))
                self.form.entry_fields["from_month"].set(f"{next_date.month:02d}")
                self.form.entry_fields["from_day"].set("01")
                self.form.entry_fields["to_year"].set(str(next_date.year))
                self.form.entry_fields["to_month"].set(f"{next_date.month:02d}")
                self.form.entry_fields["to_day"].set(f"{self.form._get_last_day_of_month(next_date.year, next_date.month):02d}")

                # Генерируем новый отчет
                self.generate_report()

    def navigate_custom(self) -> None:
        """Переход к произвольному периоду."""
        try:
            # Открываем диалог ввода дат
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title("Произвольный период")
            dialog.geometry("300x150")
            dialog.resizable(False, False)

            # Центрируем окно
            x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
            y = (dialog.winfo_screenheight() // 2) - (150 // 2)
            dialog.geometry(f"+{x}+{y}")

            # Форма выбора дат
            date_frame = ctk.CTkFrame(dialog)
            date_frame.pack(pady=20)

            # Дата "от"
            from_frame = ctk.CTkFrame(date_frame)
            from_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            ctk.CTkLabel(from_frame, text="От:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

            from_day = ctk.CTkComboBox(from_frame, width=60, values=[f"{i:02d}" for i in range(1, 32)])
            from_day.pack(side=tk.LEFT, padx=(0, 5))

            from_month = ctk.CTkComboBox(from_frame, width=60, values=[f"{i:02d}" for i in range(1, 13)])
            from_month.pack(side=tk.LEFT, padx=(0, 5))

            from_year = ctk.CTkComboBox(from_frame, width=80, values=[str(i) for i in range(2000, 2051)])
            from_year.pack(side=tk.LEFT)

            # Дата "до"
            to_frame = ctk.CTkFrame(date_frame)
            to_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            ctk.CTkLabel(to_frame, text="До:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

            to_day = ctk.CTkComboBox(to_frame, width=60, values=[f"{i:02d}" for i in range(1, 32)])
            to_day.pack(side=tk.LEFT, padx=(0, 5))

            to_month = ctk.CTkComboBox(to_frame, width=60, values=[f"{i:02d}" for i in range(1, 13)])
            to_month.pack(side=tk.LEFT, padx=(0, 5))

            to_year = ctk.CTkComboBox(to_frame, width=80, values=[str(i) for i in range(2000, 2051)])
            to_year.pack(side=tk.LEFT)

            def _on_submit():
                """Обработчик отправки формы."""
                try:
                    start_date = date(int(from_year.get()), int(from_month.get()), int(from_day.get()))
                    end_date = date(int(to_year.get()), int(to_month.get()), int(to_day.get()))

                    if start_date > end_date:
                        raise ValueError("Дата начала не может быть позже даты окончания")

                    # Обновляем форму
                    self.form.entry_fields["from_year"].set(str(start_date.year))
                    self.form.entry_fields["from_month"].set(f"{start_date.month:02d}")
                    self.form.entry_fields["from_day"].set(f"{start_date.day:02d}")
                    self.form.entry_fields["to_year"].set(str(end_date.year))
                    self.form.entry_fields["to_month"].set(f"{end_date.month:02d}")
                    self.form.entry_fields["to_day"].set(f"{end_date.day:02d}")

                    # Генерируем отчет
                    self.generate_report()
                    dialog.destroy()

                except Exception as e:
                    logger.error(f"Ошибка ввода дат: {e}", exc_info=True)
                    messagebox.showerror("Ошибка", f"Некорректные даты: {e}")

            submit_btn = ctk.CTkButton(dialog, text="Подтвердить", command=_on_submit)
            submit_btn.pack(pady=10)

        except Exception as e:
            logger.error(f"Ошибка навигации: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось открыть диалог: {str(e)}")