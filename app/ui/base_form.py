"""
File: app/core/forms/base_form.py
Базовый класс для всех форм с общей логикой валидации, отображения и обработки событий.
"""
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox
from typing import Any, Dict, List, Optional, Callable
import customtkinter as ctk
from app.config import UI_SETTINGS
import logging

from app.ui.autocomplete_combobox import AutocompleteCombobox

logger = logging.getLogger(__name__)


class BaseForm(ctk.CTkToplevel):
    """
    Базовая форма с общей логикой для всех форм.

    Attributes:
        entry_fields: Словарь с полями ввода
        form_validators: Список валидаторов формы
        on_save_callback: Callback-функция после сохранения
        display_key: Ключ для отображения в автозаполнении
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация базовой формы.

        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.parent = parent
        self.entry_fields = {}
        self.form_validators = []
        self.on_save_callback = None
        self.display_key = "name"

        # Настройка окна
        self._setup_window()

        # Создаем контейнер для формы
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def _setup_window(self) -> None:
        """Настройка параметров окна."""
        self.title("Новая форма")
        self.geometry(f"{UI_SETTINGS['form_width']}x{UI_SETTINGS['form_height']}")

        # Центрируем окно
        x = (self.winfo_screenwidth() // 2) - (UI_SETTINGS['form_width'] // 2)
        y = (self.winfo_screenheight() // 2) - (UI_SETTINGS['form_height'] // 2)
        self.geometry(f"+{x}+{y}")

        # Устанавливаем иконку
        if UI_SETTINGS.get('icon_path') and os.path.exists(UI_SETTINGS['icon_path']):
            self.iconbitmap(UI_SETTINGS['icon_path'])

    def bind_save_event(self, widget: tk.Widget, callback: Callable) -> None:
        """
        Привязывает событие сохранения к виджету.

        Args:
            widget: Виджет, к которому привязываем событие
            callback: Функция обратного вызова
        """
        widget.bind("<Return>", lambda e: self._on_save(callback))
        widget.bind("<KP_Enter>", lambda e: self._on_save(callback))

    def _on_save(self, callback: Callable) -> None:
        """
        Обработчик события сохранения.

        Args:
            callback: Функция сохранения
        """
        try:
            if self.validate():
                result = callback()
                if result[0]:  # Успех
                    self.show_success_message()
                    if self.on_save_callback:
                        self.on_save_callback()
                    self.clear()
                else:
                    self.show_error_message(result[1] or "Не удалось сохранить данные")
        except Exception as e:
            logger.error(f"Ошибка сохранения формы: {e}", exc_info=True)
            self.show_error_message(f"Не удалось сохранить данные: {str(e)}")

    def validate(self) -> bool:
        """Валидирует данные формы."""
        try:
            # Проверяем общие поля
            if not self._validate_form_fields():
                return False

            # Проверяем дополнительные валидаторы
            for validator in self.form_validators:
                if not validator():
                    return False

            return True

        except Exception as e:
            logger.error(f"Ошибка валидации формы: {e}", exc_info=True)
            return False

    def _validate_form_fields(self) -> bool:
        """Проверяет обязательные поля формы."""
        for field_name, field in self.entry_fields.items():
            if isinstance(field, ctk.CTkEntry) and not field.get().strip():
                self.show_error_message(f"Поле '{field_name}' обязательно")
                return False
        return True

    def clear(self) -> None:
        """Очищает поля формы."""
        for field in self.entry_fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, tk.END)
            elif isinstance(field, AutocompleteCombobox):
                field.clear()

    def show_success_message(self) -> None:
        """Отображает сообщение об успешном сохранении."""
        messagebox.showinfo("Успех", "Данные успешно сохранены")

    def show_error_message(self, message: str) -> None:
        """Отображает сообщение об ошибке.

        Args:
            message: Текст ошибки
        """
        messagebox.showerror("Ошибка", message)

    def refresh(self) -> None:
        """Обновляет данные в форме."""
        pass

    def set_validator(self, validator: Callable) -> None:
        """
        Добавляет валидатор формы.

        Args:
            validator: Функция валидации
        """
        if validator not in self.form_validators:
            self.form_validators.append(validator)

    def remove_validator(self, validator: Callable) -> None:
        """
        Удаляет валидатор формы.

        Args:
            validator: Функция валидации
        """
        if validator in self.form_validators:
            self.form_validators.remove(validator)

    def set_on_save(self, callback: Callable) -> None:
        """
        Устанавливает callback-функцию для сохранения.

        Args:
            callback: Функция сохранения
        """
        self.on_save_callback = callback

    def _validate_date(self, day: str, month: str, year: str) -> Optional[date]:
        """
        Проверяет корректность даты.

        Args:
            day: День
            month: Месяц
            year: Год

        Returns:
            Дата или None
        """
        try:
            return date(int(year), int(month), int(day))
        except ValueError as ve:
            self.show_error_message(f"Некорректная дата: {ve}")
            return None

    def _validate_relations(self) -> bool:
        """
        Проверяет связи с другими сущностями.

        Returns:
            True если связи корректны, иначе False
        """
        return True

    def _get_display_value(self, item: Dict[str, Any]) -> str:
        """
        Получает значение для отображения из элемента.

        Args:
            item: Элемент данных

        Returns:
            Значение для отображения
        """
        return str(item.get(self.display_key, "")) if item else ""