from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.reports.base import ReportContext, ReportStrategy


class ExcelReportStrategy(ReportStrategy):
    def generate(self, df: pd.DataFrame, output_path: Path, context: ReportContext) -> Path:
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")
        return output_path