"""
Форма для управления информацией о работнике.
Разделена на UI и бизнес-логику, реализует валидацию через отдельные классы.
"""

import customtkinter as ctk
from typing import Optional, Callable
from app.core.services.worker_service import WorkerService
from app.utils.validators.validators import WorkerValidator
from app.utils.exceptions import ValidationError
from app.ui.forms.base_form import BaseForm


class WorkerForm(BaseForm):
    """
    Форма для добавления и редактирования информации о работнике
    """

    def __init__(
            self,
            parent,
            worker_service: WorkerService,
            worker_id: Optional[int] = None,
            on_save: Optional[Callable] = None,
            on_cancel: Optional[Callable] = None
    ):
        """
        Args:
            parent: Родительский виджет
            worker_service: Сервис для работы с работниками
            worker_id: ID работника для редактирования
            on_save: Callback-функция при успешном сохранении
            on_cancel: Callback-функция при отмене
        """
        super().__init__(parent)
        self.worker_id = worker_id
        self.worker_service = worker_service
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.validator = WorkerValidator()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка пользовательского интерфейса формы работника"""
        ctk.CTkLabel(self, text="ФИО:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.name_entry = ctk.CTkEntry(self, width=300)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(self, text="Табельный номер:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.tab_num_entry = ctk.CTkEntry(self)
        self.tab_num_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(self, text="Номер цеха:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.workshop_entry = ctk.CTkEntry(self)
        self.workshop_entry.grid(row=2, column=1, padx=10, pady=5)

        # Кнопки управления
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ctk.CTkButton(button_frame, text="Сохранить", command=self._save).pack(
            side="left", padx=10
        )
        ctk.CTkButton(
            button_frame, text="Отмена", command=self._handle_cancel, fg_color="gray"
        ).pack(side="left", padx=10)

        if self.worker_id:
            self._load_worker_data()

    def _load_worker_data(self) -> None:
        """Загружает данные работника для редактирования"""
        try:
            worker = self.worker_service.get_by_id(self.worker_id)
            if worker:
                self.name_entry.insert(0, f"{worker.last_name} {worker.first_name} {worker.middle_name}")
                self.tab_num_entry.insert(0, str(worker.employee_id))
                self.workshop_entry.insert(0, str(worker.workshop_number))
        except Exception as e:
            self.show_error(f"Ошибка загрузки данных: {str(e)}")

    def _save(self) -> None:
        """Сохраняет данные работника"""
        try:
            # Сбор данных
            full_name = self.name_entry.get().strip().split()
            if len(full_name) < 2:
                raise ValidationError("Введите полное имя (Фамилия Имя [Отчество])")

            employee_id = int(self.tab_num_entry.get())
            workshop_number = int(self.workshop_entry.get())

            worker_data = {
                "last_name": full_name[0],
                "first_name": full_name[1],
                "middle_name": full_name[2] if len(full_name) > 2 else "",
                "employee_id": employee_id,
                "workshop_number": workshop_number,
            }

            # Валидация
            if not self.validator.validate(worker_data):
                raise ValidationError("Проверьте правильность введенных данных")

            # Сохранение
            if self.worker_id:
                worker = self.worker_service.update(self.worker_id, worker_data)
            else:
                worker = self.worker_service.create(worker_data)

            if self.on_save:
                self.on_save(worker)

            self.show_success("Данные успешно сохранены")

        except ValueError as e:
            self.show_error(f"Введите корректные числовые значения: {str(e)}")
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Ошибка сохранения: {str(e)}")

    def _handle_cancel(self) -> None:
        """Обработчик отмены"""
        if self.on_cancel:
            self.on_cancel()


if __name__ == "__main__":
    # Пример использования
    root = ctk.CTk()
    root.title("Форма работника")


    # Создаем фиктивный сервис
    class DummyWorkerService:
        def create(self, data):
            print("Создание работника:", data)
            return type('obj', (object,), data)

        def update(self, id, data):
            print(f"Обновление работника {id}:", data)
            return type('obj', (object,), data)

        def get_by_id(self, id):
            return None


    form = WorkerForm(root, DummyWorkerService())
    form.pack(padx=20, pady=20)
    root.mainloop()