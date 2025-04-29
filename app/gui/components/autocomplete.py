# File: app/gui/components/autocomplete.py
"""
CustomTkinter autocomplete combobox component with proper positioning
"""

import tkinter as tk
import logging
from tkinter import ttk
import customtkinter as ctk


class AutocompleteCombobox(ctk.CTkFrame):
    """
    CustomTkinter-based autocomplete combobox with dropdown menu positioning

    Attributes:
        entry (CTkEntry): The input field
        listbox (Listbox): The dropdown list for suggestions
        selected_item (Any): Currently selected item from the list
    """

    def __init__(self, parent, search_function, display_key=None, *args, **kwargs):
        """
        Initialize the AutocompleteCombobox

        Args:
            parent: Parent widget
            search_function: Function to search for suggestions
            display_key: Key to display from dictionary items
            args: Additional arguments
            kwargs: Additional keyword arguments
        """
        super().__init__(parent, *args, **kwargs)

        self.logger = logging.getLogger(__name__)
        self.search_function = search_function
        self.display_key = display_key
        self.selected_item = None

        # Создаем поле ввода
        self.entry = ctk.CTkEntry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Привязываем события
        self.entry.bind('<KeyRelease>', self.on_key_release)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)

        # Создаем окно выпадающего списка
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.withdraw()
        self.dropdown_window.overrideredirect(True)

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
            highlightthickness=0
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавляем скроллбар
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Настройка списка и скроллбара
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        # Привязываем выбор из списка
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        # Привязываем клик вне окна для закрытия
        self.dropdown_window.bind('<Button-1>', self.on_click_outside)

    def on_key_release(self, event):
        """Обрабатывает нажатие клавиш в поле ввода"""
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return

        current_text = self.entry.get()
        if len(current_text) < 2:  # Поиск начинаем после 2 символов
            self.dropdown_window.withdraw()
            return

        try:
            # Получаем результаты поиска
            results = self.search_function(current_text)

            if not results:
                self.dropdown_window.withdraw()
                return

            # Отображаем список
            self.populate_listbox(results)
            self.position_dropdown()
            self.dropdown_window.deiconify()
        except Exception as e:
            self.logger.error(f"Ошибка при обработке ввода: {e}")

    def populate_listbox(self, results):
        """Заполняет список результатами поиска"""
        self.listbox.delete(0, tk.END)

        for item in results:
            if isinstance(item, dict) and self.display_key in item:
                self.listbox.insert(tk.END, item[self.display_key])
            else:
                self.listbox.insert(tk.END, str(item))

    def position_dropdown(self):
        """Позиционирует выпадающий список под полем ввода"""
        try:
            # Получаем координаты родительского окна
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()

            # Получаем ширину поля ввода
            width = self.winfo_width()

            # Позиционируем окно
            self.dropdown_window.geometry(f"{width}x200+{x}+{y}")
            self.dropdown_window.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка позиционирования: {e}")

    def on_listbox_select(self, event):
        """Обрабатывает выбор элемента из списка"""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_value = self.listbox.get(index)
        results = self.search_function(selected_value)

        # Находим соответствующий элемент
        for item in results:
            if (isinstance(item, dict) and item[self.display_key] == selected_value) or str(item) == selected_value:
                self.selected_item = item
                break

        # Обновляем поле ввода
        if isinstance(item, dict) and self.display_key in item:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, item[self.display_key])

        self.dropdown_window.withdraw()

    def on_focus_in(self, event):
        """Обрабатывает событие получения фокуса"""
        self.entry.configure(border_color=("#1f6aa5", "#1f6aa5"))

    def on_focus_out(self, event):
        """Обрабатывает событие потери фокуса"""
        self.after(100, self.check_focus_out)

    def check_focus_out(self):
        """Проверяет, находится ли фокус вне виджета"""
        if not self.focus_get() and not self.dropdown_window.focus_get():
            self.dropdown_window.withdraw()

    def on_click_outside(self, event):
        """Обрабатывает клик вне списка"""
        if event.widget != self.listbox:
            self.dropdown_window.withdraw()

    def get(self):
        """Возвращает текущее значение"""
        return self.entry.get()

    def clear(self):
        """Очищает поле ввода и выбор"""
        self.entry.delete(0, tk.END)
        self.selected_item = None
        self.dropdown_window.withdraw()

    def set(self, value):
        """Устанавливает конкретное значение"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.selected_item = value
        self.dropdown_window.withdraw()