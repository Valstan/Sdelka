# File: app/ui/worker_form.py
"""
Форма для управления информацией о работнике.
"""

import tkinter as tk
import customtkinter as ctk
from app.ui.base_form import BaseForm
from app.core.models.models import Worker
from app.core.services.worker_service import WorkerService


class WorkerForm(BaseForm):
    """
    Форма для добавления и редактирования информации о работнике

    Attributes:
        worker_id: ID текущего работника (если редактирование)
        entry_fields: Словарь полей ввода формы
    """

    def __init__(self, parent, worker_service: WorkerService, worker_id: int = None, *args, **kwargs):
        """
        Инициализация формы работника

        Args:
            parent: Родительский виджет
            worker_service: Сервис для работы с работниками
            worker_id: ID работника для редактирования (если есть)
            args: Дополнительные аргументы
            kwargs: Дополнительные ключевые аргументы
        """
        self.worker_id = worker_id
        self.worker_service = worker_service
        self.entry_fields = {}
        super().__init__(parent, worker_service, *args, **kwargs)

        if worker_id:
            self.load_worker_data(worker_id)

    def setup_ui(self):
        """Настройка пользовательского интерфейса формы работника"""
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Первая строка: ФИО
        row1 = ctk.CTkFrame(form_frame)
        row1.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row1, text="Фамилия:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["last_name"] = ctk.CTkEntry(row1)
        self.entry_fields["last_name"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ctk.CTkLabel(row1, text="Имя:", width=40).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["first_name"] = ctk.CTkEntry(row1)
        self.entry_fields["first_name"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ctk.CTkLabel(row1, text="Отчество:", width=60).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["middle_name"] = ctk.CTkEntry(row1)
        self.entry_fields["middle_name"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Вторая строка: Информация о цехе и должности
        row2 = ctk.CTkFrame(form_frame)
        row2.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row2, text="Цех:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["workshop_number"] = ctk.CTkEntry(row2)
        self.entry_fields["workshop_number"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ctk.CTkLabel(row2, text="Должность:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["position"] = ctk.CTkEntry(row2)
        self.entry_fields["position"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Третья строка: Табельный номер
        row3 = ctk.CTkFrame(form_frame)
        row3.pack(fill=tk.X, pady=(0, 20))

        ctk.CTkLabel(row3, text="Табельный номер:", width=120).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["employee_id"] = ctk.CTkEntry(row3)
        self.entry_fields["employee_id"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=self.save,
            width=120
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=self.parent.destroy,
            width=120,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Привязываем событие Enter к кнопке сохранить
        self.bind_save_event(save_btn, self.save)

    def clear(self):
        """Очищает поля формы"""
        for field in self.entry_fields.values():
            field.delete(0, tk.END)

    def get_form_data(self) -> dict:
        """
        Получает данные из формы

        Returns:
            Словарь с данными формы
        """
        return {
            "last_name": self.entry_fields["last_name"].get().strip(),
            "first_name": self.entry_fields["first_name"].get().strip(),
            "middle_name": self.entry_fields["middle_name"].get().strip(),
            "workshop_number": self.entry_fields["workshop_number"].get().strip(),
            "position": self.entry_fields["position"].get().strip(),
            "employee_id": self.entry_fields["employee_id"].get().strip()
        }

    def validate(self) -> bool:
        """
        Проверяет корректность введенных данных

        Returns:
            True если данные корректны, False в противном случае
        """
        data = self.get_form_data()

        if not data["last_name"]:
            self.show_error_message("Введите фамилию работника")
            return False

        if not data["first_name"]:
            self.show_error_message("Введите имя работника")
            return False

        if not data["employee_id"]:
            self.show_error_message("Введите табельный номер работника")
            return False

        # Проверяем уникальность табельного номера (если это новый работник или измененный)
        worker = self.worker_service.get_worker_by_employee_id(data["employee_id"])
        if worker:
            if not self.worker_id or worker.id != self.worker_id:
                self.show_error_message("Работник с таким табельным номером уже существует")
                return False

        return True

    def save(self) -> tuple:
        """
        Сохраняет данные работника

        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        if not self.validate():
            return False, "Некорректные данные формы"

        data = self.get_form_data()

        if self.worker_id:
            # Обновление существующего работника
            worker = self.worker_service.get_worker_by_id(self.worker_id)
            for key, value in data.items():
                setattr(worker, key, value)
            return self.worker_service.update_worker(worker)
        else:
            # Создание нового работника
            worker = Worker(**data)
            return self.worker_service.add_worker(worker)

    def load_worker_data(self, worker_id: int):
        """
        Загружает данные работника для редактирования

        Args:
            worker_id: ID работника
        """
        worker = self.worker_service.get_worker_by_id(worker_id)
        if not worker:
            self.show_error_message("Не удалось загрузить данные работника")
            return

        self.entry_fields["last_name"].insert(0, worker.last_name)
        self.entry_fields["first_name"].insert(0, worker.first_name)
        if worker.middle_name:
            self.entry_fields["middle_name"].insert(0, worker.middle_name)
        if worker.workshop_number:
            self.entry_fields["workshop_number"].insert(0, worker.workshop_number)
        if worker.position:
            self.entry_fields["position"].insert(0, worker.position)
        if worker.employee_id:
            self.entry_fields["employee_id"].insert(0, worker.employee_id)