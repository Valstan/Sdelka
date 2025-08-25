from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

from config.settings import CONFIG
from db.sqlite import get_connection
from services import suggestions
from services.work_orders import WorkOrderInput, WorkOrderItemInput, WorkOrderWorkerInput, create_work_order
from services.validation import validate_date
from db import queries as q
from gui.widgets.date_picker import DatePicker
from gui.widgets.date_picker import open_for_anchor
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import place_suggestions_under_entry, create_suggestion_button, create_suggestions_frame
import logging

logger = logging.getLogger(__name__)


@dataclass
class ItemRow:
    job_type_id: int
    job_type_name: str
    quantity: float
    unit_price: float
    line_amount: float


class WorkOrdersForm(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self.selected_contract_id: Optional[int] = None
        self.selected_product_id: Optional[int] = None
        self.selected_workers: dict[int, str] = {}
        self.worker_amounts: dict[int, float] = {}
        self._worker_amount_vars: dict[int, ctk.StringVar] = {}
        self._manual_amount_ids: set[int] = set()
        self._manual_mode: bool = False
        self.item_rows: list[ItemRow] = []
        self.editing_order_id: Optional[int] = None
        self._manual_worker_counter = -1  # Инициализируем счетчик для ручных работников

        self._build_ui()
        self._update_totals()
        self._load_recent_orders()

    def _build_ui(self) -> None:
        # Контейнер без разделителя: правая панель фиксированной ширины, левая — остальное
        container = ctk.CTkFrame(self)
        container.pack(expand=True, fill="both")

        # Right side (orders list) — пакуем справа, ширина управляется программно
        right = ctk.CTkFrame(container, width=320)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._right = right

        # Left side (form) — занимает всё оставшееся
        left = ctk.CTkFrame(container)
        left.pack(side="left", expand=True, fill="both")
        # Резиновая сетка: списки тянут высоту
        try:
            left.grid_rowconfigure(0, weight=0)  # header
            left.grid_rowconfigure(1, weight=0)  # items controls
            left.grid_rowconfigure(2, weight=1)  # items list (expand)
            left.grid_rowconfigure(3, weight=0)  # workers controls
            left.grid_rowconfigure(4, weight=1)  # workers list (expand)
            left.grid_rowconfigure(5, weight=0)  # totals
            left.grid_columnconfigure(0, weight=1)
        except Exception:
            pass
        # Первичная установка ширины правой панели и пересчет при ресайзе
        def _set_initial_width() -> None:
            self._enforce_right_width_limit(adjust_to_content=True)
        self.after(200, _set_initial_width)

        def _on_resize(_evt=None):
            self._enforce_right_width_limit(adjust_to_content=False)
        self.bind("<Configure>", _on_resize, add="+")

        # Header form
        header = ctk.CTkFrame(left)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        # 3 колонки
        for i in range(3):
            header.grid_columnconfigure(i, weight=1)

        # Date
        self.date_var = ctk.StringVar(value=dt.date.today().strftime(CONFIG.date_format))
        ctk.CTkLabel(header, text="Дата").grid(row=0, column=0, sticky="w", padx=5)
        self.date_entry = ctk.CTkEntry(header, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 6))
        self.date_entry.bind("<FocusIn>", lambda e: self._open_date_picker())

        # Contract
        ctk.CTkLabel(header, text="Контракт").grid(row=0, column=1, sticky="w", padx=5)
        self.contract_entry = ctk.CTkEntry(header, placeholder_text="Начните вводить шифр")
        self.contract_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 6))
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)
        self.contract_entry.bind("<FocusIn>", lambda e: self._on_contract_key())

        # Product
        ctk.CTkLabel(header, text="Изделие").grid(row=0, column=2, sticky="w", padx=5)
        self.product_entry = ctk.CTkEntry(header, placeholder_text="Номер/Название")
        self.product_entry.grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 6))
        self.product_entry.bind("<KeyRelease>", self._on_product_key)
        self.product_entry.bind("<FocusIn>", lambda e: self._on_product_key())

        # Suggestion frames
        self.suggest_contract_frame = create_suggestions_frame(self)
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame = create_suggestions_frame(self)
        self.suggest_product_frame.place_forget()

        # Items section
        items_frame = ctk.CTkFrame(left)
        items_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        for i in range(5):
            items_frame.grid_columnconfigure(i, weight=1 if i == 0 else 0)

        ctk.CTkLabel(items_frame, text="Вид работ").grid(row=0, column=0, sticky="w", padx=5)
        self.job_entry = ctk.CTkEntry(items_frame, placeholder_text="Начните ввод")
        self.job_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 6))
        self.job_entry.bind("<KeyRelease>", self._on_job_key)
        self.job_entry.bind("<FocusIn>", lambda e: self._on_job_key())
        self.job_entry.bind("<Button-1>", lambda e: self.after(1, self._on_job_key))

        ctk.CTkLabel(items_frame, text="Кол-во").grid(row=0, column=1, sticky="w", padx=5)
        self.qty_var = ctk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(items_frame, textvariable=self.qty_var)
        self.qty_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 6))
        self.qty_entry.bind("<FocusIn>", lambda e: self._hide_all_suggests())

        add_btn = ctk.CTkButton(items_frame, text="Добавить", command=self._add_item)
        add_btn.grid(row=1, column=4, sticky="e", padx=5, pady=(0, 6))

        self.suggest_job_frame = create_suggestions_frame(self)
        self.suggest_job_frame.place_forget()

        # Items list (adaptive rows with delete buttons)
        items_list_frame = ctk.CTkFrame(left)
        items_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        # Header row
        hdr = ctk.CTkFrame(items_list_frame)
        hdr.grid(row=0, column=0, sticky="ew")
        for i, txt in enumerate(["Вид работ", "Кол-во", "Цена", "Сумма", " "]):
            c = ctk.CTkLabel(hdr, text=txt)
            c.grid(row=0, column=i, sticky="w", padx=4)
        for i, w in enumerate([6, 2, 2, 2, 1]):
            hdr.grid_columnconfigure(i, weight=w)
        # Scrollable rows
        items_list_frame.grid_rowconfigure(1, weight=1)
        items_list_frame.grid_columnconfigure(0, weight=1)
        self.items_list = ctk.CTkScrollableFrame(items_list_frame)
        self.items_list.grid(row=1, column=0, sticky="nsew")

        # Workers section
        workers_frame = ctk.CTkFrame(left)
        workers_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(workers_frame, text="Работник").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.worker_entry = ctk.CTkEntry(workers_frame, placeholder_text="Начните ввод ФИО", width=300)
        self.worker_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.worker_entry.bind("<KeyRelease>", self._on_worker_key)
        self.worker_entry.bind("<FocusIn>", lambda e: self._on_worker_key())
        self.worker_entry.bind("<Button-1>", lambda e: self.after(1, self._on_worker_key))
        ctk.CTkButton(workers_frame, text="Добавить", command=self._add_worker_from_entry).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.suggest_worker_frame = create_suggestions_frame(self)
        self.suggest_worker_frame.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

        self.workers_list = ctk.CTkScrollableFrame(left)
        self.workers_list.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 8))

        # Totals and Save
        totals_frame = ctk.CTkFrame(left)
        totals_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=6)
        for i in range(4):
            totals_frame.grid_columnconfigure(i, weight=1 if i == 0 else 0)

        self.total_var = ctk.StringVar(value="0.00")
        self.per_worker_var = ctk.StringVar(value="0.00")

        # Итоги — верхняя строка
        totals_row = ctk.CTkFrame(totals_frame)
        totals_row.grid(row=0, column=0, columnspan=4, sticky="ew")
        ctk.CTkLabel(totals_row, text="Итог, руб:").pack(side="left", padx=5)
        ctk.CTkLabel(totals_row, textvariable=self.total_var).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(totals_row, text="На одного, руб:").pack(side="left", padx=5)
        ctk.CTkLabel(totals_row, textvariable=self.per_worker_var).pack(side="left")

        # Кнопки — ниже итогов
        actions = ctk.CTkFrame(totals_frame)
        actions.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=(6, 0))
        self.save_btn = ctk.CTkButton(actions, text="Сохранить", command=self._save)
        self.save_btn.pack(side="left", padx=4)
        self.delete_btn = ctk.CTkButton(actions, text="Удалить", command=self._delete, fg_color="#b91c1c", hover_color="#7f1d1d")
        self.delete_btn.pack(side="left", padx=4)
        self.cancel_btn = ctk.CTkButton(actions, text="Отмена", command=self._cancel_edit, fg_color="#6b7280")
        self.cancel_btn.pack(side="left", padx=4)
        self.manual_btn = ctk.CTkButton(actions, text="Ручной ввод сумм: ВЫКЛ", command=self._toggle_manual_mode)
        self.manual_btn.pack(side="left", padx=4)

        if self._readonly:
            # Заблокировать ввод и действия редактирования
            for w in (self.date_entry, self.contract_entry, self.product_entry, self.job_entry, self.qty_entry, self.worker_entry):
                try:
                    w.configure(state="disabled")
                except Exception:
                    pass
            for b in (add_btn, self.save_btn, self.delete_btn, self.cancel_btn):
                b.configure(state="disabled")

        # Right-side: existing orders list
        ctk.CTkLabel(right, text="Список нарядов").pack(padx=10, pady=(10, 0), anchor="w")
        filter_frame = ctk.CTkFrame(right)
        filter_frame.pack(fill="x", padx=10, pady=5)
        self.filter_from = ctk.StringVar()
        self.filter_to = ctk.StringVar()
        ctk.CTkLabel(filter_frame, text="с").pack(side="left", padx=2)
        self.filter_from_entry = ctk.CTkEntry(filter_frame, textvariable=self.filter_from, width=100)
        self.filter_from_entry.pack(side="left")
        self.filter_from_entry.bind("<FocusIn>", lambda e: self._open_date_picker_for(self.filter_from, self.filter_from_entry))

        ctk.CTkLabel(filter_frame, text="по").pack(side="left", padx=2)
        self.filter_to_entry = ctk.CTkEntry(filter_frame, textvariable=self.filter_to, width=100)
        self.filter_to_entry.pack(side="left")
        self.filter_to_entry.bind("<FocusIn>", lambda e: self._open_date_picker_for(self.filter_to, self.filter_to_entry))
        ctk.CTkButton(filter_frame, text="Фильтр", width=80, command=self._apply_filter).pack(side="left", padx=6)

        list_frame = ctk.CTkFrame(right)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.orders_tree = ttk.Treeview(list_frame, columns=("no", "date", "contract", "product", "total"), show="headings")
        self.orders_tree.heading("no", text="№")
        self.orders_tree.heading("date", text="Дата")
        self.orders_tree.heading("contract", text="Контракт")
        self.orders_tree.heading("product", text="Изделие")
        self.orders_tree.heading("total", text="Сумма")
        self.orders_tree.column("no", width=60, anchor="center")
        self.orders_tree.column("date", width=100, anchor="center")
        self.orders_tree.column("contract", width=140)
        self.orders_tree.column("product", width=200)
        self.orders_tree.column("total", width=110, anchor="e")
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.orders_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.orders_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)
        # Заголовки кликабельны для сортировки
        for col, title in (("no", "№"), ("date", "Дата"), ("contract", "Контракт"), ("product", "Изделие"), ("total", "Сумма")):
            self.orders_tree.heading(col, text=title, command=lambda c=col: self._sort_orders_by(c))

    # --- enforce right panel width and autosize columns ---
    def _autosize_orders_columns(self) -> None:
        try:
            font = tkfont.nametofont("TkDefaultFont")
        except Exception:
            font = tkfont.Font()
        pad = 24
        min_widths = {"no": 50, "date": 90, "contract": 80, "product": 120, "total": 90}
        for col in self.orders_tree["columns"]:
            header = self.orders_tree.heading(col).get("text", "")
            max_w = font.measure(str(header))
            for iid in self.orders_tree.get_children(""):
                text = str(self.orders_tree.set(iid, col))
                w = font.measure(text)
                if w > max_w:
                    max_w = w
            self.orders_tree.column(col, width=max(max_w + pad, min_widths.get(col, 60)))

    def _get_orders_content_width(self) -> int:
        total = 0
        try:
            for col in self.orders_tree["columns"]:
                total += int(self.orders_tree.column(col, "width") or 0)
            # учесть вертикальный скроллбар и внутренние отступы
            total += 20 + 16
        except Exception:
            total = 360
        return total

    def _enforce_right_width_limit(self, adjust_to_content: bool) -> None:
        try:
            total = self.winfo_width()
            if not total or total <= 1:
                self.after(120, lambda: self._enforce_right_width_limit(adjust_to_content))
                return
            max_right = int(total * 0.40)
            desired = max_right
            if adjust_to_content:
                desired = min(max_right, self._get_orders_content_width())
            # Минимальная ширина справа, чтобы элементы управления не ломались
            min_right = 260
            desired = max(min_right, desired)
            # Применить ширину к правой панели
            try:
                self._right.configure(width=desired)
                self._right.pack_propagate(False)
            except Exception:
                pass
        except Exception:
            pass

    # --- suggest helpers ---
    def _hide_all_suggests(self) -> None:
        for frame in (
            self.suggest_contract_frame,
            self.suggest_product_frame,
            self.suggest_job_frame,
            self.suggest_worker_frame,
        ):
            frame.place_forget()

    def _place_suggest_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        place_suggestions_under_entry(entry, frame, self)

    def _on_contract_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_contract_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.contract_entry, self.suggest_contract_frame, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_contracts(conn, self.contract_entry.get().strip(), CONFIG.autocomplete_limit)
        
        shown = 0
        for _id, label in rows:
            create_suggestion_button(self.suggest_contract_frame, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("work_orders.contract", self.contract_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(self.suggest_contract_frame, text=label, command=lambda l=label: self._pick_contract(self.selected_contract_id or 0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все контракты
        if shown == 0:
            with get_connection() as conn:
                all_contracts = suggestions.suggest_contracts(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_contracts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_contract_frame, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_contract(self, contract_id: int, label: str) -> None:
        self.selected_contract_id = contract_id
        self.contract_entry.delete(0, "end")
        self.contract_entry.insert(0, label)
        record_use("work_orders.contract", label)
        self.suggest_contract_frame.place_forget()

    def _on_product_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_product_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.product_entry, self.suggest_product_frame, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_products(conn, self.product_entry.get().strip(), CONFIG.autocomplete_limit)
        
        shown = 0
        for _id, label in rows:
            create_suggestion_button(self.suggest_product_frame, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("work_orders.product", self.product_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(self.suggest_product_frame, text=label, command=lambda l=label: self._pick_product(self.selected_product_id or 0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все изделия
        if shown == 0:
            with get_connection() as conn:
                all_products = suggestions.suggest_products(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_product_frame, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_job_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.job_entry, self.suggest_job_frame, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_job_types(conn, self.job_entry.get().strip(), CONFIG.autocomplete_limit)
        
        shown = 0
        for _id, label in rows:
            create_suggestion_button(self.suggest_job_frame, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("work_orders.job_type", self.job_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(self.suggest_job_frame, text=label, command=lambda l=label: self._pick_job(getattr(self.job_entry, "_selected_job_id", 0) or 0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все виды работ
        if shown == 0:
            with get_connection() as conn:
                all_job_types = suggestions.suggest_job_types(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_job_types:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_job_frame, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_job(self, job_type_id: int, label: str) -> None:
        self.job_entry.delete(0, "end")
        self.job_entry.insert(0, label)
        self.job_entry._selected_job_id = job_type_id
        record_use("work_orders.job_type", label)
        self.suggest_job_frame.place_forget()

    def _pick_product(self, product_id: int, label: str) -> None:
        self.product_entry.delete(0, "end")
        self.product_entry.insert(0, label)
        self.selected_product_id = product_id
        record_use("work_orders.product", label)
        self.suggest_product_frame.place_forget()

    def _on_worker_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_worker_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.worker_entry, self.suggest_worker_frame, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_workers(conn, self.worker_entry.get().strip(), CONFIG.autocomplete_limit)
        
        shown = 0
        for _id, label in rows:
            create_suggestion_button(self.suggest_worker_frame, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("work_orders.worker", self.worker_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(self.suggest_worker_frame, text=label, command=lambda l=label: self._pick_worker(0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем всех работников
        if shown == 0:
            with get_connection() as conn:
                all_workers = suggestions.suggest_workers(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_workers:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_worker_frame, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_worker(self, worker_id: int, label: str) -> None:
        self.worker_entry.delete(0, "end")
        self.worker_entry.insert(0, label)
        record_use("work_orders.worker", label)
        # Исторические подсказки передают worker_id == 0. Считаем их ручными и
        # создаем уникальный отрицательный ID, чтобы не конфликтовать и не терять при сохранении.
        if worker_id == 0:
            self._manual_worker_counter -= 1
            manual_worker_id = self._manual_worker_counter
            self.selected_workers[manual_worker_id] = label
            self._refresh_workers_display()
            self._update_totals()
        else:
            self._add_worker(worker_id, label)
        self.suggest_worker_frame.place_forget()

    def _add_worker_from_entry(self) -> None:
        worker_name = self.worker_entry.get().strip()
        if not worker_name:
            messagebox.showwarning("Проверка", "Введите имя работника")
            return
        
        # Проверяем, не добавлен ли уже этот работник
        if worker_name in self.selected_workers.values():
            messagebox.showwarning("Проверка", "Работник уже добавлен в бригаду")
            return
        
        # Генерируем уникальный отрицательный ID для ручно добавленного работника
        self._manual_worker_counter -= 1
        manual_worker_id = self._manual_worker_counter
        
        # Добавляем работника
        self.selected_workers[manual_worker_id] = worker_name
        
        # Обновляем отображение списка работников
        self._refresh_workers_display()
        self._update_totals()
        
        # Очищаем поле ввода
        self.worker_entry.delete(0, "end")
        self.suggest_worker_frame.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggests()
            return
        for frame in (self.suggest_contract_frame, self.suggest_product_frame, self.suggest_job_frame, self.suggest_worker_frame):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self._hide_all_suggests()

    # ---- Items and Workers manipulation ----
    def _add_item(self) -> None:
        job_type_id = getattr(self.job_entry, "_selected_job_id", None)
        if not job_type_id:
            messagebox.showwarning("Проверка", "Выберите вид работ из подсказки")
            return
        try:
            qty = float(self.qty_var.get().strip() or "0")
        except Exception:
            messagebox.showwarning("Проверка", "Количество должно быть числом")
            return
        if qty <= 0:
            messagebox.showwarning("Проверка", "Количество должно быть > 0")
            return

        with get_connection() as conn:
            row = conn.execute("SELECT name, price FROM job_types WHERE id = ?", (job_type_id,)).fetchone()
            if not row:
                messagebox.showerror("Ошибка", "Вид работ не найден")
                return
            name = row["name"]
            unit_price = float(row["price"]) if row["price"] is not None else 0.0

        amount = float(Decimal(str(unit_price)) * Decimal(str(qty)))
        item = ItemRow(job_type_id=job_type_id, job_type_name=name, quantity=qty, unit_price=unit_price, line_amount=amount)
        self.item_rows.append(item)
        # UI row
        row = ctk.CTkFrame(self.items_list)
        row.pack(fill="x", pady=2)
        # grid columns
        for i, w in enumerate([6, 2, 2, 2, 1]):
            row.grid_columnconfigure(i, weight=w)
        ctk.CTkLabel(row, text=name, anchor="w").grid(row=0, column=0, sticky="ew", padx=4)
        ctk.CTkLabel(row, text=str(qty)).grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(row, text=f"{unit_price:.2f}").grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkLabel(row, text=f"{amount:.2f}").grid(row=0, column=3, sticky="w", padx=4)
        del_btn = ctk.CTkButton(row, text="Удалить", width=80, fg_color="#b91c1c", hover_color="#7f1d1d")
        del_btn.grid(row=0, column=4, sticky="e", padx=4)
        idx = len(self.item_rows) - 1
        del_btn.configure(command=lambda i=idx, rf=row: self._remove_item_row(i, rf))
        row._del_btn = del_btn

        self.job_entry.delete(0, "end")
        if hasattr(self.job_entry, "_selected_job_id"):
            delattr(self.job_entry, "_selected_job_id")
        self.qty_var.set("1")

        self._update_totals()

    def _remove_item_row(self, idx: int, row_frame: ctk.CTkFrame) -> None:
        if 0 <= idx < len(self.item_rows):
            self.item_rows.pop(idx)
        try:
            row_frame.destroy()
        except Exception:
            pass
        # Перенумеровать callbacks
        for new_idx, child in enumerate(self.items_list.winfo_children()):
            if hasattr(child, "_del_btn"):
                child._del_btn.configure(command=lambda i=new_idx, rf=child: self._remove_item_row(i, rf))
        self._update_totals()

    def _clear_items(self) -> None:
        for child in self.items_list.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self.item_rows.clear()
        self._update_totals()

    def _add_worker(self, worker_id: Optional[int] = None, label: Optional[str] = None) -> None:
        if worker_id is None:
            return
        
        # Проверяем корректность ID
        if not isinstance(worker_id, int):
            logger.warning("Попытка добавить некорректный ID работника: %s", worker_id)
            return
        
        # Проверяем, не добавлен ли уже этот работник
        if worker_id in self.selected_workers:
            logger.info("Работник %s уже добавлен в бригаду", worker_id)
            return
        
        # Добавляем работника
        self.selected_workers[worker_id] = label or f"Работник {worker_id}"
        
        # Обновляем отображение списка работников
        self._refresh_workers_display()
        self._update_totals()
    
    def _refresh_workers_display(self) -> None:
        """Обновляет отображение списка работников"""
        # Очищаем текущий список
        for w in self.workers_list.winfo_children():
            w.destroy()
        self._worker_amount_vars.clear()

        # Создаем новые строки для каждого работника
        for wid, name in self.selected_workers.items():
            row = ctk.CTkFrame(self.workers_list)
            row.pack(fill="x", pady=2)
            
            # Имя работника
            ctk.CTkLabel(row, text=name).pack(side="left", padx=4)

            # Поле суммы для работника
            var = ctk.StringVar(value=f"{self.worker_amounts.get(wid, 0.0):.2f}")
            self._worker_amount_vars[wid] = var
            amount_entry = ctk.CTkEntry(row, textvariable=var, width=100)
            amount_entry.pack(side="right", padx=4)
            amount_entry.bind("<KeyRelease>", lambda _e=None, i=wid: self._on_worker_amount_change(i))
            if self._readonly or not self._manual_mode:
                try:
                    amount_entry.configure(state="disabled")
                except Exception:
                    pass
            
            # Кнопка удаления
            del_btn = ctk.CTkButton(
                row, 
                text="Удалить", 
                width=80, 
                fg_color="#b91c1c", 
                hover_color="#7f1d1d", 
                command=lambda i=wid: self._remove_worker(i)
            )
            del_btn.pack(side="right", padx=4)

        # После перерисовки — пересчитать и обновить поля сумм
        self._recalculate_worker_amounts()
        self._update_worker_amount_entries()

    def _remove_worker(self, worker_id: int) -> None:
        if worker_id in self.selected_workers:
            del self.selected_workers[worker_id]
            if worker_id in self.worker_amounts:
                del self.worker_amounts[worker_id]
            if worker_id in self._manual_amount_ids:
                self._manual_amount_ids.discard(worker_id)
            self._refresh_workers_display()
            self._update_totals()

    def _update_totals(self) -> None:
        total = sum(i.line_amount for i in self.item_rows)
        num_workers = max(1, len(self.selected_workers))
        per_worker = total / num_workers if num_workers else 0.0
        self.total_var.set(f"{total:.2f}")
        self.per_worker_var.set(f"{per_worker:.2f}")
        # Обновляем распределение по работникам
        self._recalculate_worker_amounts()
        self._update_worker_amount_entries()

    def _update_worker_amount_entries(self) -> None:
        for wid, var in self._worker_amount_vars.items():
            try:
                var.set(f"{float(self.worker_amounts.get(wid, 0.0)):.2f}")
            except Exception:
                pass

    def _on_worker_amount_change(self, worker_id: int) -> None:
        var = self._worker_amount_vars.get(worker_id)
        if not var:
            return
        if self._readonly or not getattr(self, "_manual_mode", False):
            return
        raw = (var.get() or "").strip().replace(",", ".")
        try:
            entered = round(float(raw), 2)
        except Exception:
            return
        if entered < 0:
            entered = 0.0
        # Фиксируем ручное значение; перераспределения в ручном режиме не выполняем
        self._manual_amount_ids.add(worker_id)
        self.worker_amounts[worker_id] = float(entered)
        self._update_worker_amount_entries()

    def _recalculate_worker_amounts(self) -> None:
        """Автоматическое равномерное распределение между всеми работниками (если режим авто)."""
        if getattr(self, "_manual_mode", False):
            return
        ids = list(self.selected_workers.keys())
        if not ids:
            return
        total = round(sum(i.line_amount for i in self.item_rows), 2)
        n = len(ids)
        per = round(total / n, 2) if n else 0.0
        amounts = [per] * n
        diff = round(total - round(per * n, 2), 2)
        if n > 0 and abs(diff) >= 0.01:
            amounts[-1] = round(amounts[-1] + diff, 2)
        for wid, amt in zip(ids, amounts):
            self.worker_amounts[wid] = float(amt)

    def _toggle_manual_mode(self) -> None:
        self._manual_mode = not self._manual_mode
        try:
            self.manual_btn.configure(text=f"Ручной ввод сумм: {'ВКЛ' if self._manual_mode else 'ВЫКЛ'}")
        except Exception:
            pass
        if not self._manual_mode:
            # Выходим из ручного режима: очищаем ручные отметки и равномерно распределяем
            self._manual_amount_ids.clear()
            self._recalculate_worker_amounts()
            self._update_worker_amount_entries()
        # Перерисовать строки работников с актуальной доступностью полей
        self._refresh_workers_display()

    def _open_date_picker(self) -> None:
        self._hide_all_suggests()
        open_for_anchor(self, self.date_entry, self.date_var.get().strip(), lambda d: self.date_var.set(d))

    def _open_date_picker_for(self, var, anchor=None) -> None:
        self._hide_all_suggests()
        if anchor is None:
            return
        open_for_anchor(self, anchor, var.get().strip(), lambda d: var.set(d))

    # ---- Orders list ----
    def _load_recent_orders(self) -> None:
        for iid in getattr(self, "_order_rows", []):
            try:
                self.orders_tree.delete(iid)
            except Exception:
                pass
        self._order_rows = []
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT wo.id, wo.order_no, wo.date, c.code AS contract_code, p.name AS product_name, wo.total_amount
                FROM work_orders wo
                LEFT JOIN contracts c ON c.id = wo.contract_id
                LEFT JOIN products p ON p.id = wo.product_id
                ORDER BY date DESC, order_no DESC
                LIMIT 200
                """
            ).fetchall()
        for r in rows:
            iid = self.orders_tree.insert("", "end", iid=str(r["id"]), values=(r["order_no"], r["date"], r["contract_code"] or "", r["product_name"] or "", f"{r['total_amount']:.2f}"))
            self._order_rows.append(iid)
        self._autosize_orders_columns()

    def _apply_filter(self) -> None:
        date_from = (self.filter_from.get().strip() or None)
        date_to = (self.filter_to.get().strip() or None)
        where = []
        params: list[str] = []
        if date_from:
            where.append("date >= ?")
            params.append(date_from)
        if date_to:
            where.append("date <= ?")
            params.append(date_to)
        sql = "SELECT wo.id, wo.order_no, wo.date, c.code, p.name, wo.total_amount FROM work_orders wo LEFT JOIN contracts c ON c.id=wo.contract_id LEFT JOIN products p ON p.id=wo.product_id"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY date DESC, order_no DESC LIMIT 500"
        for iid in self.orders_tree.get_children():
            self.orders_tree.delete(iid)
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        for r in rows:
            self.orders_tree.insert("", "end", iid=str(r["id"]), values=(r["order_no"], r["date"], r["code"] or "", r["name"] or "", f"{r['total_amount']:.2f}"))
        self._autosize_orders_columns()

    def _sort_orders_by(self, col: str) -> None:
        # Текущее направление
        direction = getattr(self, "_orders_sort_dir", {}).get(col, "asc")
        new_dir = "desc" if direction == "asc" else "asc"
        # Собираем все элементы и сортируем локально
        rows = []
        for iid in self.orders_tree.get_children(""):
            vals = self.orders_tree.item(iid, "values")
            rows.append((iid, vals))
        index_map = {"no": 0, "date": 1, "contract": 2, "product": 3, "total": 4}
        idx = index_map[col]

        def key_func(item):
            vals = item[1]
            val = vals[idx]
            if col == "no":
                try:
                    return int(val)
                except Exception:
                    return 0
            if col == "total":
                try:
                    return float(val.replace(" ", "").replace(",", "."))
                except Exception:
                    return 0.0
            if col == "date":
                # ДД.ММ.ГГГГ -> ГГГГММДД для корректной сортировки строкой
                try:
                    d, m, y = val.split(".")
                    return f"{y}{m}{d}"
                except Exception:
                    return val
            return val.casefold() if isinstance(val, str) else val

        rows.sort(key=key_func, reverse=(new_dir == "desc"))
        # Переставляем элементы
        for pos, (iid, _vals) in enumerate(rows):
            self.orders_tree.move(iid, "", pos)
        # Сохраняем направление для колонки
        if not hasattr(self, "_orders_sort_dir"):
            self._orders_sort_dir = {}
        self._orders_sort_dir[col] = new_dir

    def _on_order_select(self, _evt=None) -> None:
        sel = self.orders_tree.selection()
        if not sel:
            return
        work_order_id = int(sel[0])
        try:
            from services.work_orders import load_work_order  # lazy import
            with get_connection() as conn:
                data = load_work_order(conn, work_order_id)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось загрузить наряд: {exc}")
            return
        self._fill_form_from_loaded(data)

    def _fill_form_from_loaded(self, data) -> None:
        self.editing_order_id = data.id
        self._loaded_snapshot = data
        # визуально показать режим редактирования
        try:
            self.save_btn.configure(text="Сохранить изменения", fg_color="#2563eb")
        except Exception:
            pass
        self.date_var.set(data.date)
        # contract text
        with get_connection() as conn:
            c = conn.execute("SELECT code FROM contracts WHERE id=?", (data.contract_id,)).fetchone()
            p = conn.execute("SELECT name, product_no FROM products WHERE id=?", (data.product_id,)).fetchone() if data.product_id else None
        self.contract_entry.delete(0, "end")
        if c:
            self.contract_entry.insert(0, c["code"])  # display
        self.selected_contract_id = data.contract_id
        self.product_entry.delete(0, "end")
        if p:
            self.product_entry.insert(0, f"{p['product_no']} — {p['name']}")
        self.selected_product_id = data.product_id
        # items
        self._clear_items()
        for (job_type_id, name, qty, unit_price, line_amount) in data.items:
            self.item_rows.append(ItemRow(job_type_id=job_type_id, job_type_name=name, quantity=qty, unit_price=unit_price, line_amount=line_amount))
            # Render UI row
            row = ctk.CTkFrame(self.items_list)
            row.pack(fill="x", pady=2)
            for i, w in enumerate([6, 2, 2, 2, 1]):
                row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(row, text=name, anchor="w").grid(row=0, column=0, sticky="ew", padx=4)
            ctk.CTkLabel(row, text=str(qty)).grid(row=0, column=1, sticky="w", padx=4)
            ctk.CTkLabel(row, text=f"{unit_price:.2f}").grid(row=0, column=2, sticky="w", padx=4)
            ctk.CTkLabel(row, text=f"{line_amount:.2f}").grid(row=0, column=3, sticky="w", padx=4)
            del_btn = ctk.CTkButton(row, text="Удалить", width=80, fg_color="#b91c1c", hover_color="#7f1d1d")
            del_btn.grid(row=0, column=4, sticky="e", padx=4)
            idx = len(self.item_rows) - 1
            del_btn.configure(command=lambda i=idx, rf=row: self._remove_item_row(i, rf))
            row._del_btn = del_btn
        # workers
        self.selected_workers.clear()
        self.worker_amounts.clear()
        with get_connection() as conn:
            for wid, amount in data.workers:
                r = conn.execute("SELECT full_name FROM workers WHERE id=?", (wid,)).fetchone()
                self.selected_workers[wid] = r["full_name"] if r else str(wid)
                try:
                    self.worker_amounts[wid] = float(amount)
                except Exception:
                    self.worker_amounts[wid] = 0.0
        # Помечаем загруженные суммы как ручные, чтобы не перезаписывать
        self._manual_amount_ids = set(self.selected_workers.keys())
        self._refresh_workers_display()
        self._update_worker_amount_entries()
        self._update_totals()

    # ---- Save/Update/Delete ----
    def _build_input(self) -> Optional[WorkOrderInput]:
        if not self.item_rows:
            messagebox.showwarning("Проверка", "Добавьте хотя бы одну строку работ")
            return None
        if not self.selected_contract_id:
            messagebox.showwarning("Проверка", "Выберите контракт из подсказок")
            return None
        date_str = self.date_var.get().strip()
        try:
            validate_date(date_str)
        except Exception as exc:
            messagebox.showwarning("Проверка", str(exc))
            return None
        
        # Проверяем работников
        worker_ids = list(self.selected_workers.keys())
        if not worker_ids:
            messagebox.showwarning("Проверка", "Добавьте работников в бригаду")
            return None
        
        # Проверяем на дубликаты и некорректные ID
        unique_worker_ids = list(set(worker_ids))
        if len(unique_worker_ids) != len(worker_ids):
            messagebox.showwarning("Проверка", "Обнаружены дублирующиеся работники в бригаде")
            return None
        
        # Проверяем корректность ID
        for worker_id in unique_worker_ids:
            if not isinstance(worker_id, int):
                messagebox.showwarning("Проверка", f"Некорректный ID работника: {worker_id}")
                return None
            # Разрешаем отрицательные ID для ручно добавленных работников
            if worker_id > 0:
                # Для положительных ID проверяем существование в БД
                with get_connection() as conn:
                    exists = conn.execute("SELECT 1 FROM workers WHERE id = ?", (worker_id,)).fetchone()
                    if not exists:
                        messagebox.showwarning("Проверка", f"Работник с ID {worker_id} не найден в базе данных")
                        return None
        
        # Проверим, что виды работ выбраны корректно
        items: list[WorkOrderItemInput] = []
        for i in self.item_rows:
            if not i.job_type_id:
                messagebox.showwarning("Проверка", "Выберите вид работ из подсказок для каждой строки")
                return None
            items.append(WorkOrderItemInput(job_type_id=i.job_type_id, quantity=i.quantity))
        
        # Создаем список работников с именами и суммами
        workers: list[WorkOrderWorkerInput] = []
        for worker_id, worker_name in self.selected_workers.items():
            amount = self.worker_amounts.get(worker_id)
            workers.append(WorkOrderWorkerInput(worker_id=worker_id, worker_name=worker_name, amount=amount))
        
        return WorkOrderInput(
            date=date_str,
            product_id=self.selected_product_id,
            contract_id=int(self.selected_contract_id),
            items=items,
            workers=workers,  # Передаем работников с именами
        )

    def _save(self) -> None:
        if getattr(self, "_readonly", False):
            return
        
        wo = self._build_input()
        if not wo:
            return
        
        # Логируем данные для диагностики
        logger.info("Попытка сохранения наряда: работники=%s, контракт=%s, изделие=%s, строк=%d", 
                   [(w.worker_id, w.worker_name) for w in wo.workers], wo.contract_id, wo.product_id, len(wo.items))
        
        try:
            if self.editing_order_id:
                from services.work_orders import update_work_order  # lazy import
                with get_connection() as conn:
                    update_work_order(conn, self.editing_order_id, wo)
                messagebox.showinfo("Сохранено", "Наряд обновлен")
                logger.info("Наряд %s успешно обновлен", self.editing_order_id)
            else:
                with get_connection() as conn:
                    _id = create_work_order(conn, wo)
                messagebox.showinfo("Сохранено", "Наряд успешно сохранен")
                logger.info("Наряд %s успешно создан", _id)
        except sqlite3.IntegrityError as exc:
            logger.error("Ошибка целостности БД при сохранении наряда: %s", exc)
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {exc}")
            return
        except Exception as exc:
            logger.error("Неожиданная ошибка при сохранении наряда: %s", exc, exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось сохранить наряд: {exc}")
            return
        
        self._reset_form()
        self._load_recent_orders()

    def _delete(self) -> None:
        if getattr(self, "_readonly", False):
            return
        if not self.editing_order_id:
            messagebox.showwarning("Проверка", "Выберите наряд в списке справа")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный наряд?"):
            return
        try:
            from services.work_orders import delete_work_order  # lazy import
            with get_connection() as conn:
                delete_work_order(conn, self.editing_order_id)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось удалить наряд: {exc}")
            return
        messagebox.showinfo("Готово", "Наряд удален")
        self._reset_form()
        self._load_recent_orders()

    def _cancel_edit(self) -> None:
        self._reset_form()

    def _reset_form(self) -> None:
        self.editing_order_id = None
        self.selected_contract_id = None
        self.selected_product_id = None
        self.selected_workers.clear()
        self.item_rows.clear()
        self._manual_worker_counter = -1  # Сбрасываем счетчик ручных работников
        self._refresh_workers_display()
        for w in self.workers_list.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        for w in self.suggest_contract_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        for w in self.suggest_product_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        for w in self.suggest_job_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame.place_forget()
        self.suggest_job_frame.place_forget()
        self.date_var.set(dt.date.today().strftime(CONFIG.date_format))
        self.contract_entry.delete(0, "end")
        self.product_entry.delete(0, "end")
        self.qty_var.set("1")
        for child in self.items_list.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self._update_totals()
        # вернуть кнопку в обычный режим
        try:
            self.save_btn.configure(text="Сохранить", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])  # стандартный цвет темы
        except Exception:
            self.save_btn.configure(text="Сохранить")