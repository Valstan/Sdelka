# File: app/ui/components/autocomplete_combobox.py
"""
CustomTkinter компонент автозаполнения с правильным позиционированием.
"""

import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional
from functools import partial
import logging

logger = logging.getLogger(__name__)


class AutocompleteCombobox(ctk.CTkFrame):
    """
    Компонент автозаполнения для выпадающего списка.

    Attributes:
        parent: Родительский виджет
        search_function: Функция поиска
        display_key: Ключ для отображения
        selected_item: Выбранный элемент
        last_search: Последний выполненный поиск
        suggestions: Список предложенных вариантов
        menu: Меню предложений
        entry: Поле ввода
    """

    def __init__(
            self,
            parent: ctk.CTkFrame,
            search_function: Callable[[str], List[Dict[str, Any]]],
            display_key: str = "name",
            *args,
            **kwargs
    ):
        """
        Инициализирует компонент автозаполнения.

        Args:
            parent: Родительский виджет
            search_function: Функция поиска
            display_key: Ключ для отображения
            args: Дополнительные аргументы для CTkEntry
            kwargs: Дополнительные ключевые аргументы
        """
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.search_function = search_function
        self.display_key = display_key
        self.selected_item = None
        self.last_search = ""
        self.suggestions = []

        # Настройка внешнего вида
        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # Создаем поле ввода
        self.entry = ctk.CTkEntry(self, placeholder_text="Введите значение...", border_width=2)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Down>", self._show_menu)
        self.entry.bind("<Up>", self._hide_menu)
        self.entry.bind("<FocusOut>", lambda e: self._hide_menu())

        # Создаем кнопку для открытия меню
        self.button = ctk.CTkButton(
            self,
            text="▾",
            width=30,
            command=self._show_menu,
            fg_color=["#F0F0F0", "#3B3B3B"],
            hover_color=["#D3D3D3", "#5A5A5A"]
        )
        self.button.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Создаем меню предложений
        self.menu = tk.Menu(
            self.entry,
            tearoff=False,
            bg="white" if ctk.get_appearance_mode() == "Light" else "black",
            fg="black" if ctk.get_appearance_mode() == "Light" else "white"
        )

        # Установка темы
        self._setup_theme_callback()

    def _setup_theme_callback(self) -> None:
        """
        Устанавливает callback для обновления цветовой темы.
        """
        ctk.set_appearance_mode_callback(lambda mode: self._update_theme(mode))

    def _update_theme(self, mode: str) -> None:
        """
        Обновляет тему меню предложений.

        Args:
            mode: Режим темы ('light' или 'dark')
        """
        self.menu.config(
            bg="white" if mode == "Light" else "black",
            fg="black" if mode == "Light" else "white"
        )

    def _on_key_release(self, event: tk.Event) -> None:
        """
        Обработчик события KeyRelease.

        Args:
            event: Событие клавиатуры
        """
        current_search = self.entry.get()

        if current_search == self.last_search:
            return

        self.last_search = current_search

        if len(current_search) < 2:
            self._hide_menu()
            return

        try:
            self.suggestions = self.search_function(current_search)
            if self.suggestions:
                self._update_menu_options()
                self._show_menu(event)
            else:
                self._hide_menu()

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")

    def _update_menu_options(self) -> None:
        """
        Обновляет список опций в меню.
        """
        self.menu.delete(0, tk.END)

        for item in self.suggestions:
            display_value = item.get(self.display_key, "")
            if callable(display_value):
                display_value = display_value()

            self.menu.add_command(
                label=display_value,
                command=partial(self._select_item, item)
            )

    def _show_menu(self, event: Optional[tk.Event] = None) -> None:
        """
        Показывает меню предложений.

        Args:
            event: Событие клавиатуры
        """
        if not self.suggestions:
            return

        try:
            self.menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())
            self.menu.selection_clear()

        finally:
            self.menu.grab_release()

    def _hide_menu(self, event: Optional[tk.Event] = None) -> None:
        """
        Скрывает меню предложений.

        Args:
            event: Событие клавиатуры
        """
        self.menu.unpost()

    def _select_item(self, item: Dict[str, Any]) -> None:
        """
        Выбирает элемент из меню.

        Args:
            item: Выбранный элемент
        """
        self.selected_item = item
        display_value = item.get(self.display_key, "")

        if callable(display_value):
            display_value = display_value()

        self.entry.delete(0, tk.END)
        self.entry.insert(0, display_value)

        self._hide_menu()

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """
        Получает выбранный элемент.

        Returns:
            Выбранный элемент или None
        """
        return self.selected_item

    def clear(self) -> None:
        """
        Очищает выбор и содержимое поля ввода.
        """
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
        self.selected_item = None