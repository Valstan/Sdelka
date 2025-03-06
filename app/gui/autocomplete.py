"""
Модуль для создания компонентов с функцией автозаполнения.
Включает виджеты для поиска и выбора данных из базы данных.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional

class AutocompleteCombobox(ctk.CTkComboBox):
    """
    Выпадающий список с функцией автозаполнения.
    Позволяет искать элементы по мере ввода текста.
    """

    def __init__(self,
                master: Any,
                search_function: Callable[[str], List[Dict[str, Any]]],
                display_key: str,
                value_key: str,
                width: int = 200,
                command: Optional[Callable] = None,
                **kwargs):
        """
        Инициализация комбобокса с автозаполнением.

        Args:
            master: Родительский виджет
            search_function: Функция для поиска данных по тексту
            display_key: Ключ для отображения в выпадающем списке
            value_key: Ключ для получения значения выбранного элемента
            width: Ширина виджета
            command: Функция обратного вызова при выборе элемента
            **kwargs: Дополнительные параметры для CTkComboBox
        """
        super().__init__(master, width=width, **kwargs)

        self.search_function = search_function
        self.display_key = display_key
        self.value_key = value_key
        self.user_command = command

        # Словарь для хранения полных данных элементов
        self.items_data = {}

        # Переменная для отслеживания ввода
        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_var_change)

        # Связываем переменную с полем ввода комбобокса
        self._entry.configure(textvariable=self.var)

        # Привязываем события
        self.bind("<Return>", self._on_enter_pressed)
        self.bind("<Tab>", self._on_tab_pressed)

        # Переопределяем обработчик выбора элемента
        self._original_command = self._command
        self._command = self._on_item_selected

    def _on_var_change(self, *args):
        """Обработчик изменения текста в поле ввода"""
        text = self.var.get()
        if text:
            # Ищем данные с помощью функции поиска
            results = self.search_function(text)

            if results:
                # Формируем список строк для отображения
                display_values = [item[self.display_key] for item in results]

                # Обновляем словарь данных
                self.items_data = {item[self.display_key]: item for item in results}

                # Обновляем список значений
                self.configure(values=display_values)

                # Показываем выпадающий список
                if not self._dropdown_window.winfo_ismapped():
                    self._open_dropdown()
            else:
                # Если ничего не найдено, закрываем выпадающий список
                self._close_dropdown()
        else:
            # Если поле пустое, закрываем выпадающий список
            self._close_dropdown()

    def _on_item_selected(self, selected_value):
        """Обработчик выбора элемента из выпадающего списка"""
        # Вызываем оригинальный обработчик
        if self._original_command:
            self._original_command(selected_value)

        # Получаем полные данные выбранного элемента
        if selected_value in self.items_data:
            selected_item = self.items_data[selected_value]

            # Вызываем пользовательский обработчик, если он задан
            if self.user_command:
                self.user_command(selected_item)

    def _on_enter_pressed(self, event):
        """Обработчик нажатия клавиши Enter"""
        # Если список открыт и есть выбранный элемент, делаем выбор
        if self._dropdown_window.winfo_ismapped() and self._dropdown_list.curselection():
            self._select(self._dropdown_list.curselection()[0])
        else:
            # Иначе вызываем поиск по текущему тексту
            self._on_var_change()

    def _on_tab_pressed(self, event):
        """Обработчик нажатия клавиши Tab"""
        # Аналогично Enter
        if self._dropdown_window.winfo_ismapped() and self._dropdown_list.curselection():
            self._select(self._dropdown_list.curselection()[0])
            return "break"  # Предотвращаем стандартное действие Tab

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """
        Получение полных данных выбранного элемента.

        Returns:
            Dict или None: Данные выбранного элемента или None, если ничего не выбрано
        """
        selected_value = self.get()
        return self.items_data.get(selected_value)

    def get_selected_value(self) -> Any:
        """
        Получение значения выбранного элемента (по value_key).

        Returns:
            Any: Значение выбранного элемента или None, если ничего не выбрано
        """
        item = self.get_selected_item()
        return item.get(self.value_key) if item else None

    def set_by_value(self, value: Any) -> bool:
        """
        Установка выбранного элемента по значению (value_key).

        Args:
            value: Значение для поиска

        Returns:
            bool: True если элемент найден и установлен, иначе False
        """
        # Ищем элемент с заданным значением в словаре данных
        for display_text, item in self.items_data.items():
            if item.get(self.value_key) == value:
                self.set(display_text)
                return True

        # Если не нашли в кэше, можно попробовать поискать в базе
        # Но это требует дополнительной функции поиска по значению

        return False