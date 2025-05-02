# File: app/ui/base_form.py

import tkinter as tk
from datetime import date
from logging import getLogger
from typing import Dict, Any
from typing import Optional, Callable

import customtkinter as ctk

from app.ui.components.date_field import DateField

logger = getLogger(__name__)


class BaseForm(ctk.CTkToplevel):
    """
    Базовый класс для всех форм приложения.
    Предоставляет общую логику создания форм, валидации и обработки событий.
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Форма",
        width: int = 400,
        height: int = 300,
        on_save: Optional[Callable] = None
    ):
        """
        Инициализация базовой формы.

        Args:
            parent: Родительский виджет
            title: Заголовок формы
            width: Ширина окна
            height: Высота окна
            on_save: Callback-функция после сохранения
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.on_save = on_save
        self.entry_fields = {}  # Словарь для хранения полей ввода
        self.validators = []   # Список валидаторов
        self._setup_ui()

    def _setup_date_field(self, parent, label_text: str, default_date: Optional[date] = None) -> DateField:
        """Создает и настраивает поле даты."""
        field = DateField(parent, label_text, default_date)
        field.pack(fill=tk.X, pady=(0, 15))
        return field

    def _get_date_value(self, field: DateField) -> Optional[date]:
        """Получает значение даты из поля."""
        return field.get_date()

    def _validate_date(self, field: DateField, field_name: str) -> bool:
        """Проверяет, что дата корректна."""
        is_valid, message = field.validate(field_name)
        if not is_valid:
            self.show_error_message(message)
        return is_valid

    def _validate_date_range(self, start_field: DateField, end_field: DateField) -> bool:
        """Проверяет, что начальная дата не позже конечной."""
        start_date = self._get_date_value(start_field)
        end_date = self._get_date_value(end_field)

        if start_date and end_date and start_date > end_date:
            self.show_error_message("Дата начала не может быть позже даты окончания")
            return False
        return True

    def _setup_ui(self) -> None:
        """Настройка базового интерфейса формы."""
        self._center_window()

        # Основной фрейм
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Кнопки действий
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            self.action_frame,
            text="Сохранить",
            command=self._on_save,
            fg_color="#1f6aa5",
            hover_color="#144b78"
        )
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.cancel_button = ctk.CTkButton(
            self.action_frame,
            text="Отмена",
            command=self._on_cancel,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        self.cancel_button.pack(side=tk.RIGHT)

        # Привязываем события
        self.bind("<Return>", lambda event: self._on_save())
        self.bind("<KP_Enter>", lambda event: self._on_save())
        self.bind("<Escape>", lambda event: self._on_cancel())

    def _center_window(self) -> None:
        """Центрирует окно на экране."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_save(self) -> None:
        """Обработчик события сохранения."""
        try:
            if self.validate():
                data = self._get_form_data()
                if self.on_save:
                    self.on_save(data)
                self.destroy()
        except Exception as e:
            self.show_error_message(str(e))

    def _on_cancel(self) -> None:
        """Обработчик события отмены."""
        self.clear()
        self.destroy()

    def _get_form_data(self) -> Dict[str, Any]:
        """Получает данные из формы."""
        raise NotImplementedError("Метод _get_form_data должен быть реализован в подклассе")

    def validate(self) -> bool:
        """Валидирует данные формы."""
        try:
            # Проверяем общие поля
            if not self._validate_form_fields():
                return False

            # Проверяем дополнительные валидаторы
            for validator in self.validators:
                if not validator():
                    return False

            return True
        except Exception as e:
            self.show_error_message(f"Ошибка валидации: {str(e)}")
            return False

    def _validate_form_fields(self) -> bool:
        """Проверяет обязательные поля формы."""
        raise NotImplementedError("Метод _validate_form_fields должен быть реализован в подклассе")

    def clear(self) -> None:
        """Очищает поля формы."""
        for field in self.entry_fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, tk.END)
            elif isinstance(field, ctk.CTkComboBox):
                field.set("")
            elif isinstance(field, ctk.CTkTextbox):
                field.delete("1.0", tk.END)

    def show_success_message(self) -> None:
        """Показывает сообщение об успешном сохранении."""
        pass  # Может быть переопределен в подклассах

    def show_error_message(self, message: str) -> None:
        """Показывает сообщение об ошибке."""
        pass  # Может быть переопределен в подклассах