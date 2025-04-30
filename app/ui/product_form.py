"""
File: app/ui/product_form.py
Форма для добавления/редактирования изделий.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from app.core.models.product import Product
from app.core.services.product_service import ProductService
from app.ui.base_form import BaseForm
from app.config import UI_SETTINGS


class ProductForm(BaseForm):
    """
    Форма для добавления и редактирования изделий.
    """

    def __init__(
            self,
            parent: tk.Widget,
            product_service: ProductService,
            product: Product = None,
            on_save: callable = None
    ):
        """
        Инициализация формы изделия.

        Args:
            parent: Родительский виджет
            product_service: Сервис для работы с изделиями
            product: Модель изделия для редактирования
            on_save: Callback-функция после сохранения
        """
        super().__init__(parent)
        self.product_service = product_service
        self.product = product or Product()
        self.on_save = on_save
        self.entry_fields = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        """Настройка интерфейса формы."""
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 1-я строка: Шифр изделия
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row1, text="Шифр изделия:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["code"] = ctk.CTkEntry(row1, placeholder_text="Введите шифр...")
        self.entry_fields["code"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2-я строка: Название изделия
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 20))
        ctk.CTkLabel(row2, text="Наименование:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["name"] = ctk.CTkEntry(row2, placeholder_text="Введите наименование...")
        self.entry_fields["name"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки действий
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            action_frame,
            text="Сохранить",
            command=self._save_product,
            **UI_SETTINGS['button_style']
        )
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_button = ctk.CTkButton(
            action_frame,
            text="Отмена",
            command=self._on_cancel,
            fg_color="#9E9E9E",
            hover_color="#757575",
            **UI_SETTINGS['button_style']
        )
        cancel_button.pack(side=tk.RIGHT)

        # Привязываем событие Enter к кнопке "Сохранить"
        self.bind("<Return>", lambda event: self._save_product())
        self.bind("<KP_Enter>", lambda event: self._save_product())

        # Загружаем данные в форму
        self._load_data()

    def _load_data(self) -> None:
        """Загружает данные в поля формы."""
        self.entry_fields["code"].insert(0, self.product.product_code)
        self.entry_fields["name"].insert(0, self.product.name)

    def _save_product(self) -> None:
        """Обработчик события сохранения изделия."""
        try:
            # Получаем данные из формы
            code = self.entry_fields["code"].get().strip()
            name = self.entry_fields["name"].get().strip()

            # Проверяем уникальность шифра
            if self.product_service.exists(code, self.product.id if self.product.id else None):
                raise ValueError("Изделие с таким шифром уже существует")

            # Обновляем модель
            self.product.product_code = code
            self.product.name = name

            # Валидируем данные
            if not self.product.validate():
                return

            # Сохраняем в базу данных
            if self.product.id:
                success, message = self.product_service.update(self.product)
            else:
                success, product_id = self.product_service.create(self.product)
                if success:
                    self.product.id = product_id

            if success:
                self.show_success_message()
                if self.on_save:
                    self.on_save()
                self._on_cancel()
            else:
                self.show_error_message(message or "Не удалось сохранить изделие")

        except Exception as e:
            self.show_error_message(str(e))

    def _on_cancel(self) -> None:
        """Обработчик события отмены."""
        self.clear()
        self.parent.destroy()

    def clear(self) -> None:
        """Очищает поля формы."""
        for field in self.entry_fields.values():
            field.delete(0, tk.END)