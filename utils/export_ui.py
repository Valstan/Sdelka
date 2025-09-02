from __future__ import annotations

from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from db.sqlite import get_connection


def _export_table_to_excel(table: str, target_path: str) -> None:
    from import_export.excel_io import export_table_to_excel  # local import to avoid hard dep at import time
    with get_connection() as conn:
        export_table_to_excel(conn, table, target_path)


def create_export_button(parent: ctk.CTkFrame, table: str, button_text: str) -> ctk.CTkButton:
    """Create a standard export button for a given table.

    - parent: container to pack/place the button
    - table: one of 'workers', 'job_types', 'products', 'contracts'
    - button_text: button label in UI
    """

    def _on_export() -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_map = {
            "workers": f"экспорт_работники_{stamp}.xlsx",
            "job_types": f"экспорт_виды_работ_{stamp}.xlsx",
            "products": f"экспорт_изделия_{stamp}.xlsx",
            "contracts": f"экспорт_контракты_{stamp}.xlsx",
        }
        initial = default_map.get(table, f"export_{table}_{stamp}.xlsx")
        path = filedialog.asksaveasfilename(
            title="Сохранить экспорт",
            defaultextension=".xlsx",
            initialfile=initial,
            filetypes=[("Excel", "*.xlsx"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            _export_table_to_excel(table, path)
            messagebox.showinfo("Экспорт", "Готово")
        except Exception as exc:
            messagebox.showerror("Экспорт", str(exc))

    btn = ctk.CTkButton(parent, text=button_text, command=_on_export)
    return btn


