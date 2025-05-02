# File: app/ui/components/date_field.py

import tkinter as tk
import customtkinter as ctk
from datetime import date
from typing import Optional, Tuple
from logging import getLogger

logger = getLogger(__name__)


class DateField(ctk.CTkFrame):
    """
    Компонент для ввода даты с выпадающими списками для дня, месяца и года.
    """

    def __init__(self, master, label_text: str = "", default_date: Optional[date] = None, **kwargs):
        """
        Инициализация поля ввода даты.

        Args:
            master: Родительский контейнер
            label_text: Текст метки
            default_date: Значение по умолчанию
            kwargs: Дополнительные параметры
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self._setup_ui(label_text, default_date)

    def _setup_ui(self, label_text: str, default_date: Optional[date]) -> None:
        """Настройка интерфейса поля даты."""
        # Метка
        if label_text:
            self.label = ctk.CTkLabel(self, text=label_text)
            self.label.pack(side=tk.LEFT, padx=(0, 5))

        # Компоненты выбора даты
        self.day_combo = ctk.CTkComboBox(self, width=60, values=[f"{i:02d}" for i in range(1, 32)])
        self.day_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.month_combo = ctk.CTkComboBox(self, width=60, values=[f"{i:02d}" for i in range(1, 13)])
        self.month_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.year_combo = ctk.CTkComboBox(self, width=80, values=[str(i) for i in range(2000, 2051)])
        self.year_combo.pack(side=tk.LEFT)

        # Устанавливаем значение по умолчанию
        today = date.today()
        default = default_date or today

        self.day_combo.set(f"{default.day:02d}")
        self.month_combo.set(f"{default.month:02d}")
        self.year_combo.set(str(default.year))

    def get_date(self) -> Optional[date]:
        """Получает значение даты из поля."""
        try:
            day = int(self.day_combo.get())
            month = int(self.month_combo.get())
            year = int(self.year_combo.get())
            return date(year, month, day)
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка получения даты: {e}")
            return None

    def set_date(self, new_date: date) -> None:
        """Устанавливает новое значение даты."""
        self.day_combo.set(f"{new_date.day:02d}")
        self.month_combo.set(f"{new_date.month:02d}")
        self.year_combo.set(str(new_date.year))

    def validate(self, field_name: str = "Дата") -> Tuple[bool, str]:
        """Проверяет, что дата корректна."""
        if not self.get_date():
            return False, f"{field_name} некорректна"
        return True, ""
