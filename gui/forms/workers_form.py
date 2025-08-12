from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import reference_data as ref
from services import suggestions


class WorkersForm(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._selected_id: int | None = None
        self._build_ui()
        self._load_workers()

    def _build_ui(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        # Поля ввода
        self.full_name_var = ctk.StringVar()
        self.dept_var = ctk.StringVar()
        self.position_var = ctk.StringVar()
        self.personnel_no_var = ctk.StringVar()

        ctk.CTkLabel(form, text="ФИО").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.full_name_entry = ctk.CTkEntry(form, textvariable=self.full_name_var, width=300)
        self.full_name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.full_name_entry.bind("<KeyRelease>", self._on_name_key)

        ctk.CTkLabel(form, text="Цех").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(form, textvariable=self.dept_var, width=150).grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form, text="Должность").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(form, textvariable=self.position_var, width=300).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form, text="Таб. номер").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(form, textvariable=self.personnel_no_var, width=150).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        btns = ctk.CTkFrame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=10)

        ctk.CTkButton(btns, text="Сохранить", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Очистить", command=self._clear).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete).pack(side="left", padx=5)

        # Таблица
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("full_name", "dept", "position", "personnel_no"), show="headings")
        self.tree.heading("full_name", text="ФИО")
        self.tree.heading("dept", text="Цех")
        self.tree.heading("position", text="Должность")
        self.tree.heading("personnel_no", text="Таб. номер")
        self.tree.column("full_name", width=320)
        self.tree.column("dept", width=100)
        self.tree.column("position", width=200)
        self.tree.column("personnel_no", width=120)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Список подсказок под полем ФИО
        self.suggest_frame = ctk.CTkFrame(self)
        self.suggest_frame.place_forget()

    def _on_name_key(self, event=None) -> None:
        prefix = self.full_name_var.get().strip()
        for w in self.suggest_frame.winfo_children():
            w.destroy()
        if not prefix:
            self.suggest_frame.place_forget()
            return
        with get_connection(CONFIG.db_path) as conn:
            items = suggestions.suggest_workers(conn, prefix, CONFIG.autocomplete_limit)
        if not items:
            self.suggest_frame.place_forget()
            return
        # Показать под полем ввода
        x = self.full_name_entry.winfo_rootx() - self.winfo_rootx()
        y = self.full_name_entry.winfo_rooty() - self.winfo_rooty() + self.full_name_entry.winfo_height()
        self.suggest_frame.place(x=x, y=y)
        for _id, label in items:
            btn = ctk.CTkButton(self.suggest_frame, text=label, command=lambda s=label: self._pick_name(s))
            btn.pack(fill="x", padx=2, pady=1)

    def _pick_name(self, name: str) -> None:
        self.full_name_var.set(name)
        self.suggest_frame.place_forget()

    def _load_workers(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        with get_connection(CONFIG.db_path) as conn:
            rows = ref.list_workers(conn)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(r["full_name"], r["dept"], r["position"], r["personnel_no"]))

    def _on_select(self, event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        self._selected_id = int(iid)
        vals = self.tree.item(iid, "values")
        self.full_name_var.set(vals[0])
        self.dept_var.set(vals[1])
        self.position_var.set(vals[2])
        self.personnel_no_var.set(vals[3])

    def _clear(self) -> None:
        self._selected_id = None
        self.full_name_var.set("")
        self.dept_var.set("")
        self.position_var.set("")
        self.personnel_no_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.suggest_frame.place_forget()

    def _save(self) -> None:
        full_name = self.full_name_var.get().strip()
        if not full_name:
            messagebox.showwarning("Проверка", "Укажите ФИО")
            return
        personnel_no = self.personnel_no_var.get().strip()
        if not personnel_no:
            messagebox.showwarning("Проверка", "Укажите табельный номер")
            return
        dept = self.dept_var.get().strip() or None
        position = self.position_var.get().strip() or None
        try:
            with get_connection(CONFIG.db_path) as conn:
                if self._selected_id:
                    ref.update_worker(conn, self._selected_id, full_name, dept, position, personnel_no)
                else:
                    ref.add_or_update_worker(conn, full_name, dept, position, personnel_no)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load_workers()
        self._clear()

    def _delete(self) -> None:
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранного работника?"):
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                ref.delete_worker(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load_workers()
        self._clear()