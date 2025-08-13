from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import reference_data as ref
from db import queries as q
from utils.usage_history import record_use, get_recent


class ContractsForm(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._selected_id: int | None = None
        self._snapshot: tuple[str, str | None, str | None, str | None] | None = None
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        self.code_var = ctk.StringVar()
        self.start_var = ctk.StringVar()
        self.end_var = ctk.StringVar()
        self.desc_var = ctk.StringVar()

        ctk.CTkLabel(form, text="Шифр контракта").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.code_entry = ctk.CTkEntry(form, textvariable=self.code_var, width=240)
        self.code_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.code_entry.bind("<KeyRelease>", self._on_code_key)
        self.code_entry.bind("<FocusIn>", lambda e: self._on_code_key())
        self.code_entry.bind("<Button-1>", lambda e: self.after(1, self._on_code_key))

        ctk.CTkLabel(form, text="Дата начала (ДД.ММ.ГГГГ)").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.start_entry = ctk.CTkEntry(form, textvariable=self.start_var, width=120)
        self.start_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.start_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.start_var, self.start_entry))

        ctk.CTkLabel(form, text="Дата окончания").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.end_entry = ctk.CTkEntry(form, textvariable=self.end_var, width=120)
        self.end_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.end_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.end_var, self.end_entry))

        ctk.CTkLabel(form, text="Описание").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(form, textvariable=self.desc_var, width=240).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        btns = ctk.CTkFrame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        ctk.CTkButton(btns, text="Сохранить", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Отмена", command=self._cancel, fg_color="#6b7280").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Очистить", command=self._clear).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete).pack(side="left", padx=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=("code", "start", "end", "desc"), show="headings")
        self.tree.heading("code", text="Шифр")
        self.tree.heading("start", text="Дата начала")
        self.tree.heading("end", text="Дата окончания")
        self.tree.heading("desc", text="Описание")
        self.tree.column("code", width=160)
        self.tree.column("start", width=140)
        self.tree.column("end", width=140)
        self.tree.column("desc", width=360)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.suggest_code_frame = ctk.CTkFrame(self)
        self.suggest_code_frame.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

    def _on_code_key(self, _evt=None) -> None:
        prefix = self.code_var.get().strip()
        for w in self.suggest_code_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            rows = q.list_contracts(conn, prefix, CONFIG.autocomplete_limit)
        vals = [r["code"] for r in rows]
        x = self.code_entry.winfo_rootx() - self.winfo_rootx()
        y = self.code_entry.winfo_rooty() - self.winfo_rooty() + self.code_entry.winfo_height()
        self.suggest_code_frame.place(x=x, y=y)
        for val in vals:
            ctk.CTkButton(self.suggest_code_frame, text=val, command=lambda s=val: self._pick_code(s)).pack(fill="x", padx=2, pady=1)
        for label in get_recent("contracts.code", prefix, CONFIG.autocomplete_limit):
            if label not in vals:
                ctk.CTkButton(self.suggest_code_frame, text=label, command=lambda s=label: self._pick_code(s)).pack(fill="x", padx=2, pady=1)

    def _pick_code(self, val: str) -> None:
        self.code_var.set(val)
        record_use("contracts.code", val)
        self.suggest_code_frame.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self.suggest_code_frame.place_forget()
            return
        w = widget
        while w is not None:
            if w == self.suggest_code_frame:
                return
            w = getattr(w, "master", None)
        self.suggest_code_frame.place_forget()

    def _load(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_connection(CONFIG.db_path) as conn:
            rows = ref.list_contracts(conn)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(r["code"], r["start_date"], r["end_date"], r["description"]))

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        code, start, end, desc = self.tree.item(sel[0], "values")
        self.code_var.set(code)
        self.start_var.set(start or "")
        self.end_var.set(end or "")
        self.desc_var.set(desc or "")
        self._snapshot = (code, start or "", end or "", desc or "")

    def _clear(self) -> None:
        self._selected_id = None
        self._snapshot = None
        self.code_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.desc_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.suggest_code_frame.place_forget()

    def _cancel(self) -> None:
        self._clear()

    def _save(self) -> None:
        code = self.code_var.get().strip()
        if not code:
            messagebox.showwarning("Проверка", "Укажите шифр контракта")
            return
        start = self.start_var.get().strip() or None
        end = self.end_var.get().strip() or None
        desc = self.desc_var.get().strip() or None
        try:
            with get_connection(CONFIG.db_path) as conn:
                if self._selected_id:
                    ref.save_contract(conn, self._selected_id, code, start, end, desc)
                else:
                    if q.get_contract_by_code(conn, code):
                        messagebox.showwarning("Дубликат", "Контракт уже существует. Выберите его для редактирования.")
                        return
                    ref.create_contract(conn, code, start, end, desc)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load()
        self._clear()

    def _delete(self) -> None:
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный контракт?"):
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                ref.delete_contract(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load()
        self._clear()

    def _open_date_picker(self, var, anchor=None) -> None:
        from gui.widgets.date_picker import DatePicker
        DatePicker(self, var.get().strip(), lambda d: var.set(d), anchor=anchor)