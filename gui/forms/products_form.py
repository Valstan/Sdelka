from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from utils.readonly_ui import guard_readonly
from utils.export_ui import create_export_button
from services import reference_data as ref
from db import queries as q
from services import suggestions
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry,
    create_suggestion_button,
    create_suggestions_frame,
)
import logging


class ProductsForm(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self._selected_id: int | None = None
        self._snapshot: tuple[str, str, int | None] | None = None
        self._build_ui()
        self._load()
        # Обновлять список при импорте
        try:
            self.bind("<<DataImported>>", lambda e: self._load())
            self.winfo_toplevel().bind(
                "<<DataImported>>", lambda e: self._load(), add="+"
            )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _build_ui(self) -> None:
        # No top spacer/banners to avoid empty gaps

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        self.name_var = ctk.StringVar()
        self.no_var = ctk.StringVar()
        self.contract_var = ctk.StringVar()
        self.selected_contract_id: int | None = None

        ctk.CTkLabel(form, text="Наименование").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=360)
        self.name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.name_entry.bind("<KeyRelease>", self._on_name_key)
        self.name_entry.bind("<FocusIn>", lambda e: self._on_name_key())
        self.name_entry.bind("<Button-1>", lambda e: self.after(1, self._on_name_key))

        ctk.CTkLabel(form, text="Номер изделия").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.no_entry = ctk.CTkEntry(form, textvariable=self.no_var, width=200)
        self.no_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.no_entry.bind("<KeyRelease>", self._on_no_key)
        self.no_entry.bind("<FocusIn>", lambda e: self._on_no_key())
        self.no_entry.bind("<Button-1>", lambda e: self.after(1, self._on_no_key))

        ctk.CTkLabel(form, text="Контракт").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.contract_entry = ctk.CTkEntry(
            form, textvariable=self.contract_var, width=360
        )
        self.contract_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)
        self.contract_entry.bind("<FocusIn>", lambda e: self._on_contract_key())
        self.contract_entry.bind(
            "<Button-1>", lambda e: self.after(1, self._on_contract_key)
        )

        btns = ctk.CTkFrame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        save_btn = ctk.CTkButton(btns, text="Сохранить", command=self._save)
        cancel_btn = ctk.CTkButton(
            btns, text="Отмена", command=self._cancel, fg_color="#6b7280"
        )
        clear_btn = ctk.CTkButton(btns, text="Очистить", command=self._clear)
        del_btn = ctk.CTkButton(
            btns,
            text="Удалить",
            fg_color="#b91c1c",
            hover_color="#7f1d1d",
            command=self._delete,
        )
        for b in (save_btn, cancel_btn, clear_btn, del_btn):
            b.pack(side="left", padx=5)
        export_btn = create_export_button(btns, "products", "Экспорт изделий")
        export_btn.pack(side="right")
        if self._readonly:
            for w in (self.name_entry, self.no_entry, self.contract_entry):
                try:
                    w.configure(state="disabled")
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
            for b in (save_btn, cancel_btn, clear_btn, del_btn):
                b.configure(state="disabled")

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("name", "product_no", "contract_code"),
            show="headings",
        )
        self.tree.heading("name", text="Наименование")
        self.tree.heading("product_no", text="Номер изделия")
        self.tree.heading("contract_code", text="Контракт")
        self.tree.column("name", width=420)
        self.tree.column("product_no", width=200)
        self.tree.column("contract_code", width=180)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.suggest_name_frame = create_suggestions_frame(self)
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame = create_suggestions_frame(self)
        self.suggest_no_frame.place_forget()
        self.suggest_contract_frame = create_suggestions_frame(self)
        self.suggest_contract_frame.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

    def _on_name_key(self, _evt=None) -> None:
        prefix = self.name_var.get().strip()
        for w in self.suggest_name_frame.winfo_children():
            w.destroy()

        place_suggestions_under_entry(self.name_entry, self.suggest_name_frame, self)

        with get_connection() as conn:
            rows = q.list_products(conn, prefix or None, CONFIG.autocomplete_limit)
        vals = [r["name"] for r in rows]

        shown = 0
        for val in vals:
            create_suggestion_button(
                self.suggest_name_frame,
                text=val,
                command=lambda s=val: self._pick_name(s),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1

        for label in get_recent("products.name", prefix, CONFIG.autocomplete_limit):
            if label not in vals:
                create_suggestion_button(
                    self.suggest_name_frame,
                    text=label,
                    command=lambda s=label: self._pick_name(s),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

        # Если нет данных из БД и истории, показываем все изделия
        if shown == 0:
            with get_connection() as conn:
                all_products = q.list_products(conn, None, CONFIG.autocomplete_limit)
            for row in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_name_frame,
                    text=row["name"],
                    command=lambda s=row["name"]: self._pick_name(s),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _on_no_key(self, _evt=None) -> None:
        prefix = self.no_var.get().strip()
        for w in self.suggest_no_frame.winfo_children():
            w.destroy()

        place_suggestions_under_entry(self.no_entry, self.suggest_no_frame, self)

        with get_connection() as conn:
            rows = q.search_products_by_prefix(conn, prefix, CONFIG.autocomplete_limit)
        vals = [r["product_no"] for r in rows]

        shown = 0
        for val in vals:
            create_suggestion_button(
                self.suggest_no_frame, text=val, command=lambda s=val: self._pick_no(s)
            ).pack(fill="x", padx=2, pady=1)
            shown += 1

        for label in get_recent(
            "products.product_no", prefix, CONFIG.autocomplete_limit
        ):
            if label not in vals:
                create_suggestion_button(
                    self.suggest_no_frame,
                    text=label,
                    command=lambda s=label: self._pick_no(s),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

        # Если нет данных из БД и истории, показываем все номера изделий
        if shown == 0:
            with get_connection() as conn:
                all_products = q.search_products_by_prefix(
                    conn, "", CONFIG.autocomplete_limit
                )
            for row in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_no_frame,
                    text=row["product_no"],
                    command=lambda s=row["product_no"]: self._pick_no(s),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

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
        for frame in (
            self.suggest_name_frame,
            self.suggest_no_frame,
            self.suggest_contract_frame,
        ):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame.place_forget()
        self.suggest_contract_frame.place_forget()

    def _load(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_connection() as conn:
            rows = ref.list_products(conn)
        for r in rows:
            try:
                cc = r["contract_code"]
            except Exception:
                try:
                    cc = r.get("contract_code")  # type: ignore[attr-defined]
                except Exception:
                    cc = ""
            self.tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(r["name"], r["product_no"], cc or ""),
            )

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        vals = self.tree.item(sel[0], "values")
        name = vals[0]
        product_no = vals[1]
        contract_code = vals[2] if len(vals) > 2 else ""
        self.name_var.set(name)
        self.no_var.set(product_no)
        self.contract_var.set(contract_code)
        # Resolve selected_contract_id by code
        self.selected_contract_id = None
        try:
            with get_connection() as conn:
                if contract_code:
                    row = conn.execute(
                        "SELECT id FROM contracts WHERE code_norm = ?",
                        (contract_code.casefold(),),
                    ).fetchone()
                    if row:
                        self.selected_contract_id = int(
                            row["id"] if isinstance(row, dict) else row[0]
                        )
        except Exception:
            self.selected_contract_id = None
        self._snapshot = (name, product_no, self.selected_contract_id)

    def _clear(self) -> None:
        self._selected_id = None
        self._snapshot = None
        self.name_var.set("")
        self.no_var.set("")
        self.contract_var.set("")
        self.selected_contract_id = None
        self.tree.selection_remove(self.tree.selection())
        self.suggest_name_frame.place_forget()
        self.suggest_no_frame.place_forget()
        self.suggest_contract_frame.place_forget()

    def _cancel(self) -> None:
        self._clear()

    def _save(self) -> None:

        if not guard_readonly("сохранение"):
            return
        name = self.name_var.get().strip()
        no = self.no_var.get().strip()
        contract_label = self.contract_var.get().strip()
        if not name or not no:
            messagebox.showwarning("Проверка", "Заполните наименование и номер изделия")
            return
        # Resolve/ensure single contract by code
        contract_id: int | None = None
        if contract_label:
            try:
                with get_connection() as conn:
                    row = conn.execute(
                        "SELECT id FROM contracts WHERE code_norm = ?",
                        (contract_label.casefold(),),
                    ).fetchone()
                    if row:
                        contract_id = int(
                            row["id"] if isinstance(row, dict) else row[0]
                        )
                    else:
                        q.upsert_contract(conn, contract_label, None, None, None)
                        row2 = conn.execute(
                            "SELECT id FROM contracts WHERE code_norm = ?",
                            (contract_label.casefold(),),
                        ).fetchone()
                        if row2:
                            contract_id = int(
                                row2["id"] if isinstance(row2, dict) else row2[0]
                            )
            except Exception:
                contract_id = None
        try:
            with get_connection() as conn:
                if self._selected_id:
                    ref.save_product(conn, self._selected_id, name, no, contract_id)
                else:
                    if q.get_product_by_name(conn, name) or q.get_product_by_no(
                        conn, no
                    ):
                        messagebox.showwarning(
                            "Дубликат",
                            "Изделие уже существует. Выберите его для редактирования.",
                        )
                        return
                    ref.create_product(conn, name, no, contract_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load()
        self._clear()

    def _delete(self) -> None:

        if not guard_readonly("удаление"):
            return
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранное изделие?"):
            return
        try:
            with get_connection() as conn:
                ref.delete_product(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load()
        self._clear()

    def _on_contract_key(self, _evt=None) -> None:
        prefix = self.contract_var.get().strip()
        for w in self.suggest_contract_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        place_suggestions_under_entry(
            self.contract_entry, self.suggest_contract_frame, self
        )
        with get_connection() as conn:
            rows = suggestions.suggest_contracts(
                conn, prefix, CONFIG.autocomplete_limit
            )
        shown = 0
        for _id, label in rows:
            create_suggestion_button(
                self.suggest_contract_frame,
                text=label,
                command=lambda i=_id, l=label: self._pick_contract(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        for label in get_recent("products.contract", prefix, CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(
                    self.suggest_contract_frame,
                    text=label,
                    command=lambda l=label: self._pick_contract(
                        self.selected_contract_id or 0, l
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        if shown == 0:
            with get_connection() as conn:
                all_rows = suggestions.suggest_contracts(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_rows:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_contract_frame,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_contract(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_contract(self, contract_id: int, label: str) -> None:
        try:
            self.selected_contract_id = int(contract_id) if contract_id else None
        except Exception:
            self.selected_contract_id = None
        self.contract_var.set(label)
        record_use("products.contract", label)
        self.suggest_contract_frame.place_forget()

    def _export_products(self) -> None:
        pass
