"""
Компонент выпадающего списка с автодополнением.
Поддерживает поиск в реальном времени и отображение результатов.
"""
import tkinter as tk


class AutocompleteCombobox:
    def __init__(self, parent, search_function, display_key='name', value_key=None, command=None, width=200):
        self.parent = parent
        self.search_function = search_function
        self.display_key = display_key
        self.value_key = value_key if value_key else display_key
        self.command = command
        self.selected_item = None
        self.items_data = {}
        self.width = width

        # Основной фрейм
        self.frame = tk.Frame(parent)

        # Создаем виджет Entry
        self.entry = tk.Entry(self.frame, width=width // 7)  # Ширина в символах примерно
        self.entry.pack(fill="x", expand=True)

        # Создаем выпадающий список как Toplevel окно
        self.dropdown = tk.Toplevel(parent)
        self.dropdown.withdraw()  # Скрываем
        self.dropdown.overrideredirect(True)  # Без рамки окна

        # Важно: запрещаем изменение размера окна пользователем
        self.dropdown.resizable(False, False)

        # Создаем скроллер и listbox в выпадающем списке
        self.listbox_frame = tk.Frame(self.dropdown)
        self.listbox_frame.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical")
        self.listbox = tk.Listbox(
            self.listbox_frame,
            yscrollcommand=self.scrollbar.set,
            selectbackground="#a6a6a6",
            exportselection=False,
            width=30  # ширина в символах
        )
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # Привязываем события
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<FocusIn>", self.show_options)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        self.entry.bind("<Down>", self.focus_listbox)

        # Привязываем события к выпадающему списку
        self.listbox.bind("<Return>", self.on_select)
        self.listbox.bind("<Escape>", self.hide_dropdown)

        # Отслеживаем закрытие родительского окна
        parent.bind("<Destroy>", self._on_parent_destroy, add="+")

        # Отслеживаем изменение размера родительского окна
        parent.bind("<Configure>", self._on_parent_configure, add="+")

    def _on_parent_destroy(self, event):
        """Обработчик закрытия родительского окна"""
        if self.dropdown.winfo_exists():
            self.dropdown.destroy()

    def _on_parent_configure(self, event):
        """Обработчик изменения размера родительского окна"""
        if self.dropdown.winfo_ismapped():
            self.update_dropdown_position()

    def pack(self, **kwargs):
        return self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        return self.frame.grid(**kwargs)

    def place(self, **kwargs):
        return self.frame.place(**kwargs)

    def on_key_release(self, event):
        """Обработчик события отпускания клавиши"""
        # Игнорируем специальные клавиши
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return

        # Обновляем список опций
        self.show_options()

    def on_focus_out(self, event):
        """Обработчик потери фокуса полем ввода"""
        # Даем немного времени, чтобы проверить, получил ли listbox фокус
        self.frame.after(100, self._check_focus)

    def _check_focus(self):
        """Проверяет, находится ли фокус на выпадающем списке"""
        try:
            # Если фокус не на listbox и не на родительском элементе entry, скрываем выпадающий список
            focused = self.parent.focus_get()
            if focused != self.listbox and focused != self.entry:
                self.hide_dropdown()
        except tk.TclError:  # Может возникнуть, если окно уже закрыто
            pass

    def update_dropdown_position(self):
        """Обновляет позицию выпадающего списка относительно поля ввода"""
        if not self.dropdown.winfo_ismapped():
            return

        try:
            # Получаем координаты и размеры entry виджета
            entry_x = self.entry.winfo_rootx()
            entry_y = self.entry.winfo_rooty()
            entry_height = self.entry.winfo_height()
            entry_width = self.entry.winfo_width()

            # Получаем размеры экрана для проверки границ
            screen_width = self.parent.winfo_screenwidth()
            screen_height = self.parent.winfo_screenheight()

            # Рассчитываем оптимальную ширину и позицию dropdown
            dropdown_width = min(entry_width, 300)  # Ограничиваем максимальную ширину

            # Проверяем, достаточно ли места внизу экрана
            dropdown_height = min(self.listbox.size() * 20, 200)  # 20px на элемент, максимум 200px

            # Расчитываем позицию выпадающего списка
            dropdown_x = entry_x
            dropdown_y = entry_y + entry_height

            # Проверка, чтобы список не выходил за пределы экрана по горизонтали
            if dropdown_x + dropdown_width > screen_width:
                dropdown_x = screen_width - dropdown_width

            # Проверка, чтобы список не выходил за пределы экрана по вертикали
            if dropdown_y + dropdown_height > screen_height:
                dropdown_y = entry_y - dropdown_height  # Показываем выше поля ввода

            # Устанавливаем геометрию выпадающего списка
            self.dropdown.geometry(f"{dropdown_width}x{dropdown_height}+{dropdown_x}+{dropdown_y}")

        except Exception as e:
            print(f"Error updating dropdown position: {str(e)}")

    def show_options(self, event=None):
        """Показывает выпадающий список с опциями"""
        # Обновляем список опций
        self.update_options()

        # Если нет элементов, не показываем выпадающий список
        if self.listbox.size() == 0:
            self.hide_dropdown()
            return

        # Обновляем позицию выпадающего списка
        self.update_dropdown_position()

        # Показываем выпадающий список поверх других окон
        self.dropdown.deiconify()
        self.dropdown.lift()
        self.dropdown.attributes('-topmost', True)  # Поверх всех окон

    def hide_dropdown(self, event=None):
        """Скрывает выпадающий список"""
        self.dropdown.withdraw()
        # Снимаем флаг topmost, чтобы не блокировать другие окна
        self.dropdown.attributes('-topmost', False)

    def update_options(self):
        """Обновляет список опций на основе текущего текста"""
        # Очищаем текущие опции
        self.listbox.delete(0, tk.END)
        self.items_data = {}

        # Получаем текущий текст для поиска
        search_text = self.entry.get().strip()

        try:
            # Выполняем поиск
            items = self.search_function(search_text)

            # Добавляем найденные элементы в выпадающий список
            for i, item in enumerate(items):
                display_text = item.get(self.display_key, "")
                self.listbox.insert(tk.END, display_text)
                self.items_data[i] = item
        except Exception as e:
            print(f"Error updating options: {str(e)}")

    def focus_listbox(self, event=None):
        """Перемещает фокус на выпадающий список"""
        if not self.dropdown.winfo_ismapped():
            self.show_options()

        if self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_set(0)

        return "break"  # Останавливаем дальнейшую обработку события

    def on_select(self, event=None):
        """Обработчик выбора элемента из списка"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            # Получаем выбранный элемент
            self.selected_item = self.items_data.get(index)
            # Устанавливаем текст в поле ввода
            display_text = self.selected_item.get(self.display_key, "")
            self.entry.delete(0, tk.END)
            self.entry.insert(0, display_text)
            # Скрываем выпадающий список
            self.hide_dropdown()
            # Вызываем функцию обратного вызова, если она указана
            if self.command:
                self.command(self.selected_item)

        return "break"  # Останавливаем дальнейшую обработку события

    def get_selected_value(self):
        """Возвращает значение выбранного элемента"""
        if self.selected_item:
            return self.selected_item.get(self.value_key)
        return None

    def get_selected_item(self):
        """Возвращает выбранный элемент целиком"""
        return self.selected_item

    def set_text(self, text):
        """Устанавливает текст в поле ввода"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def clear(self):
        """Очищает выбор и текст в поле ввода"""
        self.entry.delete(0, tk.END)
        self.selected_item = None
