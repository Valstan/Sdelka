from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.db.migrations import destroy_database_for_tests, initialize_database
from app.io.excel_exporter import ExcelExporter
from app.io.excel_importer import ExcelImporter
from app.reports.base import ReportContext
from app.reports.report_factory import ReportFactory
from app.services.workers_service import WorkersService


def setup_function(_):
    destroy_database_for_tests()


def test_reports_generation(tmp_path):
    initialize_database()
    df = pd.DataFrame([{"a": 1, "b": 2}])
    factory = ReportFactory()
    out_html = tmp_path / "r.html"
    out_pdf = tmp_path / "r.pdf"
    out_xlsx = tmp_path / "r.xlsx"
    ctx = ReportContext(title="T", filters={"x": "y"})
    factory.generate("html", df, out_html, ctx)
    factory.generate("pdf", df, out_pdf, ctx)
    factory.generate("excel", df, out_xlsx, ctx)
    assert out_html.exists() and out_pdf.exists() and out_xlsx.exists()


def test_excel_export_import(tmp_path):
    initialize_database()
    exporter = ExcelExporter()
    out = exporter.export_file(tmp_path / "dump.xlsx")
    assert out.exists()

    importer = ExcelImporter()
    # create workbook with workers sheet
    df_workers = pd.DataFrame([
        {"last_name": "Петров", "first_name": "Петр", "middle_name": None, "position": None, "phone": None, "hire_date": None}
    ])
    with pd.ExcelWriter(tmp_path / "in.xlsx") as writer:
        df_workers.to_excel(writer, index=False, sheet_name="workers")
    importer.import_file(str(tmp_path / "in.xlsx"))
    workers = WorkersService().list_workers()
    assert any(w["last_name"] == "Петров" for w in workers)