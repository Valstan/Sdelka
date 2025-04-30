"""
File: app/ui/work_type_form.py
Форма для добавления/редактирования видов работ.
"""

import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
import customtkinter as ctk
from app.core.models.work_type import WorkType
from app.core.services.work_type_service import WorkTypeService
from app.ui.base_form import BaseForm
from app.config import UI_SETTINGS


class WorkTypeForm(BaseForm):
    """
    Форма для добавления и редактирования видов работ.
    """

    def __init__(
            self,
            parent: tk.Widget,
            work_type_service: WorkTypeService,
            work_type: WorkType = None,
            on_save: callable = None
    ):
        """
        Инициализация формы вида работы.

        Args:
            parent: Родительский виджет
            work_type_service: Сервис для работы с видами работ
            work_type: Модель вида работы для редактирования
            on_save: Callback-функция после сохранения
        """
        super().__init__(parent)
        self.work_type_service = work_type_service
        self.work_type = work_type or WorkType()
        self.on_save = on_save
        self.entry_fields = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        """Настройка интерфейса формы."""
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 1-я строка: Название работы
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row1, text="Название работы:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["name"] = ctk.CTkEntry(row1, placeholder_text="Введите название...")
        self.entry_fields["name"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2-я строка: Единица измерения
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row2, text="Единица измерения:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["unit"] = ctk.CTkComboBox(row2, values=["штуки", "комплекты"])
        self.entry_fields["unit"].pack(side=tk.LEFT)

        # 3-я строка: Цена
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row3, text="Цена (руб):", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["price"] = ctk.CTkEntry(row3, placeholder_text="0.00")
        self.entry_fields["price"].pack(side=tk.LEFT)

        # 4-я строка: Дата начала действия
        row4 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row4.pack(fill=tk.X, pady=(0, 20))
        ctk.CTkLabel(row4, text="Действует с:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        date_frame = ctk.CTkFrame(row4, fg_color="transparent")
        date_frame.pack(side=tk.LEFT)

        self.entry_fields["day"] = ctk.CTkComboBox(date_frame, width=60, values=[f"{i:02d}" for i in range(1, 32)])
        self.entry_fields["day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["month"] = ctk.CTkComboBox(date_frame, width=60, values=[f"{i:02d}" for i in range(1, 13)])
        self.entry_fields["month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["year"] = ctk.CTkComboBox(date_frame, width=80, values=[str(i) for i in range(2000, 2051)])
        self.entry_fields["year"].pack(side=tk.LEFT)

        # Кнопки действий
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            action_frame,
            text="Сохранить",
            command=self._save_work_type,
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
        self.bind("<Return>", lambda event: self._save_work_type())
        self.bind("<KP_Enter>", lambda event: self._save_work_type())

        # Загружаем данные в форму
        self._load_data()

    def _load_data(self) -> None:
        """Загружает данные в поля формы."""
        self.entry_fields["name"].insert(0, self.work_type.name)
        self.entry_fields["unit"].set(self.work_type.unit)
        self.entry_fields["price"].insert(0, f"{self.work_type.price:.2f}")

        # Устанавливаем дату
        valid_from = self.work_type.valid_from or date.today()
        self.entry_fields["day"].set(f"{valid_from.day:02d}")
        self.entry_fields["month"].set(f"{valid_from.month:02d}")
        self.entry_fields["year"].set(str(valid_from.year))

    def _save_work_type(self) -> None:
        """Обработчик события сохранения вида работы."""
        try:
            # Получаем данные из формы
            name = self.entry_fields["name"].get().strip()
            unit = self.entry_fields["unit"].get()

            try:
                price = float(self.entry_fields["price"].get())
                if price < 0:
                    raise ValueError("Цена не может быть отрицательной")
            except ValueError:
                raise ValueError("Цена должна быть положительным числом")

            try:
                day = int(self.entry_fields["day"].get())
                month = int(self.entry_fields["month"].get())
                year = int(self.entry_fields["year"].get())
                valid_from = date(year, month, day)
            except ValueError:
                raise ValueError("Некорректная дата")

            # Проверяем уникальность названия
            if self.work_type_service.exists(name, self.work_type.id if self.work_type.id else None):
                raise ValueError("Вид работы с таким названием уже существует")

            # Обновляем модель
            self.work_type.name = name
            self.work_type.unit = unit
            self.work_type.price = price
            self.work_type.valid_from = valid_from

            # Валидируем данные
            if not self.work_type.validate():
                return

            # Сохраняем в базу данных
            if self.work_type.id:
                success, message = self.work_type_service.update(self.work_type)
            else:
                success, work_type_id = self.work_type_service.create(self.work_type)
                if success:
                    self.work_type.id = work_type_id

            if success:
                self.show_success_message()
                if self.on_save:
                    self.on_save()
                self._on_cancel()
            else:
                self.show_error_message(message or "Не удалось сохранить вид работы")

        except Exception as e:
            self.show_error_message(str(e))

    def _on_cancel(self) -> None:
        """Обработчик события отмены."""
        self.clear()
        self.parent.destroy()

    def clear(self) -> None:
        """Очищает поля формы."""
        for field in self.entry_fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, tk.END)
            elif isinstance(field, ctk.CTkComboBox):
                field.set("")