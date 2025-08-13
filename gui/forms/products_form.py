from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import reference_data as ref
from db import queries as q
from services import suggestions
from utils.usage_history import record_use, get_recent


class ProductsForm(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._selected_id: int | None = None
        self._snapshot: tuple[str, str] | None = None
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        self.name_var = ctk.StringVar()
        self.no_var = ctk.StringVar()

        ctk.CTkLabel(form, text="Наименование").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=360)
        self.name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.name_entry.bind("<KeyRelease>", self._on_name_key)
        self.name_entry.bind("<FocusIn>", lambda e: self._on_name_key())
        self.name_entry.bind("<Button-1>", lambda e: self.after(1, self._on_name_key))

        ctk.CTkLabel(form, text="Номер изделия").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.no_entry = ctk.CTkEntry(form, textvariable=self.no_var, width=200)
        self.no_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.no_entry.bind("<KeyRelease>", self._on_no_key)
        self.no_entry.bind("<FocusIn>", lambda e: self._on_no_key())
        self.no_entry.bind("<Button-1>", lambda e: self.after(1, self._on_no_key))

        btns = ctk.CTkFrame(form)
        btns.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        ctk.CTkButton(btns, text="Сохранить", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Отмена", command=self._cancel, fg_color="#6b7280").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Очистить", command=self._clear).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete).pack(side="left", padx=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("name", "product_no"), show="headings")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("product_no", text="Номер изделия")
        self.tree.column("name", width=420)
        self.tree.column("product_no", width=200)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.suggest_name_frame = ctk.CTkFrame(self)
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame = ctk.CTkFrame(self)
        self.suggest_no_frame.place_forget()

        # Глобальный клик — скрыть подсказки, если клик вне списков
        self.bind_all("<Button-1>", self._on_global_click, add="+")

    def _on_name_key(self, _evt=None) -> None:
        prefix = self.name_var.get().strip()
        for w in self.suggest_name_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = q.list_products(conn, prefix or None, CONFIG.autocomplete_limit)
        vals = [r["name"] for r in rows]
        x = self.name_entry.winfo_rootx() - self.winfo_rootx()
        y = self.name_entry.winfo_rooty() - self.winfo_rooty() + self.name_entry.winfo_height()
        self.suggest_name_frame.place(x=x, y=y)
        for val in vals:
            ctk.CTkButton(self.suggest_name_frame, text=val, command=lambda s=val: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("products.name", prefix, CONFIG.autocomplete_limit):
            if label not in vals:
                ctk.CTkButton(self.suggest_name_frame, text=label, command=lambda s=label: self._pick_name(s)).pack(fill="x", padx=2, pady=1)

    def _on_no_key(self, _evt=None) -> None:
        prefix = self.no_var.get().strip()
        for w in self.suggest_no_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = q.search_products_by_prefix(conn, prefix, CONFIG.autocomplete_limit)
        vals = [r["product_no"] for r in rows]
        x = self.no_entry.winfo_rootx() - self.winfo_rootx()
        y = self.no_entry.winfo_rooty() - self.winfo_rooty() + self.no_entry.winfo_height()
        self.suggest_no_frame.place(x=x, y=y)
        for val in vals:
            ctk.CTkButton(self.suggest_no_frame, text=val, command=lambda s=val: self._pick_no(s)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("products.product_no", prefix, CONFIG.autocomplete_limit):
            if label not in vals:
                ctk.CTkButton(self.suggest_no_frame, text=label, command=lambda s=label: self._pick_no(s)).pack(fill="x", padx=2, pady=1)

    def _pick_name(self, val: str) -> None:
        self.name_var.set(val)
        record_use("products.name", val)
        self.suggest_name_frame.place_forget()

    def _pick_no(self, val: str) -> None:
        self.no_var.set(val)
        record_use("products.product_no", val)
        self.suggest_no_frame.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self.suggest_name_frame.place_forget()
            self.suggest_no_frame.place_forget()
            return
        for frame in (self.suggest_name_frame, self.suggest_no_frame):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame.place_forget()

    def _load(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_connection(CONFIG.db_path) as conn:
            rows = ref.list_products(conn)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["product_no"]))

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        name, product_no = self.tree.item(sel[0], "values")
        self.name_var.set(name)
        self.no_var.set(product_no)
        self._snapshot = (name, product_no)

    def _clear(self) -> None:
        self._selected_id = None
        self._snapshot = None
        self.name_var.set("")
        self.no_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame.place_forget()

    def _cancel(self) -> None:
        self._clear()

    def _save(self) -> None:
        name = self.name_var.get().strip()
        no = self.no_var.get().strip()
        if not name or not no:
            messagebox.showwarning("Проверка", "Заполните наименование и номер изделия")
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                if self._selected_id:
                    ref.save_product(conn, self._selected_id, name, no)
                else:
                    if q.get_product_by_name(conn, name) or q.get_product_by_no(conn, no):
                        messagebox.showwarning("Дубликат", "Изделие уже существует. Выберите его для редактирования.")
                        return
                    ref.create_product(conn, name, no)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load()
        self._clear()

    def _delete(self) -> None:
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранное изделие?"):
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                ref.delete_product(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load()
        self._clear()