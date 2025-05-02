# File: app/ui/forms/contract_form.py (обновленный)
import tkinter as tk

from datetime import date
from typing import Optional, Callable, Dict, Any
import customtkinter as ctk

from app.core.models.contract import Contract
from app.ui.components.date_field import DateField
from app.ui.forms.base_form import BaseForm
from app.core.utils.form_validator import FormValidator


class ContractForm(BaseForm):
    def __init__(self, parent, contract: Optional[Contract] = None, on_save: Optional[Callable] = None):
        self.contract = contract or Contract("", date.today(), date(date.today().year, 12, 31))
        super().__init__(parent, title="Контракт", width=500, height=400, on_save=on_save)

    def _setup_ui(self) -> None:
        super()._setup_ui()
        self._setup_form_fields()
        self._load_data()

    def _setup_form_fields(self) -> None:
        # Шифр контракта
        row1 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row1, text="Шифр контракта:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["number"] = ctk.CTkEntry(row1, width=200)
        self.entry_fields["number"].pack(side=tk.LEFT)

        # Дата начала
        row2 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 15))
        self.start_date_field = self._setup_date_field(row2, "Действует с:", self.contract.start_date)

        # Дата окончания
        row3 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row3.pack(fill=tk.X, pady=(0, 20))
        self.end_date_field = self._setup_date_field(row3, "Действует до:", self.contract.end_date)

        # Описание
        row4 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row4.pack(fill=tk.X, pady=(0, 20))
        ctk.CTkLabel(row4, text="Описание:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["description"] = ctk.CTkTextbox(row4, height=100, width=300)
        self.entry_fields["description"].pack(side=tk.LEFT)

    def _setup_date_field(self, parent, label_text: str, default_date: date) -> DateField:
        """Создает и настраивает поле даты."""
        return self._setup_date_field(parent, label_text, default_date)

    def _load_data(self) -> None:
        """Загружает данные в поля формы."""
        self.entry_fields["number"].insert(0, self.contract.contract_number)
        self.start_date_field.set_date(self.contract.start_date or date.today())
        self.end_date_field.set_date(self.contract.end_date or date(date.today().year, 12, 31))

        if self.contract.description:
            self.entry_fields["description"].insert("1.0", self.contract.description)

    def _get_form_data(self) -> Dict[str, Any]:
        """Получает данные из формы."""
        return {
            "contract_number": self.entry_fields["number"].get().strip(),
            "start_date": self.start_date_field.get_date(),
            "end_date": self.end_date_field.get_date(),
            "description": self.entry_fields["description"].get("1.0", "end").strip()
        }

    def _validate_form_fields(self) -> bool:
        """Проверяет обязательные поля формы."""
        validators = [
            FormValidator.required("Шифр контракта", self.entry_fields["number"].get()),
            self._validate_date(self.start_date_field, "Дата начала"),
            self._validate_date(self.end_date_field, "Дата окончания"),
            self._validate_date_range(self.start_date_field, self.end_date_field)
        ]

        return FormValidator.validate_all(validators)