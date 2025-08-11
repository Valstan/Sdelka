from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from app.reports.base import ReportContext, ReportStrategy
from app.reports.excel_report import ExcelReportStrategy
from app.reports.html_report import HtmlReportStrategy
from app.reports.pdf_report import PdfReportStrategy

ReportType = Literal["html", "pdf", "excel"]


class ReportFactory:
    def __init__(self) -> None:
        self._strategies: dict[ReportType, ReportStrategy] = {
            "html": HtmlReportStrategy(),
            "pdf": PdfReportStrategy(),
            "excel": ExcelReportStrategy(),
        }

    def generate(self, report_type: ReportType, df: pd.DataFrame, output_path: Path, context: ReportContext) -> Path:
        strategy = self._strategies[report_type]
        return strategy.generate(df, output_path, context)