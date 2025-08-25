from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys
import subprocess

from config.settings import CONFIG
from db.sqlite import get_connection
from services import suggestions
from reports.report_builders import work_orders_report_df, work_orders_report_context
from reports.html_export import save_html
from reports.pdf_reportlab import save_pdf
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry, 
    create_suggestion_button, 
    create_suggestions_frame
)


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._selected_worker_id: int | None = None
        self._selected_job_type_id: int | None = None
        self._selected_product_id: int | None = None
        self._selected_contract_id: int | None = None
        self._df: pd.DataFrame | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        filters = ctk.CTkFrame(self)
        filters.pack(fill="x", padx=10, pady=10)

        # Dates
        self.date_from = ctk.StringVar()
        self.date_to = ctk.StringVar()
        ctk.CTkLabel(filters, text="Период с").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_from_entry = ctk.CTkEntry(filters, textvariable=self.date_from, width=120)
        self.date_from_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.date_from_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.date_from, self.date_from_entry))
        
        ctk.CTkLabel(filters, text="по").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.date_to_entry = ctk.CTkEntry(filters, textvariable=self.date_to, width=120)
        self.date_to_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.date_to_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.date_to, self.date_to_entry))

        # Worker
        ctk.CTkLabel(filters, text="Работник").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.worker_entry = ctk.CTkEntry(filters, placeholder_text="ФИО", width=240)
        self.worker_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.worker_entry.bind("<KeyRelease>", self._on_worker_key)
        self.worker_entry.bind("<FocusIn>", lambda e: self._on_worker_key())
        self.worker_entry.bind("<Button-1>", lambda e: self.after(1, self._on_worker_key))

        # Dept
        ctk.CTkLabel(filters, text="Цех").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.dept_var = ctk.StringVar()
        self.dept_entry = ctk.CTkEntry(filters, textvariable=self.dept_var, width=120)
        self.dept_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.dept_entry.bind("<KeyRelease>", self._on_dept_key)
        self.dept_entry.bind("<FocusIn>", lambda e: self._on_dept_key())
        self.dept_entry.bind("<Button-1>", lambda e: self.after(1, self._on_dept_key))

        # Job type
        ctk.CTkLabel(filters, text="Вид работ").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.job_entry = ctk.CTkEntry(filters, placeholder_text="Название вида", width=240)
        self.job_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.job_entry.bind("<KeyRelease>", self._on_job_key)
        self.job_entry.bind("<FocusIn>", lambda e: self._on_job_key())
        self.job_entry.bind("<Button-1>", lambda e: self.after(1, self._on_job_key))

        # Product
        ctk.CTkLabel(filters, text="Изделие").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.product_entry = ctk.CTkEntry(filters, placeholder_text="Номер/Название", width=240)
        self.product_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.product_entry.bind("<KeyRelease>", self._on_product_key)
        self.product_entry.bind("<FocusIn>", lambda e: self._on_product_key())
        self.product_entry.bind("<Button-1>", lambda e: self.after(1, self._on_product_key))

        # Contract
        ctk.CTkLabel(filters, text="Контракт").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.contract_entry = ctk.CTkEntry(filters, placeholder_text="Шифр", width=160)
        self.contract_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)
        self.contract_entry.bind("<FocusIn>", lambda e: self._on_contract_key())
        self.contract_entry.bind("<Button-1>", lambda e: self.after(1, self._on_contract_key))

        ctk.CTkButton(filters, text="Сформировать", command=self._build_report).grid(row=3, column=3, padx=5, pady=5, sticky="e")

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
        ctk.CTkButton(toolbar, text="Экспорт HTML", command=self._export_html).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт PDF", command=self._export_pdf).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт Excel", command=self._export_excel).pack(side="left", padx=4)

        # Простая табличка предпросмотра списка (не обязательна для печати)
        self.tree = ttk.Treeview(self, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        vsb.place_forget(); hsb.place_forget()  # оставим без явных скроллов

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

    def _on_worker_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._selected_worker_id = None
        self._clear_frame(self.sg_worker)
        text = self.worker_entry.get().strip()
        
        place_suggestions_under_entry(self.worker_entry, self.sg_worker, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_workers(conn, text, CONFIG.autocomplete_limit)
        
        seen: set[str] = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(self.sg_worker, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("reports.worker", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                create_suggestion_button(self.sg_worker, text=label, command=lambda l=label: self._pick_worker(0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем всех работников
        if shown == 0:
            with get_connection() as conn:
                all_workers = suggestions.suggest_workers(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_workers:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.sg_worker, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x", padx=2, pady=1)
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
            create_suggestion_button(self.sg_dept, text=v, command=lambda s=v: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("reports.dept", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                create_suggestion_button(self.sg_dept, text=label, command=lambda s=label: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все цеха
        if shown == 0:
            with get_connection() as conn:
                all_depts = suggestions.suggest_depts(conn, "", CONFIG.autocomplete_limit)
            for dept in all_depts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.sg_dept, text=dept, command=lambda s=dept: self._pick_dept(s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_dept, [self.dept_entry])

    def _pick_dept(self, val: str) -> None:
        self.dept_var.set(val)
        record_use("reports.dept", val)
        self.sg_dept.place_forget()

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._clear_frame(self.sg_job)
        text = self.job_entry.get().strip()
        
        place_suggestions_under_entry(self.job_entry, self.sg_job, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_job_types(conn, text, CONFIG.autocomplete_limit)
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(self.sg_job, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("reports.job_type", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                create_suggestion_button(self.sg_job, text=label, command=lambda l=label: self._pick_job(0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все виды работ
        if shown == 0:
            with get_connection() as conn:
                all_job_types = suggestions.suggest_job_types(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_job_types:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.sg_job, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_job, [self.job_entry])

    def _pick_job(self, job_type_id: int, label: str) -> None:
        self._selected_job_type_id = job_type_id if job_type_id else self._selected_job_type_id
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
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(self.sg_product, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("reports.product", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                create_suggestion_button(self.sg_product, text=label, command=lambda l=label: self._pick_product(0, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все изделия
        if shown == 0:
            with get_connection() as conn:
                all_products = suggestions.suggest_products(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.sg_product, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_product, [self.product_entry])

    def _pick_product(self, product_id: int, label: str) -> None:
        self._selected_product_id = product_id if product_id else self._selected_product_id
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
        
        seen = set()
        shown = 0
        for _id, label in rows:
            seen.add(label)
            create_suggestion_button(self.sg_contract, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent("reports.contract", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                create_suggestion_button(self.sg_contract, text=label, command=lambda s=label: self._pick_contract(0, s)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все контракты
        if shown == 0:
            with get_connection() as conn:
                all_contracts = suggestions.suggest_contracts(conn, "", CONFIG.autocomplete_limit)
            for _id, label in all_contracts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(self.sg_contract, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        self._schedule_auto_hide(self.sg_contract, [self.contract_entry])

    def _pick_contract(self, contract_id: int, label: str) -> None:
        self._selected_contract_id = contract_id if contract_id else self._selected_contract_id
        self.contract_entry.delete(0, "end")
        self.contract_entry.insert(0, label)
        record_use("reports.contract", label)
        self.sg_contract.place_forget()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggestions()
            return
        for frame in (self.sg_worker, self.sg_dept, self.sg_job, self.sg_product, self.sg_contract):
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
        with get_connection() as conn:
            df = work_orders_report_df(
                conn,
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                worker_id=self._selected_worker_id,
                worker_name=self.worker_entry.get().strip() or None,
                dept=self.dept_var.get().strip() or None,
                job_type_id=self._selected_job_type_id,
                product_id=self._selected_product_id,
                contract_id=self._selected_contract_id,
            )
        self._df = self._localize_df_columns(df)
        # Уберем технические колонки из таблицы
        for c in ("Сумма_строки", "Количество", "Кол-во", "Цена"):
            if c in self._df.columns:
                try:
                    self._df = self._df.drop(columns=[c])
                except Exception:
                    pass
        # Если выбран конкретный работник — скрыть столбцы Работник и Цех (они будут в шапке)
        if self._selected_worker_id:
            for c in ("Работник", "Цех"):
                if c in self._df.columns:
                    try:
                        self._df = self._df.drop(columns=[c])
                    except Exception:
                        pass
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
                except Exception:
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
        except Exception:
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
        except Exception:
            avail = sum(desired)
        total_desired = sum(desired)
        # Scale down if overflow, but not below min_w
        if total_desired > 0 and avail < total_desired:
            scale = avail / total_desired
            desired = [max(min_w, int(w * scale)) for w in desired]
        for c, w in zip(cols, desired):
            self.tree.column(c, width=int(w))

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

    def _ask_save_path(self, title: str, defaultextension: str, filetypes: list[tuple[str, str]]):
        from utils.text import sanitize_filename
        base = "отчет_по_нарядам"
        suffix = self._build_filename_suffix()
        initial = sanitize_filename(f"{base}_{suffix}") + defaultextension
        return filedialog.asksaveasfilename(title=title, defaultextension=defaultextension, initialfile=initial, filetypes=filetypes)

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
            )
        save_pdf(self._df, file_path=path, title="Отчет", orientation=None, font_size=None, font_family=None, context=ctx)
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
                summary_rows.append([f"Итого по отчету: {ctx.get('total_amount', 0.0):.2f}"])
                workers = ctx.get("worker_signatures") or []
                if workers:
                    summary_rows.append(["Подписи работников:"])
                    # по 3 в ряд
                    row = []
                    for i, w in enumerate(workers, 1):
                        row.append(w)
                        if i % 3 == 0:
                            summary_rows.append(row); row = []
                    if row:
                        summary_rows.append(row)
                if ctx.get("dept_head"):
                    summary_rows.append([f"Начальник цеха: {ctx['dept_head']} _____________"]) 
                if ctx.get("hr_head"):
                    summary_rows.append([f"Начальник отдела кадров: {ctx['hr_head']} _____________"]) 
                pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Итоги", index=False, header=False)
        except Exception as e:
            messagebox.showerror("Экспорт Excel", f"Ошибка сохранения: {e}\n{type(e).__name__}")
            return
        self._open_file(path)

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
        except Exception:
            pass