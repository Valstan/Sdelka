# File: app/ui/forms/work_type_form.py

import tkinter as tk
from datetime import date
from typing import Optional, Callable, Dict, Any

import customtkinter as ctk

from app.core.models.work_type import WorkType
from app.utils.form_validator import FormValidator
from app.ui.forms.base_form import BaseForm

class WorkTypeForm(BaseForm):
    def __init__(self, parent, work_type: Optional[WorkType] = None, on_save: Optional[Callable] = None):
        self.work_type = work_type or WorkType("", "штуки", 0.0, date.today())
        super().__init__(parent, title="Вид работы", width=400, height=300, on_save=on_save)

    def _setup_ui(self) -> None:
        super()._setup_ui()
        self._setup_form_fields()
        self._load_data()

    def _setup_form_fields(self) -> None:
        # Название
        row1 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row1, text="Название:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["name"] = ctk.CTkEntry(row1, width=200)
        self.entry_fields["name"].pack(side=tk.LEFT)

        # Единица измерения
        row2 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row2, text="Единица измерения:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["unit"] = ctk.CTkComboBox(row2, values=["штуки", "комплекты"], width=150)
        self.entry_fields["unit"].pack(side=tk.LEFT)

        # Цена
        row3 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row3.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row3, text="Цена:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["price"] = ctk.CTkEntry(row3, width=100)
        self.entry_fields["price"].pack(side=tk.LEFT)

        # Дата действия
        row4 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row4.pack(fill=tk.X, pady=(0, 15))
        self.valid_from_field = self._setup_date_field(row4, "Действует с:", self.work_type.valid_from)

    def _load_data(self) -> None:
        """Загружает данные в поля формы."""
        self.entry_fields["name"].insert(0, self.work_type.name)
        self.entry_fields["unit"].set(self.work_type.unit)
        self.entry_fields["price"].insert(0, f"{self.work_type.price:.2f}")
        self.valid_from_field.set_date(self.work_type.valid_from or date.today())

    def _get_form_data(self) -> Dict[str, Any]:
        """Получает данные из формы."""
        return {
            "name": self.entry_fields["name"].get().strip(),
            "unit": self.entry_fields["unit"].get(),
            "price": float(self.entry_fields["price"].get()),
            "valid_from": self.valid_from_field.get_date()
        }

    def _validate_form_fields(self) -> bool:
        """Проверяет обязательные поля формы."""
        validators = [
            FormValidator.required("Название", self.entry_fields["name"].get()),
            FormValidator.numeric_positive("Цена", self.entry_fields["price"].get()),
            self._validate_date(self.valid_from_field, "Дата действия")
        ]

        return FormValidator.validate_all(validators)