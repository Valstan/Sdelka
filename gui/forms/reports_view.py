from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

from config.settings import CONFIG
from db.sqlite import get_connection
from services import suggestions
from reports.report_builders import work_orders_report_df
from reports.html_export import save_html
from reports.pdf_reportlab import save_pdf
from utils.usage_history import record_use, get_recent


class ReportsView(ctk.CTkFrame):
    def __init__(self, master) -> None:
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
        ctk.CTkEntry(filters, textvariable=self.date_from, width=120).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(filters, text="по").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(filters, textvariable=self.date_to, width=120).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Worker
        ctk.CTkLabel(filters, text="Работник").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.worker_entry = ctk.CTkEntry(filters, placeholder_text="ФИО", width=240)
        self.worker_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.worker_entry.bind("<KeyRelease>", self._on_worker_key)
        self.worker_entry.bind("<FocusIn>", lambda e: self._on_worker_key())

        # Dept
        ctk.CTkLabel(filters, text="Цех").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.dept_var = ctk.StringVar()
        self.dept_entry = ctk.CTkEntry(filters, textvariable=self.dept_var, width=120)
        self.dept_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.dept_entry.bind("<KeyRelease>", self._on_dept_key)
        self.dept_entry.bind("<FocusIn>", lambda e: self._on_dept_key())

        # Job type
        ctk.CTkLabel(filters, text="Вид работ").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.job_entry = ctk.CTkEntry(filters, placeholder_text="Название вида", width=240)
        self.job_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.job_entry.bind("<KeyRelease>", self._on_job_key)
        self.job_entry.bind("<FocusIn>", lambda e: self._on_job_key())

        # Product
        ctk.CTkLabel(filters, text="Изделие").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.product_entry = ctk.CTkEntry(filters, placeholder_text="Номер/Название", width=240)
        self.product_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.product_entry.bind("<KeyRelease>", self._on_product_key)
        self.product_entry.bind("<FocusIn>", lambda e: self._on_product_key())

        # Contract
        ctk.CTkLabel(filters, text="Контракт").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.contract_entry = ctk.CTkEntry(filters, placeholder_text="Шифр", width=160)
        self.contract_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.contract_entry.bind("<KeyRelease>", self._on_contract_key)
        self.contract_entry.bind("<FocusIn>", lambda e: self._on_contract_key())

        ctk.CTkButton(filters, text="Сформировать", command=self._build_report).grid(row=3, column=3, padx=5, pady=5, sticky="e")

        # Suggest frames
        self.sg_worker = ctk.CTkFrame(self)
        self.sg_worker.place_forget()
        self.sg_dept = ctk.CTkFrame(self)
        self.sg_dept.place_forget()
        self.sg_job = ctk.CTkFrame(self)
        self.sg_job.place_forget()
        self.sg_product = ctk.CTkFrame(self)
        self.sg_product.place_forget()
        self.sg_contract = ctk.CTkFrame(self)
        self.sg_contract.place_forget()

        # Preview and export
        preview = ctk.CTkFrame(self)
        preview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        toolbar = ctk.CTkFrame(preview)
        toolbar.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Экспорт HTML", command=self._export_html).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт PDF", command=self._export_pdf).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт Excel", command=self._export_excel).pack(side="left", padx=4)

        self.tree = ttk.Treeview(preview, show="headings")
        self.tree.pack(fill="both", expand=True)

    def _place_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        x = entry.winfo_rootx() - self.winfo_rootx()
        y = entry.winfo_rooty() - self.winfo_rooty() + entry.winfo_height()
        frame.place(x=x, y=y)
        frame.lift()

    def _clear_frame(self, frame: ctk.CTkFrame) -> None:
        for w in frame.winfo_children():
            w.destroy()

    def _hide_all_suggestions(self) -> None:
        self.sg_worker.place_forget()
        self.sg_dept.place_forget()
        self.sg_job.place_forget()
        self.sg_product.place_forget()
        self.sg_contract.place_forget()

    def _on_worker_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._selected_worker_id = None
        self._clear_frame(self.sg_worker)
        text = self.worker_entry.get().strip()
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_workers(conn, text, CONFIG.autocomplete_limit)
        self._place_under(self.worker_entry, self.sg_worker)
        seen: set[str] = set()
        for _id, label in rows:
            seen.add(label)
            ctk.CTkButton(self.sg_worker, text=label, command=lambda i=_id, l=label: self._pick_worker(i, l)).pack(fill="x")
        for label in get_recent("reports.worker", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                ctk.CTkButton(self.sg_worker, text=label, command=lambda l=label: self._pick_worker(0, l)).pack(fill="x")

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
        with get_connection(CONFIG.db_path) as conn:
            vals = suggestions.suggest_depts(conn, text, CONFIG.autocomplete_limit)
        self._place_under(self.dept_entry, self.sg_dept)
        seen = set()
        for v in vals:
            seen.add(v)
            ctk.CTkButton(self.sg_dept, text=v, command=lambda s=v: self._pick_dept(s)).pack(fill="x")
        for label in get_recent("reports.dept", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                ctk.CTkButton(self.sg_dept, text=label, command=lambda s=label: self._pick_dept(s)).pack(fill="x")

    def _pick_dept(self, val: str) -> None:
        self.dept_var.set(val)
        record_use("reports.dept", val)
        self.sg_dept.place_forget()

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggestions()
        self._clear_frame(self.sg_job)
        text = self.job_entry.get().strip()
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_job_types(conn, text, CONFIG.autocomplete_limit)
        self._place_under(self.job_entry, self.sg_job)
        seen = set()
        for _id, label in rows:
            seen.add(label)
            ctk.CTkButton(self.sg_job, text=label, command=lambda i=_id, l=label: self._pick_job(i, l)).pack(fill="x")
        for label in get_recent("reports.job_type", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                ctk.CTkButton(self.sg_job, text=label, command=lambda l=label: self._pick_job(0, l)).pack(fill="x")

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
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_products(conn, text, CONFIG.autocomplete_limit)
        self._place_under(self.product_entry, self.sg_product)
        seen = set()
        for _id, label in rows:
            seen.add(label)
            ctk.CTkButton(self.sg_product, text=label, command=lambda i=_id, l=label: self._pick_product(i, l)).pack(fill="x")
        for label in get_recent("reports.product", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                ctk.CTkButton(self.sg_product, text=label, command=lambda l=label: self._pick_product(0, l)).pack(fill="x")

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
        with get_connection(CONFIG.db_path) as conn:
            rows = suggestions.suggest_contracts(conn, text, CONFIG.autocomplete_limit)
        self._place_under(self.contract_entry, self.sg_contract)
        seen = set()
        for _id, label in rows:
            seen.add(label)
            ctk.CTkButton(self.sg_contract, text=label, command=lambda i=_id, l=label: self._pick_contract(i, l)).pack(fill="x")
        for label in get_recent("reports.contract", text or None, CONFIG.autocomplete_limit):
            if label not in seen:
                ctk.CTkButton(self.sg_contract, text=label, command=lambda l=label: self._pick_contract(0, l)).pack(fill="x")

    def _pick_contract(self, contract_id: int, label: str) -> None:
        self._selected_contract_id = contract_id if contract_id else self._selected_contract_id
        self.contract_entry.delete(0, "end")
        self.contract_entry.insert(0, label)
        record_use("reports.contract", label)
        self.sg_contract.place_forget()

    def _localize_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Общий словарь для потенциально англ. колонок -> русские названия
        mapping = {
            # workers
            "id": "Идентификатор",
            "full_name": "ФИО",
            "dept": "Цех",
            "position": "Должность",
            "personnel_no": "Табельный номер",
            # job_types
            "name": "Наименование",
            "unit": "Ед. изм.",
            "price": "Цена",
            # products
            "product_no": "Номер изделия",
            # contracts
            "code": "Шифр контракта",
            "start_date": "Дата начала",
            "end_date": "Дата окончания",
            "description": "Описание",
            # work_orders
            "order_no": "№ наряда",
            "date": "Дата",
            "product_id": "ID изделия",
            "contract_id": "ID контракта",
            "total_amount": "Итоговая сумма",
            # items
            "work_order_id": "ID наряда",
            "job_type_id": "ID вида работ",
            "quantity": "Количество",
            "unit_price": "Цена",
            "line_amount": "Сумма",
            "worker_id": "ID работника",
        }
        # Если df уже с русскими заголовками, rename ничего не изменит
        return df.rename(columns={c: mapping.get(c, c) for c in df.columns})

    def _build_report(self) -> None:
        with get_connection(CONFIG.db_path) as conn:
            df = work_orders_report_df(
                conn,
                date_from=self.date_from.get().strip() or None,
                date_to=self.date_to.get().strip() or None,
                worker_id=self._selected_worker_id,
                dept=self.dept_var.get().strip() or None,
                job_type_id=self._selected_job_type_id,
                product_id=self._selected_product_id,
                contract_id=self._selected_contract_id,
            )
        self._df = self._localize_df_columns(df)
        self._render_preview(self._df)

    def _render_preview(self, df: pd.DataFrame) -> None:
        # Clear previous
        for col in self.tree.get_children():
            self.tree.delete(col)
        self.tree["columns"] = []
        for c in self.tree["columns"]:
            self.tree.heading(c, text="")

        if df is None or df.empty:
            self.tree["columns"] = ["msg"]
            self.tree.heading("msg", text="Нет данных")
            return

        cols = list(df.columns)
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=str(c))
            self.tree.column(c, width=120)

        # Limit rows in preview
        for _, row in df.head(200).iterrows():
            values = [row[c] for c in cols]
            self.tree.insert("", "end", values=values)

    def _ask_save_path(self, title: str, defaultextension: str, filetypes: list[tuple[str, str]]):
        return filedialog.asksaveasfilename(title=title, defaultextension=defaultextension, filetypes=filetypes)

    def _export_html(self) -> None:
        if self._df is None:
            messagebox.showwarning("Экспорт", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить HTML", ".html", [("HTML", "*.html")])
        if not path:
            return
        save_html(self._df, path, title="Отчет по нарядам")
        messagebox.showinfo("Экспорт", "HTML сохранен")

    def _export_pdf(self) -> None:
        if self._df is None:
            messagebox.showwarning("Экспорт", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить PDF", ".pdf", [("PDF", "*.pdf")])
        if not path:
            return
        save_pdf(self._df, path, title="Отчет по нарядам")
        messagebox.showinfo("Экспорт", "PDF сохранен")

    def _export_excel(self) -> None:
        if self._df is None:
            messagebox.showwarning("Экспорт", "Сначала сформируйте отчет")
            return
        path = self._ask_save_path("Сохранить Excel", ".xlsx", [("Excel", "*.xlsx")])
        if not path:
            return
        self._df.to_excel(path, index=False)
        messagebox.showinfo("Экспорт", "Excel сохранен")