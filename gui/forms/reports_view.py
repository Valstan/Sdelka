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
        self.date_from_entry = ctk.CTkEntry(filters, textvariable=self.date_from, width=120)
        self.date_from_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.date_from_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.date_from, self.date_from_entry))
        self.date_from_entry.bind("<Button-1>", lambda e: self.after(1, lambda: self._open_date_picker(self.date_from, self.date_from_entry)))
        ctk.CTkLabel(filters, text="по").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.date_to_entry = ctk.CTkEntry(filters, textvariable=self.date_to, width=120)
        self.date_to_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.date_to_entry.bind("<FocusIn>", lambda e: self._open_date_picker(self.date_to, self.date_to_entry))
        self.date_to_entry.bind("<Button-1>", lambda e: self.after(1, lambda: self._open_date_picker(self.date_to, self.date_to_entry)))

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

        # Глобальный клик по корневому окну — скрыть подсказки, если клик вне списков
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

        # Preview and export
        preview = ctk.CTkFrame(self)
        preview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        toolbar = ctk.CTkFrame(preview)
        toolbar.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Экспорт HTML", command=lambda: self._open_preview("html")).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт PDF", command=lambda: self._open_preview("pdf")).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Экспорт Excel", command=lambda: self._open_preview("excel")).pack(side="left", padx=4)

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
        self._schedule_auto_hide(self.sg_dept, [self.dept_entry])

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
        # сортировка по заголовкам
        def sort_by(col: str):
            # toggle dir
            d = getattr(self, "_report_sort_dir", {})
            new_dir = "desc" if d.get(col) == "asc" else "asc"
            # собрать текущие значения в список и отсортировать
            rows = []
            for iid in self.tree.get_children(""):
                vals = self.tree.item(iid, "values")
                rows.append((iid, vals))
            idx = cols.index(col)
            def key_func(item):
                v = item[1][idx]
                # попытка числовой сортировки
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
        for c in cols:
            self.tree.heading(c, text=str(c), command=lambda cc=c: sort_by(cc))
            self.tree.column(c, width=120)

        # Limit rows in preview
        for _, row in df.head(200).iterrows():
            values = [row[c] for c in cols]
            self.tree.insert("", "end", values=values)

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
        # Переопределено: вызываем предпросмотр
        self._open_preview("html")

    def _export_pdf(self) -> None:
        self._open_preview("pdf")

    def _export_excel(self) -> None:
        self._open_preview("excel")

    def _open_date_picker(self, var, anchor=None) -> None:
        from gui.widgets.date_picker import DatePicker
        self._hide_all_suggestions()
        DatePicker(self, var.get().strip(), lambda d: var.set(d), anchor=anchor)

    def _open_preview(self, fmt: str) -> None:
        if self._df is None or self._df.empty:
            messagebox.showwarning("Предпросмотр", "Сначала сформируйте отчет")
            return
        win = ctk.CTkToplevel(self)
        win.title(f"Предпросмотр ({fmt.upper()})")
        win.geometry("980x700")
        win.grab_set()
        # Панели настроек (2 строки для адаптивности)
        panel_top = ctk.CTkFrame(win)
        panel_top.pack(fill="x", padx=10, pady=(8, 4))
        panel_bottom = ctk.CTkFrame(win)
        panel_bottom.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(panel_top, text="Шрифт").pack(side="left", padx=4)
        font_family = ctk.StringVar(value="Авто")
        font_opts = ["Авто", "DejaVu Sans", "Noto Sans", "Arial", "Liberation Sans"]
        font_menu = ctk.CTkOptionMenu(panel_top, values=font_opts, variable=font_family)
        font_menu.pack(side="left")
        ctk.CTkLabel(panel_top, text="Размер шрифта").pack(side="left", padx=6)
        font_size = ctk.StringVar(value="14")
        size_values = [str(i) for i in range(10, 19)]
        size_menu = ctk.CTkOptionMenu(panel_top, values=size_values, variable=font_size)
        size_menu.pack(side="left")
        ctk.CTkLabel(panel_top, text="Ориентация").pack(side="left", padx=6)
        orient = ctk.StringVar(value="Автоматически")
        orient_menu = ctk.CTkOptionMenu(panel_top, values=["Автоматически", "Портрет", "Альбом"], variable=orient)
        orient_menu.pack(side="left")

        # Поля и кнопки на второй строке
        ctk.CTkLabel(panel_bottom, text="Поля:").pack(side="left", padx=(4, 8))
        ctk.CTkLabel(panel_bottom, text="Левое").pack(side="left", padx=(4, 2))
        left_margin = ctk.StringVar(value="15")
        margin_vals = [str(i) for i in range(2, 21, 2)]
        ctk.CTkOptionMenu(panel_bottom, values=margin_vals, variable=left_margin, width=60, command=lambda _: update_preview()).pack(side="left")
        ctk.CTkLabel(panel_bottom, text="Правое").pack(side="left", padx=(8, 2))
        right_margin = ctk.StringVar(value="15")
        ctk.CTkOptionMenu(panel_bottom, values=margin_vals, variable=right_margin, width=60, command=lambda _: update_preview()).pack(side="left")
        ctk.CTkLabel(panel_bottom, text="Верхнее").pack(side="left", padx=(8, 2))
        top_margin = ctk.StringVar(value="15")
        ctk.CTkOptionMenu(panel_bottom, values=margin_vals, variable=top_margin, width=60, command=lambda _: update_preview()).pack(side="left")
        ctk.CTkLabel(panel_bottom, text="Нижнее").pack(side="left", padx=(8, 2))
        bottom_margin = ctk.StringVar(value="15")
        ctk.CTkOptionMenu(panel_bottom, values=margin_vals, variable=bottom_margin, width=60, command=lambda _: update_preview()).pack(side="left")

        btns = ctk.CTkFrame(panel_bottom)
        btns.pack(side="right")

        # Область предпросмотра (внутри окна)
        body = ctk.CTkFrame(win)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Контейнер под разные типы предпросмотра
        preview_container = ctk.CTkFrame(body)
        preview_container.pack(fill="both", expand=True)
        # Держатели виджетов
        holder = {"widget": None}

        def clear_container():
            if holder["widget"] is not None:
                try:
                    holder["widget"].destroy()
                except Exception:
                    pass
                holder["widget"] = None

        def show_table_preview():
            clear_container()
            tree = ttk.Treeview(preview_container, show="headings")
            tree.pack(fill="both", expand=True)
            # колонки
            cols = list(self._df.columns)
            tree["columns"] = cols
            for col in cols:
                tree.heading(col, text=str(col), command=lambda cc=col: sort_preview_tree(tree, cols, cc))
                tree.column(col, width=140)
            for _, row in self._df.head(200).iterrows():
                tree.insert("", "end", values=[row[c] for c in cols])
            holder["widget"] = tree

        def show_html_preview():
            clear_container()
            # Генерируем HTML строку
            html = self._df.to_html(index=False)
            try:
                from tkhtmlview import HTMLLabel  # type: ignore
                widget = HTMLLabel(preview_container, html=html)
                widget.pack(fill="both", expand=True)
                holder["widget"] = widget
            except Exception:
                # Фолбек: показать исходный HTML в текстовом окне
                txt = ctk.CTkTextbox(preview_container)
                txt.pack(fill="both", expand=True)
                txt.insert("end", html)
                holder["widget"] = txt

        def show_pdf_preview():
            clear_container()
            # Попытка конвертировать PDF в изображение
            import tempfile, os
            from datetime import datetime
            try:
                tmp_path = os.path.join(tempfile.gettempdir(), f"report_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                save_pdf(
                    self._df,
                    tmp_path,
                    title="Отчет по нарядам",
                    orientation=map_orientation_rus(orient.get()),
                    font_size=int(font_size.get()),
                    font_family=map_font_family(font_family.get()),
                    margins_mm=(int(left_margin.get()), int(right_margin.get()), int(top_margin.get()), int(bottom_margin.get())),
                )
                from pdf2image import convert_from_path  # type: ignore
                from PIL import ImageTk  # type: ignore
                images = convert_from_path(tmp_path, dpi=120, first_page=1, last_page=1)
                if not images:
                    raise RuntimeError("Не удалось отобразить PDF")
                img = images[0]
                lbl = ctk.CTkLabel(preview_container, text="")
                lbl.pack(fill="both", expand=True)
                holder["widget"] = lbl
                # сохранить ссылку, чтобы не собрать GC
                lbl._img_ref = ImageTk.PhotoImage(img)
                lbl.configure(image=lbl._img_ref)
            except Exception as exc:
                # Фолбек на табличный вид
                show_table_preview()

        import os, tempfile, sys, subprocess
        from datetime import datetime

        tmp_file = {"path": None}

        def map_orientation_rus(val: str) -> str | None:
            if val == "Автоматически":
                return None
            if val == "Портрет":
                return "portrait"
            if val == "Альбом":
                return "landscape"
            return None

        def map_font_family(val: str) -> str | None:
            if val == "Авто":
                return None
            # Для остальных полагаемся на авто-поиск TTF
            return None

        def update_preview() -> None:
            if fmt == "html":
                show_html_preview()
            elif fmt == "pdf":
                show_pdf_preview()
            else:
                show_table_preview()

        def do_save() -> None:
            if fmt == "html":
                path = self._ask_save_path("Сохранить HTML", ".html", [("HTML", "*.html")])
                if not path:
                    return
                save_html(self._df, path, title="Отчет по нарядам")
                messagebox.showinfo("Экспорт", "HTML сохранен")
            elif fmt == "pdf":
                path = self._ask_save_path("Сохранить PDF", ".pdf", [("PDF", "*.pdf")])
                if not path:
                    return
                save_pdf(
                    self._df,
                    path,
                    title="Отчет по нарядам",
                    orientation=map_orientation_rus(orient.get()),
                    font_size=int(font_size.get()),
                    font_family=map_font_family(font_family.get()),
                    margins_mm=(int(left_margin.get()), int(right_margin.get()), int(top_margin.get()), int(bottom_margin.get())),
                )
                messagebox.showinfo("Экспорт", "PDF сохранен")
            else:  # excel
                path = self._ask_save_path("Сохранить Excel", ".xlsx", [("Excel", "*.xlsx")])
                if not path:
                    return
                self._df.to_excel(path, index=False)
                messagebox.showinfo("Экспорт", "Excel сохранен")

        def do_print() -> None:
            if fmt != "pdf":
                messagebox.showinfo("Печать", "Печать доступна из PDF")
                return
            # Сгенерировать временный PDF с текущими настройками и отправить на печать
            try:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(tempfile.gettempdir(), f"report_print_{stamp}.pdf")
                save_pdf(
                    self._df,
                    path,
                    title="Отчет по нарядам",
                    orientation=map_orientation_rus(orient.get()),
                    font_size=int(font_size.get()),
                    font_family=map_font_family(font_family.get()),
                    margins_mm=(int(left_margin.get()), int(right_margin.get()), int(top_margin.get()), int(bottom_margin.get())),
                )
                if sys.platform == "win32":
                    try:
                        import win32api  # type: ignore
                        win32api.ShellExecute(0, "print", path, None, ".", 0)
                    except Exception:
                        os.startfile(path, "print")  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.run(["lp", path], check=False)
                else:
                    rc = subprocess.run(["lp", path]).returncode
                    if rc != 0:
                        subprocess.Popen(["xdg-open", path])
            except Exception as exc:
                messagebox.showerror("Печать", f"Не удалось отправить на печать: {exc}")

        ctk.CTkButton(btns, text="Сохранить", command=do_save).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Печать", command=do_print).pack(side="left", padx=4)

        # Автообновление предпросмотра при изменении настроек
        font_menu.configure(command=lambda _: update_preview())
        size_menu.configure(command=lambda _: update_preview())
        orient_menu.configure(command=lambda _: update_preview())

        def sort_preview_tree(tree: ttk.Treeview, cols: list[str], col: str):
            d = getattr(tree, "_sort_dir", {})
            new_dir = "desc" if d.get(col) == "asc" else "asc"
            items = []
            for iid in tree.get_children(""):
                items.append((iid, tree.item(iid, "values")))
            idx = cols.index(col)
            def key_func(item):
                v = item[1][idx]
                try:
                    return float(str(v).replace(" ", "").replace(",", "."))
                except Exception:
                    return str(v)
            items.sort(key=key_func, reverse=(new_dir == "desc"))
            for pos, (iid, _vals) in enumerate(items):
                tree.move(iid, "", pos)
            tree._sort_dir = {col: new_dir}

        # Инициализация предпросмотра
        update_preview()