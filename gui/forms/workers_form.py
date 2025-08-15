from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import reference_data as ref
from services import suggestions
from db import queries as q
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry, 
    create_suggestion_button, 
    create_suggestions_frame
)


class WorkersForm(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self._selected_id: int | None = None
        self._edit_snapshot: dict | None = None
        self._hide_jobs: dict[int, str] = {}
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
        self.full_name_entry.bind("<FocusIn>", lambda e: self._on_name_key())
        self.full_name_entry.bind("<Button-1>", lambda e: self.after(1, self._on_name_key))

        ctk.CTkLabel(form, text="Цех").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.dept_entry = ctk.CTkEntry(form, textvariable=self.dept_var, width=150)
        self.dept_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.dept_entry.bind("<KeyRelease>", self._on_dept_key)
        self.dept_entry.bind("<FocusIn>", lambda e: self._on_dept_key())
        self.dept_entry.bind("<Button-1>", lambda e: self.after(1, self._on_dept_key))

        ctk.CTkLabel(form, text="Должность").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.position_entry = ctk.CTkEntry(form, textvariable=self.position_var, width=300)
        self.position_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.position_entry.bind("<KeyRelease>", self._on_position_key)
        self.position_entry.bind("<FocusIn>", lambda e: self._on_position_key())
        self.position_entry.bind("<Button-1>", lambda e: self.after(1, self._on_position_key))

        ctk.CTkLabel(form, text="Таб. номер").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.personnel_entry = ctk.CTkEntry(form, textvariable=self.personnel_no_var, width=150)
        self.personnel_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.personnel_entry.bind("<KeyRelease>", self._on_personnel_key)
        self.personnel_entry.bind("<FocusIn>", lambda e: self._on_personnel_key())
        self.personnel_entry.bind("<Button-1>", lambda e: self.after(1, self._on_personnel_key))

        btns = ctk.CTkFrame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=10)

        save_btn = ctk.CTkButton(btns, text="Сохранить", command=self._save)
        cancel_btn = ctk.CTkButton(btns, text="Отмена", command=self._cancel_edit, fg_color="#6b7280")
        clear_btn = ctk.CTkButton(btns, text="Очистить", command=self._clear)
        del_btn = ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete)
        for b in (save_btn, cancel_btn, clear_btn, del_btn):
            b.pack(side="left", padx=5)
        if self._readonly:
            for w in (self.full_name_entry, self.dept_entry, self.position_entry, self.personnel_entry):
                try:
                    w.configure(state="disabled")
                except Exception:
                    pass
            for b in (save_btn, cancel_btn, clear_btn, del_btn):
                b.configure(state="disabled")

        # Таблица
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Grid резиновость
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=("full_name", "dept", "position", "personnel_no"), show="headings")
        self.tree.heading("full_name", text="ФИО")
        self.tree.heading("dept", text="Цех")
        self.tree.heading("position", text="Должность")
        self.tree.heading("personnel_no", text="Таб. номер")
        self.tree.column("full_name", width=320)
        self.tree.column("dept", width=100)
        self.tree.column("position", width=200)
        self.tree.column("personnel_no", width=120)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Списки подсказок под полями
        self.suggest_frame = create_suggestions_frame(self)
        self.suggest_frame.place_forget()
        self.suggest_dept_frame = create_suggestions_frame(self)
        self.suggest_dept_frame.place_forget()
        self.suggest_position_frame = create_suggestions_frame(self)
        self.suggest_position_frame.place_forget()
        self.suggest_personnel_frame = create_suggestions_frame(self)
        self.suggest_personnel_frame.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

    def _hide_all_suggestions(self) -> None:
        self.suggest_frame.place_forget()
        self.suggest_dept_frame.place_forget()
        self.suggest_position_frame.place_forget()
        self.suggest_personnel_frame.place_forget()

    def _schedule_auto_hide(self, frame: ctk.CTkFrame, related_entries: list[ctk.CTkEntry]) -> None:
        # cancel previous job for this frame
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
            # check inside frame children
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
        prefix = self.full_name_var.get().strip()
        for w in self.suggest_frame.winfo_children():
            w.destroy()
        
        # Показываем подсказки даже при пустом вводе
        place_suggestions_under_entry(self.full_name_entry, self.suggest_frame, self)
        
        items: list[tuple[int, str]] = []
        if prefix:
            with get_connection(CONFIG.db_path) as conn:
                items = suggestions.suggest_workers(conn, prefix, CONFIG.autocomplete_limit)
        
        shown = 0
        for _id, label in items:
            create_suggestion_button(self.suggest_frame, text=label, command=lambda s=label: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        # Дополняем историей (если пустой ввод — показываем только историю)
        recent = [v for v in get_recent("workers.full_name", prefix or None, CONFIG.autocomplete_limit)]
        for label in recent:
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in [lbl for _, lbl in items]:
                create_suggestion_button(self.suggest_frame, text=label, command=lambda s=label: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все работников
        if shown == 0:
            with get_connection(CONFIG.db_path) as conn:
                all_workers = suggestions.suggest_workers(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_workers:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_frame, text=label, command=lambda s=label: self._pick_name(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.suggest_frame, [self.full_name_entry])

    def _on_dept_key(self, event=None) -> None:
        self._hide_all_suggestions()
        prefix = self.dept_var.get().strip()
        for w in self.suggest_dept_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.dept_entry, self.suggest_dept_frame, self)
        
        vals = []
        if prefix:
            with get_connection(CONFIG.db_path) as conn:
                vals = suggestions.suggest_depts(conn, prefix, CONFIG.autocomplete_limit)
        
        shown = 0
        for val in vals:
            create_suggestion_button(self.suggest_dept_frame, text=val, command=lambda s=val: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("workers.dept", prefix or None, CONFIG.autocomplete_limit):
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in vals:
                create_suggestion_button(self.suggest_dept_frame, text=label, command=lambda s=label: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все цеха
        if shown == 0:
            with get_connection(CONFIG.db_path) as conn:
                all_depts = suggestions.suggest_depts(conn, "", CONFIG.autocomplete_limit)
            for dept in all_depts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_dept_frame, text=dept, command=lambda s=dept: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.suggest_dept_frame, [self.dept_entry])

    def _on_position_key(self, event=None) -> None:
        self._hide_all_suggestions()
        prefix = self.position_var.get().strip()
        for w in self.suggest_position_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.position_entry, self.suggest_position_frame, self)
        
        vals = []
        if prefix:
            with get_connection(CONFIG.db_path) as conn:
                vals = suggestions.suggest_positions(conn, prefix, CONFIG.autocomplete_limit)
        
        shown = 0
        for val in vals:
            create_suggestion_button(self.suggest_position_frame, text=val, command=lambda s=val: self._pick_position(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("workers.position", prefix or None, CONFIG.autocomplete_limit):
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in vals:
                create_suggestion_button(self.suggest_position_frame, text=label, command=lambda s=label: self._pick_position(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все должности
        if shown == 0:
            with get_connection(CONFIG.db_path) as conn:
                all_positions = suggestions.suggest_positions(conn, "", CONFIG.autocomplete_limit)
            for position in all_positions:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_position_frame, text=position, command=lambda s=position: self._pick_position(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.suggest_position_frame, [self.position_entry])

    def _on_personnel_key(self, event=None) -> None:
        self._hide_all_suggestions()
        prefix = self.personnel_no_var.get().strip()
        for w in self.suggest_personnel_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.personnel_entry, self.suggest_personnel_frame, self)
        
        vals = []
        if prefix:
            with get_connection(CONFIG.db_path) as conn:
                vals = suggestions.suggest_personnel_nos(conn, prefix, CONFIG.autocomplete_limit)
        
        shown = 0
        for val in vals:
            create_suggestion_button(self.suggest_personnel_frame, text=val, command=lambda s=val: self._pick_personnel(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("workers.personnel_no", prefix or None, CONFIG.autocomplete_limit):
            if shown >= CONFIG.autocomplete_limit:
                break
            if label not in vals:
                create_suggestion_button(self.suggest_personnel_frame, text=label, command=lambda s=label: self._pick_personnel(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все табельные номера
        if shown == 0:
            with get_connection(CONFIG.db_path) as conn:
                all_personnel = suggestions.suggest_personnel_nos(conn, "", CONFIG.autocomplete_limit)
            for personnel in all_personnel:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_personnel_frame, text=personnel, command=lambda s=personnel: self._pick_personnel(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.suggest_personnel_frame, [self.personnel_entry])

    def _pick_name(self, name: str) -> None:
        self.full_name_var.set(name)
        record_use("workers.full_name", name)
        self.suggest_frame.place_forget()

    def _pick_dept(self, val: str) -> None:
        self.dept_var.set(val)
        record_use("workers.dept", val)
        self.suggest_dept_frame.place_forget()

    def _pick_position(self, val: str) -> None:
        self.position_var.set(val)
        record_use("workers.position", val)
        self.suggest_position_frame.place_forget()

    def _pick_personnel(self, val: str) -> None:
        self.personnel_no_var.set(val)
        record_use("workers.personnel_no", val)
        self.suggest_personnel_frame.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggestions()
            return
        # Если клик внутри любого фрейма подсказок — не скрывать
        for frame in (self.suggest_frame, self.suggest_dept_frame, self.suggest_position_frame, self.suggest_personnel_frame):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        # Иначе скрыть все
        self._hide_all_suggestions()

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
        # snapshot
        self._edit_snapshot = {
            "full_name": vals[0],
            "dept": vals[1],
            "position": vals[2],
            "personnel_no": vals[3],
        }

    def _clear(self) -> None:
        self._selected_id = None
        self._edit_snapshot = None
        self.full_name_var.set("")
        self.dept_var.set("")
        self.position_var.set("")
        self.personnel_no_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self._hide_all_suggestions()

    def _cancel_edit(self) -> None:
        self._clear()

    def _save(self) -> None:
        if getattr(self, "_readonly", False):
            return
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
                    # Проверка дубликатов по ФИО и табельному
                    if q.get_worker_by_full_name(conn, full_name) or q.get_worker_by_personnel_no(conn, personnel_no):
                        messagebox.showwarning("Дубликат", "Работник уже существует. Выберите его в списке для редактирования.")
                        return
                    ref.add_or_update_worker(conn, full_name, dept, position, personnel_no)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load_workers()
        self._clear()

    def _delete(self) -> None:
        if getattr(self, "_readonly", False):
            return
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