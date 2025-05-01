# File: app/ui/components/items_table.py
"""
Таблица для отображения элементов работы.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ItemsTable(ctk.CTkFrame):
    """
    Таблица элементов работы.

    Attributes:
        parent: Родительский виджет
        card_service: Сервис карточек работ
        items_container: Контейнер для элементов
        items: Список элементов
        on_update: Callback при обновлении
    """

    def __init__(
            self,
            parent: ctk.CTkFrame,
            card_service: 'WorkCardsService',
            *args,
            **kwargs
    ):
        """
        Инициализирует таблицу элементов работы.

        Args:
            parent: Родительский виджет
            card_service: Сервис карточек работ
            args: Дополнительные аргументы
            kwargs: Дополнительные ключевые аргументы
        """
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.card_service = card_service
        self.items_container = ctk.CTkFrame(self)
        self.items = []

    def set_card(self, card: Dict[str, Any]) -> None:
        """
        Устанавливает карточку для редактирования.

        Args:
            card: Карточка работы
        """
        self.card = card
        self.items = card.get("items", [])

        self._clear_table()
        self._update_table()

    def _clear_table(self) -> None:
        """
        Очищает таблицу от текущих элементов.
        """
        for widget in self.winfo_children():
            if hasattr(widget, "is_item_row") or hasattr(widget, "is_add_button"):
                continue
            widget.destroy()

    def _update_table(self) -> None:
        """
        Обновляет таблицу данными из текущей карточки.
        """
        if not self.items:
            return

        for idx, item in enumerate(self.items):
            item_frame = ctk.CTkFrame(self.items_container)
            self._create_item_row(item_frame, item, idx)
            item_frame.pack(fill=tk.X, pady=(0, 5))

        self.items_container.pack(fill=tk.BOTH, expand=True)

    def _create_item_row(self, parent: ctk.CTkFrame, item: Dict[str, Any], index: int) -> None:
        """
        Создает строку элемента работы.

        Args:
            parent: Родительский виджет
            item: Элемент работы
            index: Индекс элемента
        """
        parent.is_item_row = True

        # Наименование работы
        name_label = ctk.CTkLabel(parent, text=item.get("work_type_name", ""), width=200)
        name_label.grid(row=0, column=0, padx=5)

        # Количество
        quantity_entry = ctk.CTkEntry(parent, width=100)
        quantity_entry.grid(row=0, column=1, padx=5)
        quantity_entry.insert(0, str(item.get("quantity", "")))

        # Сумма
        amount_entry = ctk.CTkEntry(parent, width=100)
        amount_entry.grid(row=0, column=2, padx=5)
        amount_entry.insert(0, f"{item.get('amount', 0):.2f}")
        amount_entry.configure(state="readonly")

        # Кнопка удаления
        delete_btn = ctk.CTkButton(
            parent,
            text="Удалить",
            width=80,
            fg_color="#C62828",
            hover_color="#B71C1C",
            command=lambda: self._remove_item(parent)
        )
        delete_btn.grid(row=0, column=3, padx=5)

    def add_item(self, item: Dict[str, Any]) -> None:
        """
        Добавляет новый элемент работы.

        Args:
            item: Новый элемент работы
        """
        self.items.append(item)
        self._clear_table()
        self._update_table()

    def _remove_item(self, parent: ctk.CTkFrame) -> None:
        """
        Удаляет элемент работы.

        Args:
            parent: Родительский виджет элемента
        """
        if not messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот элемент?"):
            return

        for child in parent.winfo_children():
            if hasattr(child, "grid_info"):
                grid_info = child.grid_info()
                if grid_info.get("column") == 0:
                    # Здесь должна быть реализация удаления элемента
                    pass

        self._clear_table()
        self._update_table()