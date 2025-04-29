# File: app/gui/work_type_form.py
"""
Форма для добавления и редактирования информации о видах работ
"""

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple
import customtkinter as ctk
from app.models.models import WorkType
from app.services.work_types_service import WorkTypeService


class WorkTypeForm(ctk.CTkFrame):
    """
    Форма для добавления и редактирования видов работ

    Attributes:
        work_type_id: ID вида работы при редактировании
        service: Сервис для работы с видами работ
        entry_fields: Словарь полей ввода формы
        on_save_callback: Callback-функция после сохранения
    """

    def __init__(self, parent, service: WorkTypeService, work_type_id: Optional[int] = None):
        """
        Инициализация формы вида работы

        Args:
            parent: Родительский виджет
            service: Сервис для работы с видами работ
            work_type_id: ID вида работы для редактирования (опционально)
            args: Дополнительные аргументы
            kwargs: Дополнительные ключевые аргументы
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        self.parent = parent
        self.service = service
        self.work_type_id = work_type_id
        self.entry_fields = {}
        self.on_save_callback = None

        # Настройка интерфейса
        self._setup_ui()

        # Загрузка данных если это редактирование
        if work_type_id:
            self._load_work_type_data(work_type_id)

    def _setup_ui(self) -> None:
        """Настройка пользовательского интерфейса формы"""
        # Создаем контейнер для формы
        form_container = ctk.CTkFrame(self)
        form_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Наименование работы
        row1 = ctk.CTkFrame(form_container)
        row1.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row1, text="Наименование:", width=100).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["name"] = ctk.CTkEntry(row1)
        self.entry_fields["name"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Единица измерения
        row2 = ctk.CTkFrame(form_container)
        row2.pack(fill=tk.X, pady=(0, 20))

        ctk.CTkLabel(row2, text="Единица измерения:", width=100).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["unit"] = ctk.CTkComboBox(row2, values=["штуки", "комплекты"])
        self.entry_fields["unit"].set("штуки")
        self.entry_fields["unit"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Цена
        row3 = ctk.CTkFrame(form_container)
        row3.pack(fill=tk.X, pady=(0, 20))

        ctk.CTkLabel(row3, text="Цена:", width=100).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["price"] = ctk.CTkEntry(row3)
        self.entry_fields["price"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки
        btn_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        btn_frame.pack(fill=tk.X)

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

        # Привязываем событие Enter к кнопке "Сохранить"
        self.bind("<Return>", lambda event: self.save())
        self.bind("<KP_Enter>", lambda event: self.save())

    def _load_work_type_data(self, work_type_id: int) -> None:
        """
        Загружает данные вида работы для редактирования

        Args:
            work_type_id: ID вида работы
        """
        try:
            work_type = self.service.get_work_type_by_id(work_type_id)
            if work_type:
                self.entry_fields["name"].insert(0, work_type.name)
                self.entry_fields["unit"].set(work_type.unit)
                self.entry_fields["price"].insert(0, f"{work_type.price:.2f}")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных вида работы: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные вида работы: {str(e)}")

    def save(self) -> Tuple[bool, Optional[str]]:
        """
        Сохраняет или обновляет вид работы

        Returns:
            Кортеж (успех, сообщение)
        """
        # Проверяем валидность данных
        if not self.validate():
            return False, "Некорректные данные формы"

        try:
            # Получаем данные из формы
            name = self.entry_fields["name"].get().strip()
            unit = self.entry_fields["unit"].get().strip()
            price = float(self.entry_fields["price"].get().replace(',', '.'))

            # Если редактируем существующий вид работы
            if self.work_type_id:
                work_type = self.service.get_work_type_by_id(self.work_type_id)
                for key, value in locals().items():
                    if key in ["id", "service", "parent", "entry_fields"]:
                        continue
                    setattr(work_type, key, value)

                result = self.service.update_work_type(work_type)
            else:
                # Создаем новый вид работы
                work_type = WorkType(name=name, unit=unit, price=price)
                result = self.service.add_work_type(work_type)

            # Обработанный результат
            success, message = result

            if success:
                # Вызываем callback если он установлен
                if self.on_save_callback:
                    self.on_save_callback()
                else:
                    messagebox.showinfo("Успех", "Данные успешно сохранены")
            else:
                messagebox.showwarning("Предупреждение", message)

            return result
        except ValueError:
            error_msg = "Цена должна быть числом"
            messagebox.showwarning("Предупреждение", error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Ошибка при сохранении вида работы: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            messagebox.showerror("Ошибка", error_msg)
            return False, error_msg

    def validate(self) -> bool:
        """
        Валидирует введенные данные

        Returns:
            True если данные корректны, иначе False
        """
        name = self.entry_fields["name"].get().strip()
        price_str = self.entry_fields["price"].get().strip()

        # Проверка наименования
        if not name:
            messagebox.showwarning("Предупреждение", "Введите наименование работы")
            return False

        # Проверка цены
        if not price_str:
            messagebox.showwarning("Предупреждение", "Введите цену работы")
            return False

        try:
            price = float(price_str.replace(',', '.'))
            if price <= 0:
                raise ValueError("Цена должна быть положительным числом")
        except ValueError:
            messagebox.showwarning("Предупреждение", "Цена должна быть положительным числом")
            return False

        return True

    def clear(self) -> None:
        """Очищает все поля формы"""
        for field in self.entry_fields.values():
            if isinstance(field, ctk.CTkComboBox):
                field.set("")
            elif hasattr(field, "delete"):
                field.delete(0, tk.END)

    def set_on_save(self, callback: Callable) -> None:
        """
        Устанавливает callback-функцию, которая будет вызвана после сохранения

        Args:
            callback: Callback-функция без аргументов
        """
        self.on_save_callback = callback