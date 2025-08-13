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


class JobTypesForm(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._selected_id: int | None = None
        self._snapshot: tuple[str, str, str] | None = None
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        self.name_var = ctk.StringVar()
        self.unit_var = ctk.StringVar()
        self.price_var = ctk.StringVar()

        ctk.CTkLabel(form, text="Наименование").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=320)
        self.name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.name_entry.bind("<KeyRelease>", self._on_name_key)
        self.name_entry.bind("<FocusIn>", lambda e: self._on_name_key())
        self.name_entry.bind("<Button-1>", lambda e: self.after(1, self._on_name_key))

        ctk.CTkLabel(form, text="Ед. изм.").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.unit_entry = ctk.CTkEntry(form, textvariable=self.unit_var, width=120)
        self.unit_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.unit_entry.bind("<KeyRelease>", self._on_unit_key)
        self.unit_entry.bind("<FocusIn>", lambda e: self._on_unit_key())
        self.unit_entry.bind("<Button-1>", lambda e: self.after(1, self._on_unit_key))

        ctk.CTkLabel(form, text="Цена").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(form, textvariable=self.price_var, width=120).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        btns = ctk.CTkFrame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        ctk.CTkButton(btns, text="Сохранить", command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Отмена", command=self._cancel, fg_color="#6b7280").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Очистить", command=self._clear).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete).pack(side="left", padx=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("name", "unit", "price"), show="headings")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("unit", text="Ед. изм.")
        self.tree.heading("price", text="Цена")
        self.tree.column("name", width=360)
        self.tree.column("unit", width=120)
        self.tree.column("price", width=120)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Suggest frames
        self.suggest_name_frame = ctk.CTkFrame(self)
        self.suggest_name_frame.place_forget()
        self.suggest_unit_frame = ctk.CTkFrame(self)
        self.suggest_unit_frame.place_forget()

        # Глобальный клик — скрыть подсказки, если клик вне списков
        self.bind_all("<Button-1>", self._on_global_click, add="+")

    def _hide_all_suggestions(self) -> None:
        self.suggest_name_frame.place_forget()
        self.suggest_unit_frame.place_forget()

    def _place_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        x = entry.winfo_rootx() - self.winfo_rootx()
        y = entry.winfo_rooty() - self.winfo_rooty() + entry.winfo_height()
        frame.place(x=x, y=y)
        frame.lift()

    def _schedule_auto_hide(self, frame: ctk.CTkFrame, related_entries: list[ctk.CTkEntry]) -> None:
        job_id = getattr(frame, "_auto_hide_job", None)
        if job_id:
            try:
                self.after_cancel(job_id)
            except Exception:
                pass
        def is_focus_within() -> bool:
            focus_w = self.focus_get()
            if not focus_w:
                return False
            if focus_w in related_entries:
                return True
            stack = list(frame.winfo_children())
            while stack:
                w = stack.pop()
                if w == focus_w:
                    return True
                stack.extend(getattr(w, "winfo_children", lambda: [])())
            return False
        def check_and_hide():
            if not is_focus_within():
                frame.place_forget()
                frame._auto_hide_job = None
            else:
                frame._auto_hide_job = self.after(5000, check_and_hide)
        frame._auto_hide_job = self.after(5000, check_and_hide)

    def _on_name_key(self, event=None) -> None:
        self._hide_all_suggestions()
        prefix = self.name_var.get().strip()
        for w in self.suggest_name_frame.winfo_children():
            w.destroy()
        # запросы
        if prefix:
            with get_connection(CONFIG.db_path) as conn:
                rows = q.search_job_types_by_prefix(conn, prefix, CONFIG.autocomplete_limit)
        else:
            with get_connection(CONFIG.db_path) as conn:
                rows = q.list_job_types(conn, None, CONFIG.autocomplete_limit)
        names = [r["name"] for r in rows]
        self._place_under(self.name_entry, self.suggest_name_frame)
        shown = 0
        for val in names:
            ctk.CTkButton(self.suggest_name_frame, text=val, command=lambda s=val: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        for label in get_recent("job_types.name", prefix or None, CONFIG.autocomplete_limit):
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in names:
                ctk.CTkButton(self.suggest_name_frame, text=label, command=lambda s=label: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        self._schedule_auto_hide(self.suggest_name_frame, [self.name_entry])

    def _pick_name(self, val: str) -> None:
        self.name_var.set(val)
        record_use("job_types.name", val)
        self.suggest_name_frame.place_forget()

    def _on_unit_key(self, event=None) -> None:
        self._hide_all_suggestions()
        prefix = self.unit_var.get().strip()
        for w in self.suggest_unit_frame.winfo_children():
            w.destroy()
        with get_connection(CONFIG.db_path) as conn:
            vals = q.distinct_units_by_prefix(conn, prefix, CONFIG.autocomplete_limit)
        self._place_under(self.unit_entry, self.suggest_unit_frame)
        shown = 0
        for val in vals:
            ctk.CTkButton(self.suggest_unit_frame, text=val, command=lambda s=val: self._pick_unit(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        for label in get_recent("job_types.unit", prefix or None, CONFIG.autocomplete_limit):
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in vals:
                ctk.CTkButton(self.suggest_unit_frame, text=label, command=lambda s=label: self._pick_unit(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        self._schedule_auto_hide(self.suggest_unit_frame, [self.unit_entry])

    def _pick_unit(self, val: str) -> None:
        self.unit_var.set(val)
        record_use("job_types.unit", val)
        self.suggest_unit_frame.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggestions()
            return
        for frame in (self.suggest_name_frame, self.suggest_unit_frame):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self._hide_all_suggestions()

    def _load(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_connection(CONFIG.db_path) as conn:
            rows = ref.list_job_types(conn)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["unit"], r["price"]))

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        name, unit, price = self.tree.item(sel[0], "values")
        self.name_var.set(name)
        self.unit_var.set(unit)
        self.price_var.set(str(price))
        self._snapshot = (name, unit, str(price))

    def _clear(self) -> None:
        self._selected_id = None
        self._snapshot = None
        self.name_var.set("")
        self.unit_var.set("")
        self.price_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self._hide_all_suggestions()

    def _cancel(self) -> None:
        self._clear()

    def _save(self) -> None:
        name = self.name_var.get().strip()
        unit = self.unit_var.get().strip()
        price_str = self.price_var.get().strip()
        if not name:
            messagebox.showwarning("Проверка", "Заполните наименование")
            return
        if not unit:
            messagebox.showwarning("Проверка", "Заполните единицу измерения")
            return
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError
        except Exception:
            messagebox.showwarning("Проверка", "Цена должна быть неотрицательным числом")
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                if self._selected_id:
                    ref.save_job_type(conn, self._selected_id, name, unit, price)
                else:
                    # Запретить добавление дубликата по name
                    if q.get_job_type_by_name(conn, name):
                        messagebox.showwarning("Дубликат", "Вид работ уже существует. Выберите его для редактирования.")
                        return
                    ref.create_job_type(conn, name, unit, price)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load()
        self._clear()

    def _delete(self) -> None:
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный вид работ?"):
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                ref.delete_job_type(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load()
        self._clear()