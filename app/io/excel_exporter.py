from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.db.connection import Database


class ExcelExporter:
    """Export all major tables to an Excel workbook with separate sheets."""

    def export_file(self, path: str | Path) -> Path:
        path = Path(path)
        db = Database.instance()
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            for name in ("workers", "job_types", "products", "contracts", "work_orders"):
                df = pd.read_sql_query(f"SELECT * FROM {name}", db.connection)
                df.to_excel(writer, index=False, sheet_name=name)
        return path