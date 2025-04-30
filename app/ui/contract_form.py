"""
File: app/ui/contract_form.py
Форма для добавления/редактирования контрактов.
"""

import tkinter as tk
from datetime import date
from tkinter import ttk
import customtkinter as ctk
from app.core.models.contract import Contract
from app.core.services.contract_service import ContractService
from app.ui.base_form import BaseForm
from app.config import UI_SETTINGS


class ContractForm(BaseForm):
    """
    Форма для добавления и редактирования контрактов.
    """

    def __init__(
            self,
            parent: tk.Widget,
            contract_service: ContractService,
            contract: Contract = None,
            on_save: callable = None
    ):
        """
        Инициализация формы контракта.

        Args:
            parent: Родительский виджет
            contract_service: Сервис для работы с контрактами
            contract: Модель контракта для редактирования
            on_save: Callback-функция после сохранения
        """
        super().__init__(parent)
        self.contract_service = contract_service
        self.contract = contract or Contract()
        self.on_save = on_save
        self.entry_fields = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        """Настройка интерфейса формы."""
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 1-я строка: Шифр контракта
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row1, text="Шифр контракта:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["number"] = ctk.CTkEntry(row1, placeholder_text="Введите шифр...")
        self.entry_fields["number"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2-я строка: Дата начала
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row2, text="Дата начала:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        date_frame_start = ctk.CTkFrame(row2, fg_color="transparent")
        date_frame_start.pack(side=tk.LEFT)

        self.entry_fields["start_day"] = ctk.CTkComboBox(date_frame_start, width=60,
                                                         values=[f"{i:02d}" for i in range(1, 32)])
        self.entry_fields["start_day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["start_month"] = ctk.CTkComboBox(date_frame_start, width=60,
                                                           values=[f"{i:02d}" for i in range(1, 13)])
        self.entry_fields["start_month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["start_year"] = ctk.CTkComboBox(date_frame_start, width=80,
                                                          values=[str(i) for i in range(2000, 2051)])
        self.entry_fields["start_year"].pack(side=tk.LEFT)

        # 3-я строка: Дата окончания
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill=tk.X, pady=(0, 15))
        ctk.CTkLabel(row3, text="Дата окончания:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))

        date_frame_end = ctk.CTkFrame(row3, fg_color="transparent")
        date_frame_end.pack(side=tk.LEFT)

        self.entry_fields["end_day"] = ctk.CTkComboBox(date_frame_end, width=60,
                                                       values=[f"{i:02d}" for i in range(1, 32)])
        self.entry_fields["end_day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["end_month"] = ctk.CTkComboBox(date_frame_end, width=60,
                                                         values=[f"{i:02d}" for i in range(1, 13)])
        self.entry_fields["end_month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["end_year"] = ctk.CTkComboBox(date_frame_end, width=80,
                                                        values=[str(i) for i in range(2000, 2051)])
        self.entry_fields["end_year"].pack(side=tk.LEFT)

        # 4-я строка: Описание
        row4 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row4.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        ctk.CTkLabel(row4, text="Описание:", **UI_SETTINGS['label_style']).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["description"] = ctk.CTkTextbox(row4, height=100)
        self.entry_fields["description"].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Кнопки действий
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            action_frame,
            text="Сохранить",
            command=self._save_contract,
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
        self.bind("<Return>", lambda event: self._save_contract())
        self.bind("<KP_Enter>", lambda event: self._save_contract())

        # Загружаем данные в форму
        self._load_data()

    def _load_data(self) -> None:
        """Загружает данные в поля формы."""
        self.entry_fields["number"].insert(0, self.contract.contract_number)

        # Устанавливаем дату начала
        start_date = self.contract.start_date or date.today()
        self.entry_fields["start_day"].set(f"{start_date.day:02d}")
        self.entry_fields["start_month"].set(f"{start_date.month:02d}")
        self.entry_fields["start_year"].set(str(start_date.year))

        # Устанавливаем дату окончания
        end_date = self.contract.end_date or date(date.today().year, 12, 31)
        self.entry_fields["end_day"].set(f"{end_date.day:02d}")
        self.entry_fields["end_month"].set(f"{end_date.month:02d}")
        self.entry_fields["end_year"].set(str(end_date.year))

        # Устанавливаем описание
        if self.contract.description:
            self.entry_fields["description"].insert("1.0", self.contract.description)

    def _save_contract(self) -> None:
        """Обработчик события сохранения контракта."""
        try:
            # Получаем данные из формы
            number = self.entry_fields["number"].get().strip()

            # Парсим даты
            try:
                start_day = int(self.entry_fields["start_day"].get())
                start_month = int(self.entry_fields["start_month"].get())
                start_year = int(self.entry_fields["start_year"].get())
                start_date = date(start_year, start_month, start_day)

                end_day = int(self.entry_fields["end_day"].get())
                end_month = int(self.entry_fields["end_month"].get())
                end_year = int(self.entry_fields["end_year"].get())
                end_date = date(end_year, end_month, end_day)

                if start_date > end_date:
                    raise ValueError("Дата начала не может быть позже даты окончания")
            except ValueError as ve:
                raise ValueError(f"Некорректная дата: {ve}")

            description = self.entry_fields["description"].get("1.0", "end").strip()

            # Проверяем уникальность номера
            if self.contract_service.exists(number, self.contract.id if self.contract.id else None):
                raise ValueError("Контракт с таким шифром уже существует")

            # Обновляем модель
            self.contract.contract_number = number
            self.contract.start_date = start_date
            self.contract.end_date = end_date
            self.contract.description = description

            # Валидируем данные
            if not self.contract.validate():
                return

            # Сохраняем в базу данных
            if self.contract.id:
                success, message = self.contract_service.update(self.contract)
            else:
                success, contract_id = self.contract_service.create(self.contract)
                if success:
                    self.contract.id = contract_id

            if success:
                self.show_success_message()
                if self.on_save:
                    self.on_save()
                self._on_cancel()
            else:
                self.show_error_message(message or "Не удалось сохранить контракт")

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
            elif isinstance(field, ctk.CTkTextbox):
                field.delete("1.0", tk.END)
            elif isinstance(field, ctk.CTkComboBox):
                field.set("")