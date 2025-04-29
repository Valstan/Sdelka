# File: app/gui/base_form.py
"""
Базовый класс для всех форм приложения.
Содержит общую функциональность и методы, которые могут быть использованы в различных формах.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Optional, Callable


class BaseForm(ctk.CTkFrame):
    """
    Базовый класс для форм приложения.

    Attributes:
        parent: Родительский виджет
        service: Сервисный объект для работы с данными
        on_save_callback: Callback-функция, вызываемая при сохранении
    """

    def __init__(self, parent, service, *args, **kwargs):
        """
        Инициализация базовой формы

        Args:
            parent: Родительский виджет
            service: Сервисный объект для работы с данными
            args: Дополнительные аргументы
            kwargs: Дополнительные ключевые аргументы
        """
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.service = service
        self.on_save_callback = None
        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса формы"""
        raise NotImplementedError("Подклассы должны реализовать метод setup_ui")

    def bind_save_event(self, widget, callback: Callable):
        """
        Привязывает событие сохранения к виджету

        Args:
            widget: Виджет, к которому привязывается событие
            callback: Функция обратного вызова
        """
        widget.bind("<Return>", lambda event: self._on_save(callback))
        widget.bind("<KP_Enter>", lambda event: self._on_save(callback))

    def _on_save(self, callback: Callable):
        """
        Обработчик события сохранения

        Args:
            callback: Функция обратного вызова
        """
        try:
            if self.validate():
                result = callback()
                if result[0]:  # Успех
                    self.show_success_message()
                    self.clear()
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    self.show_error_message(result[1])
        except Exception as e:
            self.show_error_message(f"Ошибка при сохранении: {str(e)}")

    def validate(self) -> bool:
        """
        Проверяет корректность введенных данных

        Returns:
            True если данные корректны, False в противном случае
        """
        return True

    def clear(self):
        """Очищает поля формы"""
        raise NotImplementedError("Подклассы должны реализовать метод clear")

    def set_on_save(self, callback: Callable):
        """
        Устанавливает callback-функцию, которая будет вызвана после сохранения

        Args:
            callback: Callback-функция
        """
        self.on_save_callback = callback

    def show_error_message(self, message: str):
        """
        Отображает сообщение об ошибке

        Args:
            message: Текст сообщения
        """
        messagebox.showerror("Ошибка", message)

    def show_success_message(self):
        """Отображает сообщение об успешном выполнении операции"""
        messagebox.showinfo("Успех", "Данные успешно сохранены")