from __future__ import annotations

from pathlib import Path
import pandas as pd

STYLE = """
<style>
  body { font-family: Arial, sans-serif; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ddd; padding: 8px; }
  th { background-color: #f2f2f2; text-align: left; }
  tr:nth-child(even){background-color: #f9f9f9;}
</style>
"""


def dataframe_to_html(df: pd.DataFrame, title: str = "Отчет") -> str:
    html_table = df.to_html(index=False, border=0)
    return f"<html><head><meta charset='utf-8'>{STYLE}<title>{title}</title></head><body><h2>{title}</h2>{html_table}</body></html>"


def save_html(df: pd.DataFrame, file_path: str | Path, title: str = "Отчет") -> Path:
    html = dataframe_to_html(df, title)
    file_path = Path(file_path)
    file_path.write_text(html, encoding="utf-8")
    return file_path