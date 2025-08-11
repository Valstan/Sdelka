from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
import pandas as pd

from app.db.connection import Database
from app.reports.base import ReportContext
from app.reports.report_factory import ReportFactory
from app.utils.paths import get_paths


class ReportsView(ctk.CTkFrame):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.factory = ReportFactory()
        self.grid_columnconfigure(0, weight=1)

        self.type_var = ctk.StringVar(value="html")
        type_opt = ctk.CTkOptionMenu(self, values=["html", "pdf", "excel"], variable=self.type_var)
        gen_btn = ctk.CTkButton(self, text="Сформировать отчет по нарядам", command=self._on_generate)
        self.status = ctk.CTkLabel(self, text="")

        type_opt.grid(row=0, column=0, padx=12, pady=12, sticky="w")
        gen_btn.grid(row=0, column=1, padx=12, pady=12, sticky="w")
        self.status.grid(row=1, column=0, columnspan=2, padx=12, sticky="w")

    def _on_generate(self) -> None:
        db = Database.instance()
        df = pd.read_sql_query("SELECT * FROM work_orders", db.connection)
        paths = get_paths()
        report_type = self.type_var.get()
        out = paths.reports_dir / f"work_orders_report.{ 'html' if report_type=='html' else ('pdf' if report_type=='pdf' else 'xlsx') }"
        ctx = ReportContext(title="Отчет по нарядам", filters={})
        self.factory.generate(report_type, df, out, ctx)
        self.status.configure(text=f"Сохранено: {out}")