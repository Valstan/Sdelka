from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import pandas as pd
import os
import sys
import subprocess

from config.settings import CONFIG
import tkinter as tk
from pathlib import Path
from utils.text import normalize_for_search
from db.sqlite import get_connection
from services import suggestions
from reports.report_builders import work_orders_report_df, work_orders_report_context
from reports.html_export import save_html
from reports.pdf_reportlab import save_pdf
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry, 
    create_suggestion_button, 
    create_suggestions_frame,
)
import logging


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._selected_worker_id: int | None = None
        self._selected_job_type_id: int | None = None
        self._selected_product_id: int | None = None
        self.product_entry_text: ctk.StringVar | None = None
        self._selected_contract_id: int | None = None
        self._df: pd.DataFrame | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        filters = ctk.CTkFrame(self)
        filters.pack(fill="x", padx=10, pady=10)

        # Dates
        self.date_from = ctk.StringVar()
        self.date_to = ctk.StringVar()
        ctk.CTkLabel(filters, text="Период с").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.date_from_entry = ctk.CTkEntry(
            filters, textvariable=self.date_from, width=120
        )
        self.date_from_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.date_from_entry.bind(
            "<FocusIn>",
            lambda e: self._open_date_picker(self.date_from, self.date_from_entry),
        )
        
        ctk.CTkLabel(filters, text="по").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.date_to_entry = ctk.CTkEntry(filters, textvariable=self.date_to, width=120)
        self.date_to_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.date_to_entry.bind(
            "<FocusIn>",
            lambda e: self._open_date_picker(self.date_to, self.date_to_entry),
        )

        # Worker
        ctk.CTkLabel(filters, text="Работник").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.worker_entry = ctk.CTkEntry(filters, placeholder_text="ФИО", width=240)
        self.worker_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.worker_entry.bind("<KeyRelease>", self._on_worker_key)
        self.worker_entry.bind("<FocusIn>", lambda e: self._on_worker_key())
        self.worker_entry.bind(
            "<Button-1>", lambda e: self.after(1, self._on_worker_key)
        )

        # Dept
        ctk.CTkLabel(filters, text="Цех").grid(
            row=1, column=2, padx=5, pady=5, sticky="w"
        )
        self.dept_var = ctk.StringVar()
        self.dept_entry = ctk.CTkEntry(filters, textvariable=self.dept_var, width=120)
        self.dept_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.dept_entry.bind("<KeyRelease>", self._on_dept_key)
        self.dept_entry.bind("<FocusIn>", lambda e: self._on_dept_key())
        self.dept_entry.bind("<Button-1>", lambda e: self.after(1, self._on_dept_key))

        # Job type
        ctk.CTkLabel(filters, text="Вид работ").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.job_entry = ctk.CTkEntry(
            filters, placeholder_text="Название вида", width=240
        )
        self.job_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.job_entry.bind("<KeyRelease>", self._on_job_key)
        self.job_entry.bind("<FocusIn>", lambda e: self._on_job_key())
        self.job_entry.bind("<Button-1>", lambda e: self.after(1, self._on_job_key))

        # Product
        ctk.CTkLabel(filters, text="Изделие").grid(
            row=2, column=2, padx=5, pady=5, sticky="w"
        )
        self.product_entry = ctk.CTkEntry(
            filters, placeholder_text="Номер/Название", width=240
        )
        self.product_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.product_entry.bind("<KeyRelease>", self._on_product_key)
        self.product_entry.bind("<FocusIn>", lambda e: self._on_product_key())
        self.product_entry.bind(
            "<Button-1>", lambda e: self.after(1, self._on_product_key)
        )

        # Contract
        ctk.CTkLabel(filters, text="Контракт").grid(
            row=3, column=0, padx=5, pady=5, sticky="w"
        )
        self.contract_entry = ctk.CTkEntry(filters, placeholder_text="Шифр", width=160)
        self.contract_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)
        self.contract_entry.bind("<FocusIn>", lambda e: self._on_contract_key())
        self.contract_entry.bind(
            "<Button-1>", lambda e: self.after(1, self._on_contract_key)
        )

        ctk.CTkButton(filters, text="Сформировать", command=self._build_report).grid(
            row=3, column=3, padx=5, pady=5, sticky="e"
        )

        # Suggest frames
        self.sg_worker = create_suggestions_frame(self)
        self.sg_worker.place_forget()
        self.sg_dept = create_suggestions_frame(self)
        self.sg_dept.place_forget()
        self.sg_job = create_suggestions_frame(self)
        self.sg_job.place_forget()
        self.sg_product = create_suggestions_frame(self)
        self.sg_product.place_forget()
        self.sg_contract = create_suggestions_frame(self)
        self.sg_contract.place_forget()

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

        # Панель экспорта (без предпросмотра)
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=(6, 8))
        ctk.CTkButton(toolbar, text="Экспорт HTML", command=self._export_html).pack(
            side="left", padx=4
        )
        ctk.CTkButton(toolbar, text="Экспорт PDF", command=self._export_pdf).pack(
            side="left", padx=4
        )
        ctk.CTkButton(toolbar, text="Экспорт Excel", command=self._export_excel).pack(
            side="left", padx=4
        )
        ctk.CTkButton(
            toolbar, text="Экспорт в 1С (JSON)", command=self._export_1c_json
        ).pack(side="left", padx=4)

        # Простая табличка предпросмотра списка (не обязательна для печати)
        self.tree = ttk.Treeview(self, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        vsb.place_forget()
        hsb.place_forget()  # оставим без явных скроллов
        # Автоподгон ширин колонок при изменении размеров
        self._preview_resize_job = None

        def _on_tree_resize(_evt=None):
            try:
                if self._preview_resize_job:
                    self.after_cancel(self._preview_resize_job)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            self._preview_resize_job = self.after(60, self._autosize_preview_columns)

        self.tree.bind("<Configure>", _on_tree_resize)

        # Полоса статистики под предпросмотром
        self.stats_var = ctk.StringVar(value="")
        self.stats_label = ctk.CTkLabel(self, textvariable=self.stats_var, anchor="w")
        self.stats_label.pack(fill="x", padx=10, pady=(0, 10))

    def _place_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        place_suggestions_under_entry(entry, frame, self)

    def _clear_frame(self, frame: ctk.CTkFrame) -> None:
        for w in frame.winfo_children():
            w.destroy()

    def _hide_all_suggestions(self) -> None:
        self.sg_worker.place_forget()
        self.sg_dept.place_forget()
        self.sg_job.place_forget()
        self.sg_product.place_forget()
        self.sg_contract.place_forget()

    def _schedule_auto_hide(
        self, frame: ctk.CTkFrame, related_entries: list[ctk.CTkEntry]
    ) -> None:
        job_id = getattr(frame, "_auto_hide_job", None)
        if job_id:
            try:
                self.after_cancel(job_id)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

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

    def _on_worker_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._selected_worker_id = None
        self._clear_frame(self.sg_worker)
        text = self.worker_entry.get().strip()
        
        place_suggestions_under_entry(self.worker_entry, self.sg_worker, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_workers(conn, text, CONFIG.autocomplete_limit)
            # Чистим историю работников от отсутствующих
            try:
                from utils.usage_history import get_recent, purge_missing
                from utils.text import normalize_for_search

                valid_norms = {
                    normalize_for_search(lbl.replace(" (Уволен)", ""))
                    for (_id, lbl) in rows
                }
                history = get_recent("reports.worker", None, CONFIG.autocomplete_limit)
                purge_missing("reports.worker", valid_norms)
                cleaned_hist = [
                    h for h in history if normalize_for_search(h) in valid_norms
                ]
            except Exception as exc:
                cleaned_hist = []
        
        seen: set[str] = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(
                self.sg_worker,
                text=label,
                command=lambda i=_id, l=label: self._pick_worker(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in cleaned_hist:
            if label not in seen:
                create_suggestion_button(
                    self.sg_worker,
                    text=label,
                    command=lambda l=label: self._pick_worker(0, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем всех работников
        if shown == 0:
            with get_connection() as conn:
                all_workers = suggestions.suggest_workers(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_workers:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.sg_worker,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_worker(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_worker, [self.worker_entry])

    def _pick_worker(self, worker_id: int, label: str) -> None:
        self._selected_worker_id = worker_id if worker_id else self._selected_worker_id
        self.worker_entry.delete(0, "end")
        self.worker_entry.insert(0, label)
        record_use("reports.worker", label)
        self.sg_worker.place_forget()

    def _on_dept_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._clear_frame(self.sg_dept)
        text = self.dept_entry.get().strip()
        
        place_suggestions_under_entry(self.dept_entry, self.sg_dept, self)
        
        with get_connection() as conn:
            vals = suggestions.suggest_depts(conn, text, CONFIG.autocomplete_limit)
        
        seen = set()
        shown = 0
        for v in vals:
            seen.add(v)
            create_suggestion_button(
                self.sg_dept, text=v, command=lambda s=v: self._pick_dept(s)
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent(
            "reports.dept", text or None, CONFIG.autocomplete_limit
        ):
            if label not in seen:
                create_suggestion_button(
                    self.sg_dept, text=label, command=lambda s=label: self._pick_dept(s)
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все цеха
        if shown == 0:
            with get_connection() as conn:
                all_depts = suggestions.suggest_depts(
                    conn, "", CONFIG.autocomplete_limit
                )
            for dept in all_depts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.sg_dept, text=dept, command=lambda s=dept: self._pick_dept(s)
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_dept, [self.dept_entry])

    def _pick_dept(self, val: str) -> None:
        self.dept_var.set(val)
        record_use("reports.dept", val)
        self.sg_dept.place_forget()

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        # при ручном вводе сбрасываем выбранный id, чтобы не остался старый
        self._selected_job_type_id = None
        self._clear_frame(self.sg_job)
        text = self.job_entry.get().strip()
        
        place_suggestions_under_entry(self.job_entry, self.sg_job, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_job_types(conn, text, CONFIG.autocomplete_limit)
            # Очистим историю от отсутствующих значений и не будем показывать их
            try:
                from utils.usage_history import get_recent, purge_missing
                from utils.text import normalize_for_search

                # Список актуальных нормализованных имен из БД (на экране)
                valid_norms = {normalize_for_search(lbl) for (_id, lbl) in rows}
                # Возьмем часть истории (без префикса, чтобы чистить глобально)
                history = get_recent(
                    "reports.job_type", None, CONFIG.autocomplete_limit
                )
                # Оставим только те, что реально присутствуют в БД
                cleaned = [h for h in history if normalize_for_search(h) in valid_norms]
                # Удалим отсутствующие из истории
                purge_missing("reports.job_type", valid_norms)
            except Exception as exc:
                cleaned = []
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(
                self.sg_job,
                text=label,
                command=lambda i=_id, l=label: self._pick_job(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in cleaned:
            if label not in seen:
                create_suggestion_button(
                    self.sg_job,
                    text=label,
                    command=lambda l=label: self._pick_job(0, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все виды работ
        if shown == 0:
            with get_connection() as conn:
                all_job_types = suggestions.suggest_job_types(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_job_types:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.sg_job,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_job(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_job, [self.job_entry])

    def _pick_job(self, job_type_id: int, label: str) -> None:
        # Если выбран конкретный id — запоминаем, иначе сбрасываем id и используем текстовый фильтр по названию
        if job_type_id:
            self._selected_job_type_id = job_type_id
        else:
            self._selected_job_type_id = None
        self.job_entry.delete(0, "end")
        self.job_entry.insert(0, label)
        record_use("reports.job_type", label)
        self.sg_job.place_forget()

    def _on_product_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._clear_frame(self.sg_product)
        text = self.product_entry.get().strip()
        
        place_suggestions_under_entry(self.product_entry, self.sg_product, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_products(conn, text, CONFIG.autocomplete_limit)
            # Чистим историю изделий
            try:
                from utils.usage_history import get_recent, purge_missing
                from utils.text import normalize_for_search

                valid_norms = {normalize_for_search(lbl) for (_id, lbl) in rows}
                hist = get_recent("reports.product", None, CONFIG.autocomplete_limit)
                purge_missing("reports.product", valid_norms)
                cleaned_hist = [
                    h for h in hist if normalize_for_search(h) in valid_norms
                ]
            except Exception as exc:
                cleaned_hist = []
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(
                self.sg_product,
                text=label,
                command=lambda i=_id, l=label: self._pick_product(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in cleaned_hist:
            if label not in seen:
                create_suggestion_button(
                    self.sg_product,
                    text=label,
                    command=lambda l=label: self._pick_product(0, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все изделия
        if shown == 0:
            with get_connection() as conn:
                all_products = suggestions.suggest_products(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.sg_product,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_product(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_product, [self.product_entry])

    def _pick_product(self, product_id: int, label: str) -> None:
        # Если нет id (выбор из истории/текста) — сбросить id и использовать текстовый фильтр
        if product_id:
            self._selected_product_id = product_id
        else:
            self._selected_product_id = None
        self.product_entry.delete(0, "end")
        self.product_entry.insert(0, label)
        record_use("reports.product", label)
        self.sg_product.place_forget()

    def _on_contract_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._clear_frame(self.sg_contract)
        text = self.contract_entry.get().strip()
        
        place_suggestions_under_entry(self.contract_entry, self.sg_contract, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_contracts(conn, text, CONFIG.autocomplete_limit)
            # Чистим историю контрактов
            try:
                from utils.usage_history import get_recent, purge_missing
                from utils.text import normalize_for_search

                valid_norms = {normalize_for_search(lbl) for (_id, lbl) in rows}
                hist = get_recent("reports.contract", None, CONFIG.autocomplete_limit)
                purge_missing("reports.contract", valid_norms)
                cleaned_hist = [
                    h for h in hist if normalize_for_search(h) in valid_norms
                ]
            except Exception as exc:
                cleaned_hist = []
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(
                self.sg_contract,
                text=label,
                command=lambda i=_id, l=label: self._pick_contract(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in cleaned_hist:
            if label not in seen:
                create_suggestion_button(
                    self.sg_contract,
                    text=label,
                    command=lambda s=label: self._pick_contract(0, s),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все контракты
        if shown == 0:
            with get_connection() as conn:
                all_contracts = suggestions.suggest_contracts(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_contracts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.sg_contract,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_contract(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_contract, [self.contract_entry])

    def _pick_contract(self, contract_id: int, label: str) -> None:
        self._selected_contract_id = (
            contract_id if contract_id else self._selected_contract_id
        )
        self.contract_entry.delete(0, "end")
        self.contract_entry.insert(0, label)
        record_use("reports.contract", label)
        self.sg_contract.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggestions()
            return
        for frame in (
            self.sg_worker,
            self.sg_dept,
            self.sg_job,
            self.sg_product,
            self.sg_contract,
        ):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self._hide_all_suggestions()

    def _localize_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Базовое сопоставление тех. колонок к русским
        mapping = {
            "full_name": "ФИО",
            "dept": "Цех",
            "position": "Должность",
            "personnel_no": "Таб. номер",
            "product_no": "№ изд.",
            "order_no": "№ наряда",
            "quantity": "Кол-во",
        }
        # Сначала переименуем по известным ключам
        df = df.rename(columns={c: mapping.get(c, c) for c in df.columns})

        # Универсальные правила поверх: убрать подчёркивания и заменить слова
        def norm(name: str) -> str:
            s = str(name)
            s = s.replace("_", " ")
            s = s.replace("Номер изделия", "№ изд.")
            s = s.replace("Номер", "№")
            s = s.replace("Количество", "Кол-во")
            return s

        return df.rename(columns={c: norm(c) for c in df.columns})

    def _build_report(self) -> None:
        try:
            with get_connection() as conn:
                # --- Проверки и разрешение фильтров до построения отчета ---
                # 1) Вид работ: сначала используем выбранный id, иначе пробуем найти по тексту
                job_id = self._selected_job_type_id
                job_text = (self.job_entry.get() or "").strip() or None
                if job_text and not job_id:
                    try:
                        jrow = conn.execute(
                            "SELECT id FROM job_types WHERE name_norm = ?",
                            (normalize_for_search(job_text),),
                        ).fetchone()
                        if jrow:
                            job_id = int(jrow[0])
                        else:
                            messagebox.showwarning(
                                "Фильтр: Вид работ",
                                "Указанный вид работ не найден в базе. Выберите из подсказки.",
                                parent=self,
                            )
                            return
                    except Exception as exc:
                        messagebox.showwarning(
                            "Фильтр: Вид работ",
                            "Указанный вид работ не найден в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return
                if job_id:
                    exists = conn.execute(
                        "SELECT 1 FROM job_types WHERE id=?", (job_id,)
                    ).fetchone()
                    if not exists:
                        messagebox.showwarning(
                            "Фильтр: Вид работ",
                            "Выбранный вид работ отсутствует в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return

                # 2) Изделие: выбранный id или попытка найти по тексту
                p_id = self._selected_product_id
                prod_text = (self.product_entry.get() or "").strip() or None
                if (not p_id) and prod_text:
                    try:
                        row = conn.execute(
                            "SELECT id FROM products WHERE product_no = ? OR name = ?",
                            (prod_text, prod_text),
                        ).fetchone()
                        if not row:
                            norm = normalize_for_search(prod_text)
                            row = conn.execute(
                                "SELECT id FROM products WHERE product_no_norm = ? OR name_norm = ?",
                                (norm, norm),
                            ).fetchone()
                        if not row:
                            like = f"%{prod_text}%"
                            row = conn.execute(
                                "SELECT id FROM products WHERE product_no LIKE ? OR name LIKE ? LIMIT 1",
                                (like, like),
                            ).fetchone()
                        if row:
                            p_id = int(row[0])
                        else:
                            messagebox.showwarning(
                                "Фильтр: Изделие",
                                "Указанное изделие не найдено в базе. Выберите из подсказки.",
                                parent=self,
                            )
                            return
                    except Exception as exc:
                        messagebox.showwarning(
                            "Фильтр: Изделие",
                            "Указанное изделие не найдено в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return
                if p_id:
                    exists = conn.execute(
                        "SELECT 1 FROM products WHERE id=?", (p_id,)
                    ).fetchone()
                    if not exists:
                        messagebox.showwarning(
                            "Фильтр: Изделие",
                            "Выбранное изделие отсутствует в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return
                # Если поле очищено — сбрасываем id
                if not prod_text:
                    p_id = None
                    self._selected_product_id = None

                # 3) Контракт: если введен текст, попытаться найти id, иначе проверка выбранного id
                c_id = self._selected_contract_id
                cont_text = (self.contract_entry.get() or "").strip() or None
                if (not c_id) and cont_text:
                    try:
                        crow = conn.execute(
                            "SELECT id FROM contracts WHERE code_norm = ?",
                            (normalize_for_search(cont_text),),
                        ).fetchone()
                        if crow:
                            c_id = int(crow[0])
                        else:
                            messagebox.showwarning(
                                "Фильтр: Контракт",
                                "Указанный контракт не найден в базе. Выберите из подсказки.",
                                parent=self,
                            )
                            return
                    except Exception as exc:
                        messagebox.showwarning(
                            "Фильтр: Контракт",
                            "Указанный контракт не найден в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return
                if c_id:
                    exists = conn.execute(
                        "SELECT 1 FROM contracts WHERE id=?", (c_id,)
                    ).fetchone()
                    if not exists:
                        messagebox.showwarning(
                            "Фильтр: Контракт",
                            "Выбранный контракт отсутствует в базе. Выберите из подсказки.",
                            parent=self,
                        )
                        return

                # Собрать отчет
            df = work_orders_report_df(
                conn,
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                worker_id=self._selected_worker_id,
                    worker_name=self.worker_entry.get().strip() or None,
                dept=self.dept_var.get().strip() or None,
                    job_type_id=job_id,
                    product_id=p_id,
                    contract_id=c_id,
                )
        except Exception as e:
            messagebox.showerror(
                "Отчеты", f"Ошибка формирования отчета: {e}", parent=self
            )
            # Очистим превью, чтобы интерфейс не завис
            try:
                for i in self.tree.get_children():
                    self.tree.delete(i)
                self.tree["columns"] = ["msg"]
                self.tree.heading("msg", text="Ошибка формирования отчета")
                self.tree.column("msg", width=240)
                import pandas as pd

                self._df = pd.DataFrame()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            return
        try:
            self._df = self._localize_df_columns(df)
            # Уберем технические колонки из таблицы
            for c in ("Сумма_строки", "Количество", "Кол-во", "Цена"):
                if c in self._df.columns:
                    try:
                        self._df = self._df.drop(columns=[c])
                    except Exception as exc:
                        logging.getLogger(__name__).exception(
                            "Ignored unexpected error: %s", exc
                        )
            # Если отчет фактически по одному работнику или выбран фильтр по работнику — скрыть столбцы Работник и Цех
            try:
                single_worker_mode = False
                if "Работник" in self._df.columns:
                    unique_workers = [
                        str(x) for x in self._df["Работник"].dropna().unique().tolist()
                    ]
                    if len(unique_workers) == 1:
                        single_worker_mode = True
                if self._selected_worker_id or (self.worker_entry.get().strip()):
                    single_worker_mode = True
                if single_worker_mode:
                    for c in ("Работник", "Цех"):
                        if c in self._df.columns:
                            try:
                                self._df = self._df.drop(columns=[c])
                            except Exception as exc:
                                logging.getLogger(__name__).exception(
                                    "Ignored unexpected error: %s", exc
                                )
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            # Обновим статистику
            try:
                self._update_stats()
            except Exception as exc:
                self.stats_var.set("")
        # Применим локализацию заголовков в превью
        cols = list(self._df.columns)
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=str(c))
        # Заполнить данными
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self._df.itertuples(index=False):
            self.tree.insert("", "end", values=tuple(row))
            # Автоподгон ширин, чтобы не было горизонтального скролла/обрезки
            self._autosize_preview_columns()
        except Exception as e:
            messagebox.showerror(
                "Отчеты", f"Ошибка отображения отчета: {e}", parent=self
            )
            try:
                for i in self.tree.get_children():
                    self.tree.delete(i)
                self.tree["columns"] = ["msg"]
                self.tree.heading("msg", text="Ошибка отображения отчета")
                self.tree.column("msg", width=280)
                import pandas as pd

                self._df = pd.DataFrame()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            return

    def _render_preview(self, df: pd.DataFrame) -> None:
        # Clear previous
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        # Reset columns
        for c in self.tree["columns"]:
            self.tree.heading(c, text="")
            self.tree.column(c, width=50)
        self.tree["columns"] = []

        if df is None or df.empty:
            self.tree["columns"] = ["msg"]
            self.tree.heading("msg", text="Нет данных")
            self.tree.column("msg", width=200)
            try:
                self.stats_var.set("Строк: 0   Период: —   Сумма: 0.00")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            return

        cols = list(df.columns)
        self.tree["columns"] = cols

        # сортировка по заголовкам
        def sort_by(col: str):
            d = getattr(self, "_report_sort_dir", {})
            new_dir = "desc" if d.get(col) == "asc" else "asc"
            rows = []
            for iid in self.tree.get_children(""):
                vals = self.tree.item(iid, "values")
                rows.append((iid, vals))
            idx = cols.index(col)

            def key_func(item):
                v = item[1][idx]
                try:
                    return float(str(v).replace(" ", "").replace(",", "."))
                except Exception as exc:
                    return str(v)

            rows.sort(key=key_func, reverse=(new_dir == "desc"))
            for pos, (iid, _vals) in enumerate(rows):
                self.tree.move(iid, "", pos)
            if not hasattr(self, "_report_sort_dir"):
                self._report_sort_dir = {}
            self._report_sort_dir[col] = new_dir

        # Fill data
        vals_cache = df.astype(str).values.tolist()
        for r in vals_cache[:200]:
            self.tree.insert("", "end", values=r)
        for c in cols:
            self.tree.heading(c, text=str(c), command=lambda cc=c: sort_by(cc))

        # Auto-size columns to fit content (header + visible rows) and fit into window width
        try:
            font = tkfont.nametofont("TkDefaultFont")
        except Exception as exc:
            font = tkfont.Font()
        pad = 24
        min_w = 60
        # First pass: measure desired widths
        desired = []
        for j, c in enumerate(cols):
            header_w = font.measure(str(c))
            max_w = header_w
            for r in vals_cache[:200]:
                w = font.measure(str(r[j]))
                if w > max_w:
                    max_w = w
            desired.append(max(min_w, max_w + pad))
        # Compute available width of tree widget
        try:
            avail = max(200, int(self.tree.winfo_width()) - 32)
        except Exception as exc:
            avail = sum(desired)
        total_desired = sum(desired)
        # Scale down if overflow, but not below min_w
        if total_desired > 0 and avail < total_desired:
            scale = avail / total_desired
            desired = [max(min_w, int(w * scale)) for w in desired]
        for c, w in zip(cols, desired):
            self.tree.column(c, width=int(w))
        # Обновить статистику для этого пути отображения
        try:
            self._df = df
            self._update_stats()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _update_stats(self) -> None:
        df = getattr(self, "_df", None)
        if df is None or df.empty:
            self.stats_var.set("Строк: 0   Период: —   Сумма: 0.00")
            return
        # Количество строк
        rows = len(df.index)
        # Период: берем из колонки даты (ищем по русским/тех названиям)
        date_col = None
        for cand in ("Дата", "date"):
            if cand in df.columns:
                date_col = cand
                break
        period_text = "—"
        if date_col:
            try:
                s = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
                s = s.dropna()
                if not s.empty:
                    dmin = s.min().strftime("%d.%m.%Y")
                    dmax = s.max().strftime("%d.%m.%Y")
                    period_text = f"{dmin} — {dmax}"
            except Exception as exc:
                period_text = "—"
        # Сумма: попробуем несколько колонок
        total = 0.0
        for cand in ("Начислено", "Сумма", "Итог", "Итого", "total_amount", "total"):
            if cand in df.columns:
                try:
                    total = float(
                        pd.to_numeric(df[cand], errors="coerce").fillna(0).sum()
                    )
                    break
                except Exception as exc:
                    continue
        self.stats_var.set(
            f"Строк: {rows}   Период: {period_text}   Сумма: {total:.2f}"
        )

    def _autosize_preview_columns(self) -> None:
        """Подгоняет ширины колонок превью: фиксированные по содержимому, 'Вид работ'/'Работник' — резиновые.

        - Все столбцы получают ширину по содержимому (заголовок + первые ~200 строк)
        - Если суммарная ширина превышает доступное пространство, сначала сжимаем резиновые столбцы
          ("Вид работ", "Работник", также учитываем "ФИО") до минимально допустимой, затем остальные пропорционально
        - Если остаётся свободное место, распределяем его между резиновыми столбцами
        """
        df = getattr(self, "_df", None)
        if df is None or df.empty:
            return
        cols = list(df.columns)
        if not cols:
            return
        # Определяем резиновые столбцы по названиям
        names_cf = [str(c).casefold() for c in cols]
        flex_cols: list[str] = []
        for c, cf in zip(cols, names_cf):
            if ("вид работ" in cf) or ("работник" in cf) or ("фио" in cf):
                flex_cols.append(c)
        if not flex_cols:
            # Если нет явных резиновых — последний столбец сделаем резиновым
            flex_cols = [cols[-1]]

        # Измеряем желаемые ширины по содержимому
        try:
            font = tkfont.nametofont("TkDefaultFont")
        except Exception as exc:
            font = tkfont.Font()
        pad = 24
        min_fixed = 60
        min_flex = 100
        sample = df.astype(str).values.tolist()[:200]
        desired: dict[str, int] = {}
        for j, c in enumerate(cols):
            header_w = font.measure(str(c))
            max_w = header_w
            for r in sample:
                try:
                    w = font.measure(str(r[j]))
                except Exception as exc:
                    w = header_w
                if w > max_w:
                    max_w = w
            desired[c] = max(min_fixed, max_w + pad)

        # Доступная ширина виджета
        try:
            avail = int(self.tree.winfo_width() or 0)
            if avail <= 1:
                self.after(80, self._autosize_preview_columns)
                return
            # Небольшой запас на внутренние отступы
            avail = max(200, avail - 16)
        except Exception as exc:
            avail = sum(desired.values())

        nonflex_cols = [c for c in cols if c not in flex_cols]
        sum_nonflex = sum(desired[c] for c in nonflex_cols)
        # Стартовые ширины для flex — по содержимому
        widths = {c: desired[c] for c in cols}
        leftover = avail - sum_nonflex - sum(desired[c] for c in flex_cols)

        if leftover < 0:
            # Нужно сжать: сперва резиновые до min_flex
            need = -leftover
            can_shrink_flex = sum(max(0, desired[c] - min_flex) for c in flex_cols)
            shrink_left = need
            if can_shrink_flex > 0:
                for c in flex_cols:
                    cap = max(0, desired[c] - min_flex)
                    take = min(cap, shrink_left)
                    widths[c] = desired[c] - take
                    shrink_left -= take
                    if shrink_left <= 0:
                        break
            # Если всё ещё не влезает — пропорционально ужмём остальные до min_fixed
            if shrink_left > 0:
                can_shrink_fixed = sum(
                    max(0, desired[c] - min_fixed) for c in nonflex_cols
                )
                if can_shrink_fixed > 0:
                    ratio = min(1.0, shrink_left / can_shrink_fixed)
                    consumed = 0
                    for c in nonflex_cols:
                        cap = max(0, desired[c] - min_fixed)
                        take = int(cap * ratio)
                        widths[c] = desired[c] - take
                        consumed += take
                    shrink_left -= consumed
                # Если совсем не помещается — равномерно масштабируем всё не ниже минимума
                if shrink_left > 0:
                    total_now = sum(widths.values())
                    if total_now > 0:
                        scale = max(0.1, (avail / total_now))
                        for c in cols:
                            base_min = min_flex if c in flex_cols else min_fixed
                            widths[c] = max(base_min, int(widths[c] * scale))
        else:
            # Есть запас: распределим между резиновыми столбцами
            if flex_cols:
                per = leftover // len(flex_cols)
                rem = leftover - per * len(flex_cols)
                for i, c in enumerate(flex_cols):
                    extra = per + (1 if i == len(flex_cols) - 1 else 0) * rem
                    widths[c] = desired[c] + max(0, extra)

        # Применяем ширины и stretch-поведение
        for c in cols:
            try:
                self.tree.column(
                    c,
                    width=int(widths.get(c, desired.get(c, 80))),
                    stretch=(c in flex_cols),
                )
            except Exception as exc:
                try:
                    self.tree.column(c, width=int(widths.get(c, 80)))
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )

    def _build_filename_suffix(self) -> str:
        from datetime import datetime

        parts: list[str] = []
        dfrom = (self.date_from.get() or "").strip()
        dto = (self.date_to.get() or "").strip()
        if dfrom or dto:
            parts.append(f"{dfrom or '...'}-{dto or '...'}")
        if self._selected_worker_id and not self.worker_entry.get().strip():
            parts.append("по_работнику")
        if self.dept_var.get().strip():
            parts.append(f"цех_{self.dept_var.get().strip()}")
        if self._selected_job_type_id and not self.job_entry.get().strip():
            parts.append("по_виду_работ")
        if self._selected_product_id and not self.product_entry.get().strip():
            parts.append("по_изделию")
        if self._selected_contract_id and not self.contract_entry.get().strip():
            parts.append("по_контракту")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts.append(ts)
        suffix = "_".join(filter(None, parts))
        return suffix

    def _ask_save_path(
        self, title: str, defaultextension: str, filetypes: list[tuple[str, str]]
    ):
        from utils.text import sanitize_filename

        base = "отчет_по_нарядам"
        suffix = self._build_filename_suffix()
        initial = sanitize_filename(f"{base}_{suffix}") + defaultextension
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=defaultextension,
            initialfile=initial,
            filetypes=filetypes,
        )

    def _export_html(self) -> None:
        if self._df is None or self._df.empty:
            messagebox.showwarning("Экспорт HTML", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить HTML", ".html", [("HTML", "*.html")])
        if not path:
            return
        with get_connection() as conn:
            ctx = work_orders_report_context(
                conn,
                self._df,
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                dept=self.dept_var.get().strip() or None,
                worker_id=self._selected_worker_id,
                worker_name=self.worker_entry.get().strip() or None,
            )
        save_html(self._df, title="Отчет", path=path, context=ctx)
        self._open_file(path)

    def _export_pdf(self) -> None:
        if self._df is None or self._df.empty:
            messagebox.showwarning("Экспорт PDF", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить PDF", ".pdf", [("PDF", "*.pdf")])
        if not path:
            return
        # Портрет по умолчанию, но авто-подбор в save_pdf переключит, если не влезает
        with get_connection() as conn:
            ctx = work_orders_report_context(
                conn,
                self._df,
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                dept=self.dept_var.get().strip() or None,
                worker_id=self._selected_worker_id,
                worker_name=self.worker_entry.get().strip() or None,
            )
        save_pdf(
            self._df,
            file_path=path,
            title="Отчет",
            orientation=None,
            font_size=None,
            font_family=None,
            context=ctx,
        )
        self._open_file(path)

    def _export_excel(self) -> None:
        if self._df is None or self._df.empty:
            messagebox.showwarning("Экспорт Excel", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить Excel", ".xlsx", [("Excel", "*.xlsx")])
        if not path:
            return
        try:
            # Сохранение с шапкой/футером: простой вариант — отдельные листы
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                with get_connection() as conn:
                    ctx = work_orders_report_context(
                        conn,
                        self._df,
                        date_from=self.date_from.get().strip() or None,
                        date_to=self.date_to.get().strip() or None,
                        dept=self.dept_var.get().strip() or None,
                    )
                # Лист с данными
                self._df.to_excel(writer, sheet_name="Данные", index=False)
                # Лист с итогами и подписями
                summary_rows = []
                summary_rows.append(["Отчет по нарядам"])    
                if ctx.get("created_at"):
                    summary_rows.append([f"Дата составления: {ctx['created_at']}"])
                if ctx.get("period"):
                    summary_rows.append([ctx["period"]])
                if ctx.get("dept_name"):
                    summary_rows.append([f"Цех: {ctx['dept_name']}"])
                summary_rows.append([""])
                summary_rows.append(
                    [f"Итого по отчету: {ctx.get('total_amount', 0.0):.2f}"]
                )
                workers = ctx.get("worker_signatures") or []
                if workers:
                    summary_rows.append(["Подписи работников:"])
                    # по 3 в ряд
                    row = []
                    for i, w in enumerate(workers, 1):
                        row.append(w)
                        if i % 3 == 0:
                            summary_rows.append(row)
                            row = []
                    if row:
                        summary_rows.append(row)
                if ctx.get("dept_head"):
                    summary_rows.append(
                        [f"Начальник цеха: {ctx['dept_head']} _____________"]
                    )
                if ctx.get("hr_head"):
                    summary_rows.append(
                        [f"Начальник отдела кадров: {ctx['hr_head']} _____________"]
                    )
                pd.DataFrame(summary_rows).to_excel(
                    writer, sheet_name="Итоги", index=False, header=False
                )
        except Exception as e:
            messagebox.showerror(
                "Экспорт Excel", f"Ошибка сохранения: {e}\n{type(e).__name__}"
            )
            return
        self._open_file(path)

    def _export_1c_json(self) -> None:
        # Экспорт в 1С: единый формат JSON
        from reports.export_1c import build_orders_unified, save_1c_json

        base_path = filedialog.asksaveasfilename(
            title="Сохранить JSON для 1С",
            defaultextension=".json",
            initialfile="выгрузка_1с.json",
            filetypes=[("JSON", "*.json")],
        )
        if not base_path:
            return
        # Собрать данные
        with get_connection() as conn:
            kwargs = dict(
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                product_id=self._selected_product_id,
                contract_id=self._selected_contract_id,
                worker_id=self._selected_worker_id,
                worker_name=self.worker_entry.get().strip() or None,
                dept=self.dept_var.get().strip() or None,
                job_type_id=self._selected_job_type_id,
            )
            orders = build_orders_unified(conn, **kwargs)
        meta = {
            "date_from": self.date_from.get().strip() or None,
            "date_to": self.date_to.get().strip() or None,
            "product_id": self._selected_product_id,
            "contract_id": self._selected_contract_id,
            "worker_id": self._selected_worker_id,
            "worker_name": self.worker_entry.get().strip() or None,
            "dept": self.dept_var.get().strip() or None,
            "job_type_id": self._selected_job_type_id,
        }
        try:
            save_1c_json(path=base_path, orders=orders, meta=meta, encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Экспорт 1С", f"Ошибка экспорта: {e}")
            return
        self._open_file(str(base_path))

    def _open_date_picker(self, var, anchor=None) -> None:
        from gui.widgets.date_picker import open_for_anchor

        self._hide_all_suggestions()
        if anchor is None:
            return
        open_for_anchor(self, anchor, var.get().strip(), lambda d: var.set(d))

    def _open_file(self, path: str) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
