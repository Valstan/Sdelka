from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox

from config.settings import CONFIG
from db.sqlite import get_connection
from import_export.excel_io import (
    import_workers_from_excel,
    import_job_types_from_excel,
    import_products_from_excel,
    import_contracts_from_excel,
    export_table_to_excel,
    export_all_tables_to_excel,
    generate_workers_template,
    generate_job_types_template,
    generate_products_template,
    generate_contracts_template,
)


class ImportExportView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._build_ui()

    def _build_ui(self) -> None:
        row1 = ctk.CTkFrame(self)
        row1.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(row1, text="Импорт из Excel").pack(anchor="w")
        ctk.CTkButton(row1, text="Импорт Работников", command=self._import_workers).pack(side="left", padx=5)
        ctk.CTkButton(row1, text="Импорт Видов работ", command=self._import_jobs).pack(side="left", padx=5)
        ctk.CTkButton(row1, text="Импорт Изделий", command=self._import_products).pack(side="left", padx=5)
        ctk.CTkButton(row1, text="Импорт Контрактов", command=self._import_contracts).pack(side="left", padx=5)

        row2 = ctk.CTkFrame(self)
        row2.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(row2, text="Экспорт таблиц").pack(anchor="w")
        ctk.CTkButton(row2, text="Экспорт Работников", command=lambda: self._export_table("workers")).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Экспорт Видов работ", command=lambda: self._export_table("job_types")).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Экспорт Изделий", command=lambda: self._export_table("products")).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Экспорт Контрактов", command=lambda: self._export_table("contracts")).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Экспорт всего набора", command=self._export_all).pack(side="left", padx=5)

        row3 = ctk.CTkFrame(self)
        row3.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(row3, text="Шаблоны Excel").pack(anchor="w")
        ctk.CTkButton(row3, text="Шаблон Работники", command=lambda: self._save_template("workers")).pack(side="left", padx=5)
        ctk.CTkButton(row3, text="Шаблон Виды работ", command=lambda: self._save_template("job_types")).pack(side="left", padx=5)
        ctk.CTkButton(row3, text="Шаблон Изделия", command=lambda: self._save_template("products")).pack(side="left", padx=5)
        ctk.CTkButton(row3, text="Шаблон Контракты", command=lambda: self._save_template("contracts")).pack(side="left", padx=5)

    def _ask_open(self) -> str | None:
        return filedialog.askopenfilename(title="Выберите файл Excel", filetypes=[("Excel", "*.xlsx;*.xls")])

    def _ask_save(self, title: str, default_ext: str, filter_name: str) -> str | None:
        return filedialog.asksaveasfilename(title=title, defaultextension=default_ext, filetypes=[(filter_name, f"*{default_ext}")])

    # Imports
    def _import_workers(self) -> None:
        path = self._ask_open()
        if not path:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                n = import_workers_from_excel(conn, path)
            messagebox.showinfo("Импорт", f"Импортировано работников: {n}")
        except Exception as exc:
            messagebox.showerror("Импорт", str(exc))

    def _import_jobs(self) -> None:
        path = self._ask_open()
        if not path:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                n = import_job_types_from_excel(conn, path)
            messagebox.showinfo("Импорт", f"Импортировано видов работ: {n}")
        except Exception as exc:
            messagebox.showerror("Импорт", str(exc))

    def _import_products(self) -> None:
        path = self._ask_open()
        if not path:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                n = import_products_from_excel(conn, path)
            messagebox.showinfo("Импорт", f"Импортировано изделий: {n}")
        except Exception as exc:
            messagebox.showerror("Импорт", str(exc))

    def _import_contracts(self) -> None:
        path = self._ask_open()
        if not path:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                n = import_contracts_from_excel(conn, path)
            messagebox.showinfo("Импорт", f"Импортировано контрактов: {n}")
        except Exception as exc:
            messagebox.showerror("Импорт", str(exc))

    # Exports
    def _export_table(self, table: str) -> None:
        from datetime import datetime
        from utils.text import sanitize_filename
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_rus = {
            "workers": "работники",
            "job_types": "виды_работ",
            "products": "изделия",
            "contracts": "контракты",
        }.get(table, table)
        initial = sanitize_filename(f"экспорт_{table_rus}_{stamp}") + ".xlsx"
        path = filedialog.asksaveasfilename(title=f"Сохранить {table_rus}", defaultextension=".xlsx", initialfile=initial, filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                export_table_to_excel(conn, table, path)
            messagebox.showinfo("Экспорт", "Готово")
        except Exception as exc:
            messagebox.showerror("Экспорт", str(exc))

    def _export_all(self) -> None:
        directory = filedialog.askdirectory(title="Выберите папку для экспорта")
        if not directory:
            return
        try:
            with get_connection(CONFIG.db_path) as conn:
                export_all_tables_to_excel(conn, directory)
            messagebox.showinfo("Экспорт", "Готово")
        except Exception as exc:
            messagebox.showerror("Экспорт", str(exc))

    # Templates
    def _save_template(self, kind: str) -> None:
        from datetime import datetime
        from utils.text import sanitize_filename
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        map_rus = {
            "workers": "работники",
            "job_types": "виды_работ",
            "products": "изделия",
            "contracts": "контракты",
        }
        initial = sanitize_filename(f"шаблон_{map_rus.get(kind, kind)}_{stamp}") + ".xlsx"
        path = filedialog.asksaveasfilename(title=f"Шаблон {map_rus.get(kind, kind)}", defaultextension=".xlsx", initialfile=initial, filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            if kind == "workers":
                generate_workers_template(path)
            elif kind == "job_types":
                generate_job_types_template(path)
            elif kind == "products":
                generate_products_template(path)
            elif kind == "contracts":
                generate_contracts_template(path)
            messagebox.showinfo("Шаблон", "Шаблон сохранен")
        except Exception as exc:
            messagebox.showerror("Шаблон", str(exc))