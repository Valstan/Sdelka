"""
File: app/ui/report_preview.py
Форма для отображения данных сгенерированного отчета.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Any, Dict, Optional, Callable
import logging
import pandas as pd

from app.config import UI_SETTINGS
from app.config import APP_WIDTH, APP_HEIGHT
from app.ui.work_card_form import WorkCardForm

logger = logging.getLogger(__name__)


class ReportPreview(ctk.CTkFrame):
    """
    Фрейм для отображения данных отчета.

    Attributes:
        preview_table: Таблица для отображения детализации
        summary_frame: Фрейм для отображения сводной информации
        summary_labels: Словарь с лейблами для сводки
    """

    def __init__(
            self,
            parent: tk.Widget,
            on_export: Optional[Callable] = None
    ):
        """
        Инициализация фрейма отчета.

        Args:
            parent: Родительский виджет
            on_export: Callback-функция для экспорта
        """
        super().__init__(parent)
        self.parent = parent
        self.on_export = on_export
        self.preview_table = None
        self.summary_frame = None
        self.summary_labels = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка интерфейса формы."""
        # Добавляем заголовок
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text="Просмотр отчета",
            **UI_SETTINGS['header_style']
        ).pack(side=tk.LEFT)

        if self.on_export:
            export_btn = ctk.CTkButton(
                header_frame,
                text="Экспорт",
                command=self.on_export,
                **UI_SETTINGS['button_style']
            )
            export_btn.pack(side=tk.RIGHT)

        # Фрейм для сводной информации
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Таблица с данными
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Создаем таблицу
        self.preview_table = ttk.Treeview(
            table_container,
            show="headings",
            selectmode="browse"
        )

        # Определяем стили
        style = ttk.Style()
        style.configure("Treeview", rowheight=UI_SETTINGS.get('row_height', 28))
        style.configure("Treeview.Heading", font=UI_SETTINGS.get('header_font', ('Roboto', 11, 'bold')))

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.preview_table.yview
        )
        self.preview_table.configure(yscroll=scrollbar.set)

        # Размещаем таблицу
        self.preview_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def display_report(self, df: pd.DataFrame, summary: Dict[str, Any]) -> None:
        """
        Отображает данные отчета.

        Args:
            df: DataFrame с данными
            summary: Сводная информация по отчету
        """
        try:
            # Обновляем сводную информацию
            self._update_summary(summary)

            # Очищаем таблицу
            self._clear_table()

            # Проверяем, есть ли данные
            if df.empty:
                logger.info("Нет данных для отображения в отчете")
                return

            # Добавляем колонки
            for column in df.columns:
                self.preview_table.heading(column, text=column)
                self.preview_table.column(column, width=100)

            # Добавляем данные
            for _, row in df.iterrows():
                self.preview_table.insert("", "end", values=tuple(row))

            # Автоматически подстраиваем ширину колонок
            self._adjust_column_widths()

        except Exception as e:
            logger.error(f"Ошибка отображения отчета: {e}", exc_info=True)
            raise

    def _update_summary(self, summary: Dict[str, Any]) -> None:
        """
        Обновляет сводную информацию по отчету.

        Args:
            summary: Словарь со статистикой
        """
        # Удаляем старые лейблы
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        if not summary or not isinstance(summary, dict):
            return

        # Создаем новые лейблы
        summary_container = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        summary_container.pack(fill=tk.X)

        metrics = [
            ("total_amount", "Итоговая сумма"),
            ("total_cards", "Количество нарядов"),
            ("total_workers", "Количество работников"),
            ("total_products", "Количество изделий"),
            ("total_contracts", "Количество контрактов"),
            ("works_count", "Количество видов работ"),
            ("total_quantity", "Общее количество работ")
        ]

        for key, display_name in metrics:
            if key in summary:
                self._add_summary_item(display_name, summary[key])

    def _add_summary_item(self, label: str, value: Any) -> None:
        """
        Добавляет элемент в сводную информацию.

        Args:
            label: Название метрики
            value: Значение
        """
        item_frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        item_frame.pack(fill=tk.X, padx=5, pady=3)

        ctk.CTkLabel(
            item_frame,
            text=f"{label}:",
            width=150,
            anchor="w",
            **UI_SETTINGS['label_style']
        ).pack(side=tk.LEFT)

        ctk.CTkLabel(
            item_frame,
            text=str(value),
            width=100,
            anchor="w",
            **UI_SETTINGS['label_style']
        ).pack(side=tk.LEFT)

    def _clear_table(self) -> None:
        """Очищает таблицу от данных."""
        for item in self.preview_table.get_children():
            self.preview_table.delete(item)

        # Удаляем заголовки
        for col in self.preview_table["columns"]:
            self.preview_table.heading(col, text="")
            self.preview_table.column(col, width=0)

    def _adjust_column_widths(self) -> None:
        """Автоматически подстраивает ширину колонок."""
        for col in self.preview_table["columns"]:
            max_width = 100
            for item in self.preview_table.get_children():
                cell_text = self.preview_table.item(item, "values")[self.preview_table["columns"].index(col)]
                max_width = max(max_width, len(str(cell_text)) * 10)
            self.preview_table.column(col, width=min(max_width, 300))

    def _export_report(self) -> None:
        """Обработчик события экспорта отчета."""
        if self.on_export:
            self.on_export()

    def _on_double_click(self, event: tk.Event) -> None:
        """
        Обработчик двойного клика по строке отчета.

        Args:
            event: Событие клика
        """
        try:
            # Получаем выбранную строку
            item_id = self.preview_table.identify_row(event.y)
            if not item_id:
                return

            # Открываем карточку наряда
            item_data = self.preview_table.item(item_id)
            card_id = item_data['values'][0]

            # Открываем форму редактирования
            card = self.card_service.get_work_card_by_id(card_id)
            if card:
                edit_window = ctk.CTkToplevel(self)
                edit_window.title(f"Редактирование наряда {card.card_number}")
                edit_window.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")

                x = (self.winfo_screenwidth() // 2) - (APP_WIDTH // 2)
                y = (self.winfo_screenheight() // 2) - (APP_HEIGHT // 2)
                edit_window.geometry(f"+{x}+{y}")

                WorkCardForm(edit_window, card, self.card_service, on_save=self.load_report)
                edit_window.focus_set()

        except Exception as e:
            logger.error(f"Ошибка при открытии наряда: {e}", exc_info=True)
            self.show_error_message(f"Не удалось открыть наряд: {str(e)}")

    def load_report(self, df: pd.DataFrame, summary: Dict[str, Any]) -> None:
        """
        Загружает данные отчета в таблицу.

        Args:
            df: DataFrame с данными
            summary: Словарь с обобщенными данными
        """
        try:
            self.display_report(df, summary)
        except Exception as e:
            logger.error(f"Ошибка загрузки отчета: {e}", exc_info=True)
            self.show_error_message(f"Не удалось загрузить отчет: {str(e)}")

    def show(self) -> None:
        """Показывает фрейм отчета."""
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self) -> None:
        """Скрывает фрейм отчета."""
        self.pack_forget()