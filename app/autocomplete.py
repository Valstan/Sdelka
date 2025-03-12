"""
Компонент выпадающего списка с автодополнением.
Поддерживает поиск в реальном времени и отображение результатов.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import List, Dict, Any, Callable

class AutocompleteCombobox:
    def __init__(self, parent, search_function, display_key='name', value_key=None, command=None, width=200):
        """
        Инициализация выпадающего списка с автозаполнением.

        Args:
            parent: Родительский виджет
            search_function: Функция поиска данных
            display_key: Ключ для отображения значений
            value_key: Ключ для значения (по умолчанию совпадает с display_key)
            command: Функция, вызываемая при выборе элемента
            width: Ширина виджета
        """
        self.parent = parent
        self.search_function = search_function
        self.display_key = display_key
        self.value_key = value_key if value_key else display_key
        self.command = command
        self.selected_item = None
        self.items_data = {}
        self.width = width

        # Основной фрейм компонента
        self.frame = tk.Frame(parent)

        # Строка ввода
        self.entry = ctk.CTkEntry(self.frame, width=width)
        self.entry.pack(fill="x", expand=True)

        # Выпадающий список
        self.dropdown = tk.Toplevel(parent)
        self.dropdown.withdraw()  # Скрываем до первого использования
        self.dropdown.overrideredirect(True)  # Убираем рамку окна

        # Настройка стиля для выпадающего списка
        self.dropdown.configure(bg='#F5F5F5')

        # Список для отображения результатов
        self.listbox = tk.Listbox(self.dropdown, bg='#F5F5F5', fg="black", highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=2, pady=2)

        # Привязка событий
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        self.entry.bind("<Down>", self.focus_listbox)
        self.listbox.bind("<Double-Button-1>", self.on_select)
        self.listbox.bind("<Return>", self.on_select)
        self.listbox.bind("<Escape>", self.hide_dropdown)

        # Перемещение по списку с помощью клавиш вверх/вниз
        self.entry.bind("<Up>", lambda event: self.move_selection(-1))
        self.entry.bind("<Down>", lambda event: self.move_selection(1))

        # Отслеживание закрытия родительского окна
        parent.bind("<Destroy>", self.on_parent_destroy)

    def pack(self, **kwargs):
        """Метод для упаковки виджета"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Метод для размещения виджета в сетке"""
        self.frame.grid(**kwargs)

    def place(self, **kwargs):
        """Метод для размещения виджета на конкретной позиции"""
        self.frame.place(**kwargs)

    def on_key_release(self, event):
        """Обработчик события释放键盘键"""
        # Игнорируем специальные клавиши
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return

        search_text = self.entry.get().strip()
        if len(search_text) >= 2:
            self.show_options(search_text)
        else:
            self.hide_dropdown()

    def on_focus_out(self, event):
        """Обработчик потери фокуса"""
        # Проверяем, не является ли новое активное окно частью нашего приложения
        if self.dropdown.winfo_exists() and self.dropdown.focus_get() is None:
            self.hide_dropdown()

    def focus_listbox(self, event):
        """Перемещение фокуса на список"""
        if self.dropdown.winfo_ismapped():
            self.listbox.focus_set()

    def move_selection(self, direction):
        """Перемещение выделения в списке"""
        if not self.dropdown.winfo_ismapped():
            return

        current_selection = self.listbox.curselection()
        if not current_selection:
            self.listbox.selection_set(0)
            return

        current_index = current_selection[0]
        new_index = current_index + direction

        if 0 <= new_index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(new_index)
            self.listbox.activate(new_index)

    def show_options(self, search_text):
        """Показать список с результатами поиска"""
        # Получаем результаты поиска
        items = self.search_function(search_text)
        if not items:
            self.hide_dropdown()
            return

        # Обновляем данные и отображаем dropdown
        self.items_data = {getattr(item, self.display_key): item for item in items}

        # Очищаем список
        self.listbox.delete(0, tk.END)

        # Добавляем найденные элементы
        for item in items:
            self.listbox.insert(tk.END, getattr(item, self.display_key))

        # Позиционируем dropdown под полем ввода
        self.position_dropdown()

        # Показываем dropdown
        self.dropdown.deiconify()

    def position_dropdown(self):
        """Позиционирование dropdown под полем ввода"""
        self.dropdown.withdraw()  # Сначала скрываем, чтобы получить правильные размеры после обновления
        self.dropdown.update_idletasks()  # Обновляем размеры

        # Получаем позицию и размеры поля ввода
        entry_x = self.entry.winfo_rootx()
        entry_y = self.entry.winfo_rooty() + self.entry.winfo_height()
        entry_width = self.entry.winfo_width()

        # Устанавливаем позицию dropdown
        self.dropdown.geometry(f"+{entry_x}+{entry_y}")

        # Ограничиваем ширину dropdown шириной поля ввода
        if self.dropdown.winfo_reqwidth() < entry_width:
            self.dropdown.geometry(f"{entry_width}x{self.dropdown.winfo_reqheight()}")

        # Показываем dropdown
        self.dropdown.deiconify()

    def hide_dropdown(self, event=None):
        """Скрыть dropdown"""
        self.dropdown.withdraw()

    def on_select(self, event):
        """Обработчик выбора элемента из списка"""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        display_value = self.listbox.get(index)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, display_value)

        # Сохраняем выбранный элемент
        self.selected_item = self.items_data.get(display_value)

        # Вызываем callback функцию, если она задана
        if self.command and self.selected_item:
            self.command(self.selected_item)

        self.hide_dropdown()

    def on_parent_destroy(self, event):
        """Обработчик закрытия родительского окна"""
        if self.dropdown.winfo_exists():
            self.dropdown.destroy()

    def get_selected_item(self):
        """Возвращает выбранный элемент"""
        return self.selected_item

    def set_text(self, text):
        """Устанавливает текст в поле ввода"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def clear(self):
        """Очищает поле ввода и сбрасывает выбор"""
        self.entry.delete(0, tk.END)
        self.selected_item = None
