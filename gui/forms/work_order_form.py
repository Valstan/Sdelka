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

        self._build_ui()
        self._update_totals()

    def _build_ui(self) -> None:
        # Header form
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        # Date
        self.date_var = ctk.StringVar(value=dt.date.today().strftime(CONFIG.date_format))
        ctk.CTkLabel(header, text="Дата").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = ctk.CTkEntry(header, textvariable=self.date_var, width=120)
        self.date_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.date_quick_btn = ctk.CTkButton(header, text="Выбрать дату", width=120, command=self._show_date_quick)
        self.date_quick_btn.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Contract
        ctk.CTkLabel(header, text="Контракт").grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.contract_entry = ctk.CTkEntry(header, placeholder_text="Начните вводить шифр", width=180)
        self.contract_entry.grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)

        # Product
        ctk.CTkLabel(header, text="Изделие").grid(row=0, column=5, sticky="w", padx=5, pady=5)
        self.product_entry = ctk.CTkEntry(header, placeholder_text="Номер/Название", width=220)
        self.product_entry.grid(row=0, column=6, sticky="w", padx=5, pady=5)
        self.product_entry.bind("<KeyRelease>", self._on_product_key)

        # Suggestion frames
        self.suggest_contract_frame = ctk.CTkFrame(self)
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame = ctk.CTkFrame(self)
        self.suggest_product_frame.place_forget()

        # Items section
        items_frame = ctk.CTkFrame(self)
        items_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(items_frame, text="Вид работ").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.job_entry = ctk.CTkEntry(items_frame, placeholder_text="Начните ввод", width=280)
        self.job_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.job_entry.bind("<KeyRelease>", self._on_job_key)

        ctk.CTkLabel(items_frame, text="Кол-во").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.qty_var = ctk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(items_frame, textvariable=self.qty_var, width=80)
        self.qty_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(items_frame, text="Добавить", command=self._add_item).grid(row=0, column=4, sticky="w", padx=5, pady=5)

        self.suggest_job_frame = ctk.CTkFrame(self)
        self.suggest_job_frame.place_forget()

        # Items table
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.items_tree = ttk.Treeview(table_frame, columns=("job", "qty", "price", "amount"), show="headings")
        self.items_tree.heading("job", text="Вид работ")
        self.items_tree.heading("qty", text="Количество")
        self.items_tree.heading("price", text="Цена")
        self.items_tree.heading("amount", text="Сумма")
        self.items_tree.column("job", width=360)
        self.items_tree.column("qty", width=100)
        self.items_tree.column("price", width=120)
        self.items_tree.column("amount", width=140)
        self.items_tree.pack(side="left", fill="both", expand=True)

        btns_col = ctk.CTkFrame(table_frame)
        btns_col.pack(side="left", fill="y", padx=8)
        ctk.CTkButton(btns_col, text="Удалить строку", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._remove_item).pack(pady=4)
        ctk.CTkButton(btns_col, text="Очистить", command=self._clear_items).pack(pady=4)

        # Workers section
        workers_frame = ctk.CTkFrame(self)
        workers_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(workers_frame, text="Работник").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.worker_entry = ctk.CTkEntry(workers_frame, placeholder_text="Начните ввод ФИО", width=300)
        self.worker_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.worker_entry.bind("<KeyRelease>", self._on_worker_key)
        ctk.CTkButton(workers_frame, text="Добавить", command=self._add_worker).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.suggest_worker_frame = ctk.CTkFrame(self)
        self.suggest_worker_frame.place_forget()

        self.workers_list = ctk.CTkScrollableFrame(self, height=120)
        self.workers_list.pack(fill="x", padx=10)

        # Totals and Save
        totals_frame = ctk.CTkFrame(self)
        totals_frame.pack(fill="x", padx=10, pady=10)

        self.total_var = ctk.StringVar(value="0.00")
        self.per_worker_var = ctk.StringVar(value="0.00")

        ctk.CTkLabel(totals_frame, text="Итог, руб:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(totals_frame, textvariable=self.total_var).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(totals_frame, text="На одного, руб:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(totals_frame, textvariable=self.per_worker_var).grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(totals_frame, text="Сохранить наряд", command=self._save).grid(row=0, column=4, padx=10, pady=5)

    # ---- Suggestions ----
    def _place_suggest_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        x = entry.winfo_rootx() - self.winfo_rootx()
        y = entry.winfo_rooty() - self.winfo_rooty() + entry.winfo_height()
        frame.place(x=x, y=y)

    def _on_contract_key(self, _evt=None) -> None:
        for w in self.suggest_contract_frame.winfo_children():
            w.destroy()
        text = self.contract_entry.get().strip()
        if not text:
            self.suggest_contract_frame.place_forget()
            self.selected_contract_id = None
            return
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_contracts(conn, text, CONFIG.autocomplete_limit)
        if not rows:
            self.suggest_contract_frame.place_forget()
            return
        self._place_suggest_under(self.contract_entry, self.suggest_contract_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_contract_frame, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)

    def _pick_contract(self, contract_id: int, label: str) -> None:
        self.selected_contract_id = contract_id
        self.contract_entry.delete(0, "end")
        self.contract_entry.insert(0, label)
        self.suggest_contract_frame.place_forget()

    def _on_product_key(self, _evt=None) -> None:
        for w in self.suggest_product_frame.winfo_children():
            w.destroy()
        text = self.product_entry.get().strip()
        if not text:
            self.suggest_product_frame.place_forget()
            self.selected_product_id = None
            return
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_products(conn, text, CONFIG.autocomplete_limit)
        if not rows:
            self.suggest_product_frame.place_forget()
            return
        self._place_suggest_under(self.product_entry, self.suggest_product_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_product_frame, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)

    def _pick_product(self, product_id: int, label: str) -> None:
        self.selected_product_id = product_id
        self.product_entry.delete(0, "end")
        self.product_entry.insert(0, label)
        self.suggest_product_frame.place_forget()

    def _on_job_key(self, _evt=None) -> None:
        for w in self.suggest_job_frame.winfo_children():
            w.destroy()
        text = self.job_entry.get().strip()
        if not text:
            self.suggest_job_frame.place_forget()
            return
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_job_types(conn, text, CONFIG.autocomplete_limit)
        if not rows:
            self.suggest_job_frame.place_forget()
            return
        self._place_suggest_under(self.job_entry, self.suggest_job_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_job_frame, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)

    def _pick_job(self, job_type_id: int, label: str) -> None:
        self.job_entry.delete(0, "end")
        self.job_entry.insert(0, label)
        self.job_entry._selected_job_id = job_type_id  # attach attribute for temporary storage
        self.suggest_job_frame.place_forget()

    def _on_worker_key(self, _evt=None) -> None:
        for w in self.suggest_worker_frame.winfo_children():
            w.destroy()
        text = self.worker_entry.get().strip()
        if not text:
            self.suggest_worker_frame.place_forget()
            return
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_workers(conn, text, CONFIG.autocomplete_limit)
        if not rows:
            self.suggest_worker_frame.place_forget()
            return
        self._place_suggest_under(self.worker_entry, self.suggest_worker_frame)
        for _id, label in rows:
            ctk.CTkButton(self.suggest_worker_frame, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)

    def _pick_worker(self, worker_id: int, label: str) -> None:
        self.worker_entry.delete(0, "end")
        self.worker_entry.insert(0, label)
        self._add_worker(worker_id, label)
        self.suggest_worker_frame.place_forget()

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

        # Fetch current unit price
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
        self.items_tree.insert("", "end", values=(name, qty, f"{unit_price:.2f}", f"{amount:.2f}"))

        # Reset entry
        self.job_entry.delete(0, "end")
        if hasattr(self.job_entry, "_selected_job_id"):
            delattr(self.job_entry, "_selected_job_id")
        self.qty_var.set("1")

        self._update_totals()

    def _remove_item(self) -> None:
        sel = self.items_tree.selection()
        if not sel:
            return
        index = self.items_tree.index(sel[0])
        self.items_tree.delete(sel[0])
        if 0 <= index < len(self.item_rows):
            self.item_rows.pop(index)
        self._update_totals()

    def _clear_items(self) -> None:
        for iid in self.items_tree.get_children():
            self.items_tree.delete(iid)
        self.item_rows.clear()
        self._update_totals()

    def _add_worker(self, worker_id: Optional[int] = None, label: Optional[str] = None) -> None:
        if worker_id is None:
            # if user typed manually and pressed button, do nothing without selection
            return
        if worker_id in self.selected_workers:
            return
        self.selected_workers[worker_id] = label or ""
        # Rebuild list
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
            self._add_worker()  # rebuild

    def _update_totals(self) -> None:
        total = sum(i.line_amount for i in self.item_rows)
        num_workers = max(1, len(self.selected_workers))
        per_worker = total / num_workers if num_workers else 0.0
        self.total_var.set(f"{total:.2f}")
        self.per_worker_var.set(f"{per_worker:.2f}")

    def _show_date_quick(self) -> None:
        # Simple dropdown with last 7 days
        frame = ctk.CTkFrame(self)
        x = self.date_entry.winfo_rootx() - self.winfo_rootx()
        y = self.date_entry.winfo_rooty() - self.winfo_rooty() + self.date_entry.winfo_height()
        frame.place(x=x, y=y)
        for i in range(7):
            d = (dt.date.today() - dt.timedelta(days=i)).strftime(CONFIG.date_format)
            ctk.CTkButton(frame, text=d, command=lambda s=d, f=frame: self._pick_date(s, f)).pack(fill="x")

    def _pick_date(self, date_str: str, frame: ctk.CTkFrame) -> None:
        self.date_var.set(date_str)
        frame.place_forget()

    # ---- Save ----
    def _save(self) -> None:
        if not self.item_rows:
            messagebox.showwarning("Проверка", "Добавьте хотя бы одну строку работ")
            return
        if not self.selected_contract_id:
            messagebox.showwarning("Проверка", "Выберите контракт из подсказок")
            return
        date_str = self.date_var.get().strip()
        try:
            validate_date(date_str)
        except Exception as exc:
            messagebox.showwarning("Проверка", str(exc))
            return
        worker_ids = list(self.selected_workers.keys())
        if not worker_ids:
            messagebox.showwarning("Проверка", "Добавьте работников в бригаду")
            return

        # Build WorkOrderInput
        items = [WorkOrderItemInput(job_type_id=i.job_type_id, quantity=i.quantity) for i in self.item_rows]
        wo = WorkOrderInput(
            date=date_str,
            product_id=self.selected_product_id,
            contract_id=int(self.selected_contract_id),
            items=items,
            worker_ids=worker_ids,
        )

        try:
            with get_connection(CONFIG.db_path) as conn:
                _id = create_work_order(conn, wo)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {exc}")
            return
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось сохранить наряд: {exc}")
            return

        messagebox.showinfo("Сохранено", "Наряд успешно сохранен")
        self._reset_form()

    def _reset_form(self) -> None:
        self.selected_contract_id = None
        self.selected_product_id = None
        self.selected_workers.clear()
        self.item_rows.clear()
        self.date_var.set(dt.date.today().strftime(CONFIG.date_format))
        self.contract_entry.delete(0, "end")
        self.product_entry.delete(0, "end")
        for iid in self.items_tree.get_children():
            self.items_tree.delete(iid)
        for w in self.workers_list.winfo_children():
            w.destroy()
        self._update_totals()