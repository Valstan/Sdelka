from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import suggestions
from services.work_orders import WorkOrderInput, WorkOrderItemInput, create_work_order
from services.validation import validate_date
from db import queries as q
from gui.widgets.date_picker import DatePicker
from utils.usage_history import record_use, get_recent


@dataclass
class ItemRow:
    job_type_id: int
    job_type_name: str
    quantity: float
    unit_price: float
    line_amount: float


class WorkOrdersForm(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.selected_contract_id: Optional[int] = None
        self.selected_product_id: Optional[int] = None
        self.selected_workers: dict[int, str] = {}
        self.item_rows: list[ItemRow] = []
        self.editing_order_id: Optional[int] = None

        self._build_ui()
        self._update_totals()
        self._load_recent_orders()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self)
        container.pack(expand=True, fill="both")
        # Сетка для пропорций 65% (левая часть) / 35% (правая часть)
        try:
            container.grid_columnconfigure(0, weight=65)
            container.grid_columnconfigure(1, weight=35)
            container.grid_rowconfigure(0, weight=1)
        except Exception:
            pass

        # Left side (form)
        left = ctk.CTkFrame(container)
        left.grid(row=0, column=0, sticky="nsew")
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

        # Right side (orders list)
        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, sticky="nsew")

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
        self.date_entry.bind("<Button-1>", lambda e: self.after(1, self._open_date_picker))

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
        self.suggest_contract_frame = ctk.CTkFrame(self)
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame = ctk.CTkFrame(self)
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

        self.suggest_job_frame = ctk.CTkFrame(self)
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
        ctk.CTkButton(workers_frame, text="Добавить", command=self._add_worker).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.suggest_worker_frame = ctk.CTkFrame(self)
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
        self.filter_from_entry.bind("<Button-1>", lambda e: self.after(1, lambda: self._open_date_picker_for(self.filter_from, self.filter_from_entry)))
        ctk.CTkLabel(filter_frame, text="по").pack(side="left", padx=2)
        self.filter_to_entry = ctk.CTkEntry(filter_frame, textvariable=self.filter_to, width=100)
        self.filter_to_entry.pack(side="left")
        self.filter_to_entry.bind("<FocusIn>", lambda e: self._open_date_picker_for(self.filter_to, self.filter_to_entry))
        self.filter_to_entry.bind("<Button-1>", lambda e: self.after(1, lambda: self._open_date_picker_for(self.filter_to, self.filter_to_entry)))
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
        x = entry.winfo_rootx() - self.winfo_rootx()
        y = entry.winfo_rooty() - self.winfo_rooty() + entry.winfo_height()
        frame.place(x=x, y=y)
        frame.lift()

    def _on_contract_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_contract_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_contracts(conn, self.contract_entry.get().strip(), CONFIG.autocomplete_limit)
        self._place_suggest_under(self.contract_entry, self.suggest_contract_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_contract_frame, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("work_orders.contract", self.contract_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                ctk.CTkButton(self.suggest_contract_frame, text=label, command=lambda l=label: self._pick_contract(self.selected_contract_id or 0, l)).pack(fill="x", padx=2, pady=1)

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
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_products(conn, self.product_entry.get().strip(), CONFIG.autocomplete_limit)
        self._place_suggest_under(self.product_entry, self.suggest_product_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_product_frame, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("work_orders.product", self.product_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                ctk.CTkButton(self.suggest_product_frame, text=label, command=lambda l=label: self._pick_product(self.selected_product_id or 0, l)).pack(fill="x", padx=2, pady=1)

    def _pick_product(self, product_id: int, label: str) -> None:
        self.selected_product_id = product_id
        self.product_entry.delete(0, "end")
        self.product_entry.insert(0, label)
        record_use("work_orders.product", label)
        self.suggest_product_frame.place_forget()

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_job_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_job_types(conn, self.job_entry.get().strip(), CONFIG.autocomplete_limit)
        self._place_suggest_under(self.job_entry, self.suggest_job_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_job_frame, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("work_orders.job_type", self.job_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                ctk.CTkButton(self.suggest_job_frame, text=label, command=lambda l=label: self._pick_job(getattr(self.job_entry, "_selected_job_id", 0) or 0, l)).pack(fill="x", padx=2, pady=1)

    def _pick_job(self, job_type_id: int, label: str) -> None:
        self.job_entry.delete(0, "end")
        self.job_entry.insert(0, label)
        self.job_entry._selected_job_id = job_type_id
        record_use("work_orders.job_type", label)
        self.suggest_job_frame.place_forget()

    def _on_worker_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_worker_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_workers(conn, self.worker_entry.get().strip(), CONFIG.autocomplete_limit)
        self._place_suggest_under(self.worker_entry, self.suggest_worker_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_worker_frame, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("work_orders.worker", self.worker_entry.get().strip(), CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                ctk.CTkButton(self.suggest_worker_frame, text=label, command=lambda l=label: self._pick_worker(0, l)).pack(fill="x", padx=2, pady=1)

    def _pick_worker(self, worker_id: int, label: str) -> None:
        self.worker_entry.delete(0, "end")
        self.worker_entry.insert(0, label)
        record_use("work_orders.worker", label)
        self._add_worker(worker_id, label)
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

        with get_connection(CONFIG.db_path) as conn:
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
        if worker_id in self.selected_workers:
            return
        self.selected_workers[worker_id] = label or ""
        for w in self.workers_list.winfo_children():
            w.destroy()
        for wid, name in self.selected_workers.items():
            row = ctk.CTkFrame(self.workers_list)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=name).pack(side="left")
            ctk.CTkButton(row, text="Удалить", width=80, fg_color="#b91c1c", hover_color="#7f1d1d", command=lambda i=wid: self._remove_worker(i)).pack(side="right")
        self._update_totals()

    def _remove_worker(self, worker_id: int) -> None:
        if worker_id in self.selected_workers:
            del self.selected_workers[worker_id]
            self._add_worker()

    def _update_totals(self) -> None:
        total = sum(i.line_amount for i in self.item_rows)
        num_workers = max(1, len(self.selected_workers))
        per_worker = total / num_workers if num_workers else 0.0
        self.total_var.set(f"{total:.2f}")
        self.per_worker_var.set(f"{per_worker:.2f}")

    def _open_date_picker(self) -> None:
        self._hide_all_suggests()
        DatePicker(self, self.date_var.get().strip(), lambda d: self.date_var.set(d), anchor=self.date_entry)

    def _open_date_picker_for(self, var, anchor=None) -> None:
        self._hide_all_suggests()
        DatePicker(self, var.get().strip(), lambda d: var.set(d), anchor=anchor)

    # ---- Orders list ----
    def _load_recent_orders(self) -> None:
        for iid in getattr(self, "_order_rows", []):
            try:
                self.orders_tree.delete(iid)
            except Exception:
                pass
        self._order_rows = []
        with get_connection(CONFIG.db_path) as conn:
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
        with get_connection(CONFIG.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
        for r in rows:
            self.orders_tree.insert("", "end", iid=str(r["id"]), values=(r["order_no"], r["date"], r["code"] or "", r["name"] or "", f"{r['total_amount']:.2f}"))

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
            with get_connection(CONFIG.db_path) as conn:
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
        with get_connection(CONFIG.db_path) as conn:
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
        with get_connection(CONFIG.db_path) as conn:
            for wid in data.worker_ids:
                r = conn.execute("SELECT full_name FROM workers WHERE id=?", (wid,)).fetchone()
                self.selected_workers[wid] = r["full_name"] if r else str(wid)
        for w in self.workers_list.winfo_children():
            w.destroy()
        for wid, name in self.selected_workers.items():
            row = ctk.CTkFrame(self.workers_list)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=name).pack(side="left")
            ctk.CTkButton(row, text="Удалить", width=80, fg_color="#b91c1c", hover_color="#7f1d1d", command=lambda i=wid: self._remove_worker(i)).pack(side="right")
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
        worker_ids = list(self.selected_workers.keys())
        if not worker_ids:
            messagebox.showwarning("Проверка", "Добавьте работников в бригаду")
            return None
        items = [WorkOrderItemInput(job_type_id=i.job_type_id, quantity=i.quantity) for i in self.item_rows]
        return WorkOrderInput(
            date=date_str,
            product_id=self.selected_product_id,
            contract_id=int(self.selected_contract_id),
            items=items,
            worker_ids=worker_ids,
        )

    def _save(self) -> None:
        wo = self._build_input()
        if not wo:
            return
        try:
            if self.editing_order_id:
                from services.work_orders import update_work_order  # lazy import
                with get_connection(CONFIG.db_path) as conn:
                    update_work_order(conn, self.editing_order_id, wo)
                messagebox.showinfo("Сохранено", "Наряд обновлен")
            else:
                with get_connection(CONFIG.db_path) as conn:
                    _id = create_work_order(conn, wo)
                messagebox.showinfo("Сохранено", "Наряд успешно сохранен")
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {exc}")
            return
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось сохранить наряд: {exc}")
            return
        self._reset_form()
        self._load_recent_orders()

    def _delete(self) -> None:
        if not self.editing_order_id:
            messagebox.showwarning("Проверка", "Выберите наряд в списке справа")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный наряд?"):
            return
        try:
            from services.work_orders import delete_work_order  # lazy import
            with get_connection(CONFIG.db_path) as conn:
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
        for w in self.workers_list.winfo_children():
            w.destroy()
        for w in self.suggest_contract_frame.winfo_children():
            w.destroy()
        for w in self.suggest_product_frame.winfo_children():
            w.destroy()
        for w in self.suggest_job_frame.winfo_children():
            w.destroy()
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