# File: app/ui/forms/work_card_form.py
"""
Форма для создания и редактирования карточек работ.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, Optional, Callable, Tuple
from datetime import date
import logging

logger = logging.getLogger(__name__)


class WorkCardForm(ctk.CTkFrame):
    """
    Форма для редактирования карточки работы.

    Attributes:
        parent: Родительский виджет
        card: Текущая карточка работы
        on_save: Callback-функция, вызываемая при сохранении
        on_cancel: Callback-функция, вызываемая при отмене
    """

    def __init__(
            self,
            parent: ctk.CTkFrame,
            card_service: 'WorkCardsService',
            on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
            on_cancel: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Инициализирует форму карточки работы.

        Args:
            parent: Родительский виджет
            card_service: Сервис карточек работ
            on_save: Callback при сохранении
            on_cancel: Callback при отмене
        """
        super().__init__(parent)
        self.parent = parent
        self.card_service = card_service
        self.on_save = on_save
        self.on_cancel = on_cancel

        self.card = None
        self.logger = logging.getLogger(__name__)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Создает элементы интерфейса."""
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Первая строка: Номер и дата
        row1 = ctk.CTkFrame(form_frame)
        row1.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row1, text="Номер:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields = {}

        self.entry_fields["number"] = ctk.CTkEntry(row1, width=120)
        self.entry_fields["number"].pack(side=tk.LEFT, padx=(0, 10))

        self.entry_fields["date_day"] = ctk.CTkComboBox(row1, width=60, values=[str(i) for i in range(1, 32)])
        self.entry_fields["date_day"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["date_month"] = ctk.CTkComboBox(row1, width=60, values=[str(i) for i in range(1, 13)])
        self.entry_fields["date_month"].pack(side=tk.LEFT, padx=(0, 5))

        self.entry_fields["date_year"] = ctk.CTkComboBox(row1, width=80, values=[str(i) for i in range(2000, 2051)])
        self.entry_fields["date_year"].pack(side=tk.LEFT)

        # Вторая строка: Изделие
        row2 = ctk.CTkFrame(form_frame)
        row2.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row2, text="Изделие:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["product"] = AutocompleteCombobox(
            row2,
            search_function=self.card_service.products_service.search_products,
            display_key="full_name"
        )
        self.entry_fields["product"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Третья строка: Контракт
        row3 = ctk.CTkFrame(form_frame)
        row3.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row3, text="Контракт:", width=80).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["contract"] = AutocompleteCombobox(
            row3,
            search_function=self.card_service.contracts_service.search_contracts,
            display_key="contract_number"
        )
        self.entry_fields["contract"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Четвертая строка: Таблица элементов работы
        row4 = ctk.CTkFrame(form_frame)
        row4.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        items_label = ctk.CTkLabel(row4, text="Элементы работы:")
        items_label.pack(anchor=tk.W, padx=5, pady=(0, 5))

        items_container = ctk.CTkScrollableFrame(row4)
        items_container.pack(fill=tk.BOTH, expand=True)

        self.items_table = ItemsTable(items_container, self.card_service)
        self.items_table.pack(fill=tk.BOTH, expand=True)

        add_item_btn = ctk.CTkButton(
            row4,
            text="Добавить элемент",
            command=self._add_work_item
        )
        add_item_btn.pack(pady=5, anchor=tk.E)

        # Пятая строка: Таблица работников
        row5 = ctk.CTkFrame(form_frame)
        row5.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        workers_label = ctk.CTkLabel(row5, text="Работники:")
        workers_label.pack(anchor=tk.W, padx=5, pady=(0, 5))

        workers_container = ctk.CTkScrollableFrame(row5)
        workers_container.pack(fill=tk.BOTH, expand=True)

        self.workers_table = WorkersTable(workers_container, self.card_service)
        self.workers_table.pack(fill=tk.BOTH, expand=True)

        add_worker_btn = ctk.CTkButton(
            row5,
            text="Добавить работника",
            command=self._add_worker
        )
        add_worker_btn.pack(pady=5, anchor=tk.E)

        # Шестая строка: Общая сумма
        row6 = ctk.CTkFrame(form_frame)
        row6.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(row6, text="Общая сумма:", font=("Roboto", 12, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_fields["total_amount"] = ctk.CTkEntry(row6, state="readonly")
        self.entry_fields["total_amount"].pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки действий
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        self.save_button = ctk.CTkButton(
            action_frame,
            text="Сохранить",
            command=self._save_card
        )
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_button = ctk.CTkButton(
            action_frame,
            text="Отмена",
            fg_color="#9E9E9E",
            hover_color="#757575",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT)

        # Привязываем событие Enter к кнопке "Сохранить"
        self.bind("<Return>", lambda event: self._save_card())
        self.bind("<KP_Enter>", lambda event: self._save_card())

    def set_card(self, card: Optional[Dict[str, Any]] = None) -> None:
        """
        Устанавливает карточку для редактирования.

        Args:
            card: Карточка работы для редактирования
        """
        self.card = card

        if card:
            # Загружаем основные данные карточки
            self.entry_fields["number"].insert(0, str(card.get("card_number", "")))

            # Устанавливаем дату
            card_date = card.get("card_date", date.today())
            if isinstance(card_date, str):
                try:
                    card_date = date.fromisoformat(card_date.split("T")[0])
                except ValueError:
                    card_date = date.today()

            self.entry_fields["date_day"].set(str(card_date.day))
            self.entry_fields["date_month"].set(str(card_date.month))
            self.entry_fields["date_year"].set(str(card_date.year))

            # Устанавливаем данные изделия
            if product := card.get("product"):
                self.entry_fields["product"].set(product.get("full_name", ""))

            # Устанавливаем данные контракта
            if contract := card.get("contract"):
                self.entry_fields["contract"].set(contract.get("contract_number", ""))

            # Устанавливаем общую сумму
            self.entry_fields["total_amount"].delete(0, tk.END)
            self.entry_fields["total_amount"].insert(0, f"{card.get('total_amount', 0):.2f}")

            # Обновляем таблицы
            self.items_table.set_card(card)
            self.workers_table.set_card(card)

    def _save_card(self) -> Tuple[bool, Optional[str]]:
        """
        Сохраняет текущую карточку.

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Получаем данные формы
            data = self._get_form_data()

            # Валидируем данные
            if not self._validate(data):
                return False, "Некорректные данные формы"

            # Создаем объект карточки
            card = self._create_card_object(data)

            # Сохраняем или обновляем карточку
            if card.id:
                success, message = self.card_service.update_work_card(card)
            else:
                success, message = self.card_service.add_work_card(card)

            if success:
                self._update_items_and_workers(card)

                # Вызываем callback если установлен
                if self.on_save:
                    self.on_save({"card": card})

                logger.info(f"Карточка {'обновлена' if card.id else 'создана'}: {card.card_number}")
                return True, None
            else:
                logger.warning(f"Не удалось сохранить карточку: {message}")
                return False, message

        except Exception as e:
            logger.error(f"Ошибка сохранения карточки: {e}", exc_info=True)
            return False, f"Ошибка сохранения карточки: {str(e)}"

    def _get_form_data(self) -> Dict[str, Any]:
        """
        Получает данные из формы.

        Returns:
            Словарь с данными формы
        """
        return {
            "number": int(self.entry_fields["number"].get()),
            "day": int(self.entry_fields["date_day"].get()),
            "month": int(self.entry_fields["date_month"].get()),
            "year": int(self.entry_fields["date_year"].get()),
            "product": self.entry_fields["product"].get_selected_item(),
            "contract": self.entry_fields["contract"].get_selected_item()
        }

    def _validate(self, data: Dict[str, Any]) -> bool:
        """
        Проверяет корректность введенных данных.

        Args:
            data: Данные формы

        Returns:
            True, если данные корректны, иначе False
        """
        if not data.get("product"):
            messagebox.showwarning("Предупреждение", "Выберите изделие")
            return False

        if not data.get("contract"):
            messagebox.showwarning("Предупреждение", "Выберите контракт")
            return False

        # Проверяем, чтобы номер карточки был уникальным
        existing = self.card_service.get_work_card_by_number(data["number"])
        if existing and (not self.card or existing["id"] != self.card["id"]):
            messagebox.showwarning("Предупреждение", "Карточка с таким номером уже существует")
            return False

        return True

    def _create_card_object(self, data: Dict[str, Any]) -> 'WorkCard':
        """
        Создает объект карточки работы из данных формы.

        Args:
            data: Данные формы

        Returns:
            Объект WorkCard
        """
        from app.core.models.work_card import WorkCard

        return WorkCard(
            id=self.card["id"] if self.card else None,
            card_number=str(data["number"]),
            card_date=date(data["year"], data["month"], data["day"]),
            product_id=data["product"]["id"],
            contract_id=data["contract"]["id"],
            total_amount=float(self.entry_fields["total_amount"].get().replace(',', '.'))
        )

    def _update_items_and_workers(self, card: 'WorkCard') -> None:
        """
        Обновляет элементы работы и назначения работников.

        Args:
            card: Обновленная карточка работы
        """
        # Обновляем элементы работы
        for item in card.items:
            if item.is_new:
                self.card_service.add_work_item(card, item)
            elif item.is_modified:
                self.card_service.update_work_item(card, item)

        # Обновляем назначения работников
        for worker in card.workers:
            if worker.is_new:
                self.card_service.add_worker_assignment(card, worker)
            elif worker.is_modified:
                self.card_service.update_worker_assignment(card, worker)

    def _on_cancel(self) -> None:
        """
        Обработчик события отмены.
        """
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите отменить изменения?"):
            if self.on_cancel:
                self.on_cancel({})

            if self.card:
                self.set_card(self.card)  # Сбрасываем изменения

    def _add_work_item(self) -> None:
        """
        Открывает диалоговое окно для добавления нового элемента работы.
        """
        dialog = WorkItemDialog(
            self,
            self.card_service,
            lambda item: self.items_table.add_item(item)
        )
        dialog.wait_window()
        self._update_total_amount()

    def _add_worker(self) -> None:
        """
        Открывает диалоговое окно для добавления нового работника.
        """
        dialog = WorkerAssignmentDialog(
            self,
            self.card_service,
            lambda worker: self.workers_table.add_worker(worker)
        )
        dialog.wait_window()
        self._update_total_amount()