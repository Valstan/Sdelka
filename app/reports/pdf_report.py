from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.reports.base import ReportContext, ReportStrategy


class PdfReportStrategy(ReportStrategy):
    def generate(self, df: pd.DataFrame, output_path: Path, context: ReportContext) -> Path:
        doc = SimpleDocTemplate(str(output_path), pagesize=landscape(A4), title=context.title)
        styles = getSampleStyleSheet()
        elements = [Paragraph(context.title, styles["Title"])]
        if context.filters:
            filters_text = ", ".join(f"{k}: {v}" for k, v in context.filters.items())
            elements.append(Paragraph(filters_text, styles["Normal"]))
        elements.append(Spacer(1, 12))
        data = [list(df.columns)] + df.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)
        return output_path