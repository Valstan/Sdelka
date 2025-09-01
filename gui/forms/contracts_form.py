from __future__ import annotations

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from services import reference_data as ref
from db import queries as q
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry, 
    create_suggestion_button, 
    create_suggestions_frame
)


class ContractsForm(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self._selected_id: int | None = None
        self._snapshot: tuple[str, str | None, str | None, str | None, str | None, str | None, str | None, str | None, str | None, str | None] | None = None
        self._build_ui()
        self._load()
        # Обновлять список при импорте
        try:
            self.bind("<<DataImported>>", lambda e: self._load())
            self.winfo_toplevel().bind("<<DataImported>>", lambda e: self._load(), add="+")
        except Exception:
            pass

    def _build_ui(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        # Переменные для всех полей
        self.code_var = ctk.StringVar()
        self.name_var = ctk.StringVar()
        self.contract_type_var = ctk.StringVar()
        self.executor_var = ctk.StringVar()
        self.igk_var = ctk.StringVar()
        self.contract_number_var = ctk.StringVar()
        self.bank_account_var = ctk.StringVar()
        self.start_var = ctk.StringVar()
        self.end_var = ctk.StringVar()
        self.desc_var = ctk.StringVar()

        # Первая строка
        ctk.CTkLabel(form, text="Шифр контракта").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.code_entry = ctk.CTkEntry(form, textvariable=self.code_var, width=200)
        self.code_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.code_entry.bind("<KeyRelease>", self._on_code_key)
        self.code_entry.bind("<FocusIn>", lambda e: self._on_code_key())
        self.code_entry.bind("<Button-1>", lambda e: self.after(1, self._on_code_key))

        ctk.CTkLabel(form, text="Наименование").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=300)
        self.name_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # Вторая строка
        ctk.CTkLabel(form, text="Вид контракта").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.contract_type_entry = ctk.CTkEntry(form, textvariable=self.contract_type_var, width=200)
        self.contract_type_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form, text="Исполнитель").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.executor_entry = ctk.CTkEntry(form, textvariable=self.executor_var, width=300)
        self.executor_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Третья строка
        ctk.CTkLabel(form, text="ИГК").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.igk_entry = ctk.CTkEntry(form, textvariable=self.igk_var, width=200)
        self.igk_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form, text="Номер контракта").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.contract_number_entry = ctk.CTkEntry(form, textvariable=self.contract_number_var, width=300)
        self.contract_number_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # Четвертая строка
        ctk.CTkLabel(form, text="Отдельный счет").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.bank_account_entry = ctk.CTkEntry(form, textvariable=self.bank_account_var, width=200)
        self.bank_account_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(form, text="Дата начала").grid(row=3, column=2, sticky="w", padx=5, pady=5)
        self.start_entry = ctk.CTkEntry(form, textvariable=self.start_var, width=120)
        self.start_entry.grid(row=3, column=3, sticky="w", padx=5, pady=5)
        self.start_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.start_var, self.start_entry))

        # Пятая строка
        ctk.CTkLabel(form, text="Дата окончания").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.end_entry = ctk.CTkEntry(form, textvariable=self.end_var, width=120)
        self.end_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.end_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.end_var, self.end_entry))

        ctk.CTkLabel(form, text="Описание").grid(row=4, column=2, sticky="w", padx=5, pady=5)
        self.desc_entry = ctk.CTkEntry(form, textvariable=self.desc_var, width=300)
        self.desc_entry.grid(row=4, column=3, sticky="w", padx=5, pady=5)

        # Кнопки
        btns = ctk.CTkFrame(form)
        btns.grid(row=5, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        save_btn = ctk.CTkButton(btns, text="Сохранить", command=self._save)
        cancel_btn = ctk.CTkButton(btns, text="Отмена", command=self._cancel, fg_color="#6b7280")
        clear_btn = ctk.CTkButton(btns, text="Очистить", command=self._clear)
        del_btn = ctk.CTkButton(btns, text="Удалить", fg_color="#b91c1c", hover_color="#7f1d1d", command=self._delete)
        for b in (save_btn, cancel_btn, clear_btn, del_btn):
            b.pack(side="left", padx=5)
        if self._readonly:
            for w in (self.code_entry, self.name_entry, self.contract_type_entry, self.executor_entry, 
                     self.igk_entry, self.contract_number_entry, self.bank_account_entry, 
                     self.start_entry, self.end_entry, self.desc_entry):
                try:
                    w.configure(state="disabled")
                except Exception:
                    pass
            for b in (save_btn, cancel_btn, clear_btn, del_btn):
                b.configure(state="disabled")

        # Таблица
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Обновляем колонки таблицы для всех полей
        self.tree = ttk.Treeview(table_frame, columns=("code", "name", "contract_type", "executor", "igk", "contract_number", "bank_account", "start", "end", "desc"), show="headings")
        self.tree.heading("code", text="Шифр")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("contract_type", text="Вид контракта")
        self.tree.heading("executor", text="Исполнитель")
        self.tree.heading("igk", text="ИГК")
        self.tree.heading("contract_number", text="Номер контракта")
        self.tree.heading("bank_account", text="Отдельный счет")
        self.tree.heading("start", text="Дата начала")
        self.tree.heading("end", text="Дата окончания")
        self.tree.heading("desc", text="Описание")
        
        # Устанавливаем ширину колонок
        self.tree.column("code", width=120)
        self.tree.column("name", width=200)
        self.tree.column("contract_type", width=120)
        self.tree.column("executor", width=150)
        self.tree.column("igk", width=80)
        self.tree.column("contract_number", width=120)
        self.tree.column("bank_account", width=100)
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("desc", width=200)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.suggest_code_frame = create_suggestions_frame(self)
        self.suggest_code_frame.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

    def _on_code_key(self, _evt=None) -> None:
        prefix = self.code_var.get().strip()
        for w in self.suggest_code_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.code_entry, self.suggest_code_frame, self)
        
        with get_connection() as conn:
            rows = q.list_contracts(conn, prefix, CONFIG.autocomplete_limit)
        vals = [r["code"] for r in rows]
        
        shown = 0
        for val in vals:
            create_suggestion_button(self.suggest_code_frame, text=val, command=lambda s=val: self._pick_code(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("contracts.code", prefix, CONFIG.autocomplete_limit):
            if label not in vals:
                create_suggestion_button(self.suggest_code_frame, text=label, command=lambda s=label: self._pick_code(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все контракты
        if shown == 0:
            with get_connection() as conn:
                all_contracts = q.list_contracts(conn, "", CONFIG.autocomplete_limit)
            for row in all_contracts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.suggest_code_frame, text=row["code"], command=lambda s=row["code"]: self._pick_code(s)).pack(fill="x", padx=2, pady=1)
                shown += 1

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
        with get_connection() as conn:
            rows = ref.list_contracts(conn)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["code"], 
                r["name"] if r["name"] else "", 
                r["contract_type"] if r["contract_type"] else "", 
                r["executor"] if r["executor"] else "", 
                r["igk"] if r["igk"] else "", 
                r["contract_number"] if r["contract_number"] else "", 
                r["bank_account"] if r["bank_account"] else "", 
                r["start_date"] if r["start_date"] else "", 
                r["end_date"] if r["end_date"] else "", 
                r["description"] if r["description"] else ""
            ))

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        values = self.tree.item(sel[0], "values")
        if len(values) >= 10:
            code, name, contract_type, executor, igk, contract_number, bank_account, start, end, desc = values
            self.code_var.set(code)
            self.name_var.set(name or "")
            self.contract_type_var.set(contract_type or "")
            self.executor_var.set(executor or "")
            self.igk_var.set(igk or "")
            self.contract_number_var.set(contract_number or "")
            self.bank_account_var.set(bank_account or "")
            self.start_var.set(start or "")
            self.end_var.set(end or "")
            self.desc_var.set(desc or "")
            self._snapshot = (code, name or "", contract_type or "", executor or "", igk or "", 
                            contract_number or "", bank_account or "", start or "", end or "", desc or "")

    def _clear(self) -> None:
        self._selected_id = None
        self._snapshot = None
        self.code_var.set("")
        self.name_var.set("")
        self.contract_type_var.set("")
        self.executor_var.set("")
        self.igk_var.set("")
        self.contract_number_var.set("")
        self.bank_account_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.desc_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.suggest_code_frame.place_forget()

    def _cancel(self) -> None:
        self._clear()

    def _save(self) -> None:
        if getattr(self, "_readonly", False):
            return
        code = self.code_var.get().strip()
        if not code:
            messagebox.showwarning("Проверка", "Укажите шифр контракта")
            return
        
        # Получаем все значения полей
        name = self.name_var.get().strip() or None
        contract_type = self.contract_type_var.get().strip() or None
        executor = self.executor_var.get().strip() or None
        igk = self.igk_var.get().strip() or None
        contract_number = self.contract_number_var.get().strip() or None
        bank_account = self.bank_account_var.get().strip() or None
        start = self.start_var.get().strip() or None
        end = self.end_var.get().strip() or None
        desc = self.desc_var.get().strip() or None
        
        try:
            with get_connection() as conn:
                if self._selected_id:
                    ref.save_contract(conn, self._selected_id, code, start, end, desc, 
                                   name, contract_type, executor, igk, contract_number, bank_account)
                else:
                    if q.get_contract_by_code(conn, code):
                        messagebox.showwarning("Дубликат", "Контракт уже существует. Выберите его для редактирования.")
                        return
                    ref.create_contract(conn, code, start, end, desc, 
                                     name, contract_type, executor, igk, contract_number, bank_account)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Нарушение уникальности: {exc}")
            return
        self._load()
        self._clear()

    def _delete(self) -> None:
        if getattr(self, "_readonly", False):
            return
        if not self._selected_id:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный контракт?"):
            return
        try:
            with get_connection() as conn:
                ref.delete_contract(conn, self._selected_id)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка", f"Невозможно удалить: {exc}")
            return
        self._load()
        self._clear()

    def _open_date_picker(self, var, anchor=None) -> None:
        from gui.widgets.date_picker import open_for_anchor
        if anchor is None:
            return
        open_for_anchor(self, anchor, var.get().strip(), lambda d: var.set(d))