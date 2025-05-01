"""
File: app/core/forms/autocomplete_combobox.py
Кастомный Combobox с функцией автозаполнения и выпадающим списком.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import date
import logging

from app.core.models.base_model import BaseModel

logger = logging.getLogger(__name__)


class AutocompleteCombobox(ctk.CTkFrame):
    """
    Кастомный Combobox с функцией автозаполнения и выпадающим списком.

    Attributes:
        entry: Поле ввода
        dropdown_window: Выпадающее окно со списком
        listbox: Список элементов в выпадающем окне
        search_function: Функция поиска данных
        display_key: Ключ для отображения в поле ввода
        select_callback: Callback-функция при выборе элемента
        selected_item: Выбранный элемент
        value: Текущее значение
    """

    def __init__(
            self,
            parent: tk.Widget,
            search_function: Optional[Callable] = None,
            display_key: str = "name",
            select_callback: Optional[Callable] = None,
            **kwargs
    ):
        """
        Инициализация AutocompleteCombobox.

        Args:
            parent: Родительский виджет
            search_function: Функция поиска данных
            display_key: Ключ для отображения данных
            select_callback: Callback-функция при выборе элемента
            **kwargs: Дополнительные аргументы для CTkFrame
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.search_function = search_function
        self.display_key = display_key
        self.select_callback = select_callback
        self.selected_item = None
        self._value = ""

        # Создаем поле ввода
        self.entry = ctk.CTkEntry(
            self,
            border_width=1,
            corner_radius=5,
            font=("Roboto", 12)
        )
        self.entry.pack(fill=tk.BOTH, expand=True)

        # Привязываем события
        self.entry.bind('<KeyRelease>', self.on_key_release)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)

        # Создаем окно выпадающего списка
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.withdraw()
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.attributes('-topmost', True)  # Окно поверх всех

        # Создаем фрейм для списка
        self.listbox_frame = ctk.CTkFrame(self.dropdown_window)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем список
        self.listbox = tk.Listbox(
            self.listbox_frame,
            font=("Roboto", 12),
            bg="#2a2d2e",
            fg="white",
            selectbackground="#1f6aa5",
            bd=0,
            highlightthickness=0,
            activestyle="none"
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)

        # Привязываем событие выбора
        self.listbox.bind('<ButtonRelease-1>', self.on_listbox_select)

        # Устанавливаем начальное значение
        self.set("")

    def on_key_release(self, event: tk.Event) -> None:
        """
        Обработчик события KeyRelease.

        Args:
            event: Событие клавиатуры
        """
        if event.keysym in ("Up", "Down", "Return", "KP_Enter"):
            return

        self._value = self.entry.get()
        self.show_dropdown()

    def show_dropdown(self) -> None:
        """Показывает выпадающий список."""
        try:
            # Очищаем список
            self.listbox.delete(0, tk.END)

            # Получаем данные из поисковой функции
            if self.search_function:
                results = self.search_function(self._value) if self._value else self.search_function()

                # Добавляем результаты в список
                for item in results:
                    display_value = self._get_display_value(item)
                    self.listbox.insert(tk.END, display_value)

                # Показываем или скрываем окно
                if results and self.listbox.size() > 0:
                    self._position_dropdown()
                    self.dropdown_window.update_idletasks()
                    self.dropdown_window.deiconify()
                else:
                    self.dropdown_window.withdraw()
            else:
                self.dropdown_window.withdraw()

        except Exception as e:
            logger.error(f"Ошибка показа выпадающего списка: {e}", exc_info=True)

    def _get_display_value(self, item: Union[Dict, BaseModel]) -> str:
        """
        Получает значение для отображения.

        Args:
            item: Элемент данных (словарь или модель)

        Returns:
            Строка для отображения
        """
        if isinstance(item, dict):
            return str(item.get(self.display_key, ""))
        elif hasattr(item, self.display_key):
            return str(getattr(item, self.display_key))
        return ""

    def _position_dropdown(self) -> None:
        """Позиционирует выпадающий список."""
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()

        self.dropdown_window.geometry(f"{width}x200+{x}+{y}")

    def on_listbox_select(self, event: tk.Event) -> None:
        """
        Обработчик выбора элемента в списке.

        Args:
            event: Событие выбора
        """
        try:
            selection = self.listbox.curselection()
            if selection:
                index = selection[0]
                if self.search_function:
                    results = self.search_function(self._value) if self._value else self.search_function()
                    if index < len(results):
                        self.selected_item = results[index]
                        display_value = self._get_display_value(self.selected_item)
                        self.entry.delete(0, tk.END)
                        self.entry.insert(0, display_value)

                        # Вызываем callback
                        if self.select_callback:
                            self.select_callback(self.selected_item)

                        # Скрываем список
                        self.dropdown_window.withdraw()
                        self.focus_set()

        except Exception as e:
            logger.error(f"Ошибка выбора из списка: {e}", exc_info=True)

    def on_focus_in(self, event: tk.Event) -> None:
        """
        Обработчик получения фокуса.

        Args:
            event: Событие фокуса
        """
        self.entry.configure(border_color=("#1f6aa5", "#1f6aa5"))
        self.show_dropdown()

    def on_focus_out(self, event: tk.Event) -> None:
        """
        Обработчик потери фокуса.

        Args:
            event: Событие фокуса
        """
        self.after(100, self.check_focus_out)

    def check_focus_out(self) -> None:
        """Проверяет, находится ли фокус вне виджета."""
        if not self.focus_get() and not self.dropdown_window.focus_get():
            self.dropdown_window.withdraw()

    def clear(self) -> None:
        """Очищает поле ввода и выбранный элемент."""
        self.entry.delete(0, tk.END)
        self.selected_item = None

    def set(self, value: str) -> None:
        """
        Устанавливает значение в поле ввода.

        Args:
            value: Значение для установки
        """
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)

    def get(self) -> str:
        """
        Получает текущее значение из поля ввода.

        Returns:
            Текущее значение
        """
        return self.entry.get()

    def get_selected_item(self) -> Any:
        """
        Получает выбранный элемент.

        Returns:
            Выбранный элемент или None
        """
        return self.selected_item

    def set_selected_item(self, item: Any) -> None:
        """
        Устанавливает выбранный элемент.

        Args:
            item: Элемент для установки
        """
        self.selected_item = item
        if item:
            display_value = self._get_display_value(item)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, display_value)

    def destroy(self) -> None:
        """Уничтожает виджет и его ресурсы."""
        self.dropdown_window.destroy()
        super().destroy()