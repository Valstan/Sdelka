from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
try:
    from bs4 import BeautifulSoup  # type: ignore[import]
except Exception:  # optional dependency
    BeautifulSoup = None  # type: ignore[assignment]
import json
try:
    import pdfplumber  # type: ignore[import]
except Exception:  # optional
    pdfplumber = None  # type: ignore[assignment]
try:
    from docx import Document  # type: ignore[import]
except Exception:  # optional
    Document = None  # type: ignore[assignment]
try:
    from dbfread import DBF  # type: ignore[import]
except Exception:
    DBF = None  # type: ignore[assignment]
try:
    from odf.opendocument import load as odf_load  # type: ignore[import]
    from odf.table import Table, TableRow, TableCell  # type: ignore[import]
except Exception:
    odf_load = None  # type: ignore[assignment]


def read_any_tabular(path: str | Path) -> list[pd.DataFrame]:
    """Read file as list of DataFrames (one per sheet or table).

    Minimal scaffold for initial wiring; robust readers will be added later.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        xls = pd.ExcelFile(p)
        return [xls.parse(name) for name in xls.sheet_names]
    if suffix in {".ods"}:
        return [pd.read_excel(p, engine="odf")]
    if suffix in {".csv"}:
        return [pd.read_csv(p, sep=None, engine="python")]
    if suffix in {".txt"}:
        return [pd.read_csv(p, sep=None, engine="python", header=None)]
    if suffix in {".docx"} and Document is not None:
        try:
            doc = Document(str(p))
            dfs: list[pd.DataFrame] = []
            for t in doc.tables:
                rows = []
                for r in t.rows:
                    rows.append([c.text.strip() for c in r.cells])
                if rows:
                    header = rows[0]
                    data = rows[1:] if len(rows) > 1 else []
                    try:
                        dfs.append(pd.DataFrame(data, columns=header))
                    except Exception:
                        dfs.append(pd.DataFrame(rows))
            return dfs
        except Exception:
            return []
    if suffix in {".odt"} and odf_load is not None:
        try:
            doc = odf_load(str(p))
            # Collect all tables
            tables = [el for el in doc.getElementsByType(Table)]
            dfs: list[pd.DataFrame] = []
            for t in tables:
                rows = []
                for tr in t.getElementsByType(TableRow):
                    cells = tr.getElementsByType(TableCell)
                    row = []
                    for cell in cells:
                        text = "".join([node.data for node in cell.childNodes if hasattr(node, 'data')])
                        row.append(text.strip())
                    if row:
                        rows.append(row)
                if rows:
                    try:
                        dfs.append(pd.DataFrame(rows[1:], columns=rows[0]))
                    except Exception:
                        dfs.append(pd.DataFrame(rows))
            return dfs
        except Exception:
            return []
    if suffix in {".xml"}:
        try:
            return [pd.read_xml(str(p))]
        except Exception:
            return []
    if suffix in {".dbf"} and DBF is not None:
        try:
            records = list(DBF(str(p), load=True, char_decode_errors='ignore'))
            return [pd.DataFrame(records)]
        except Exception:
            return []
    if suffix in {".json"}:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [pd.DataFrame(data)]
            if isinstance(data, dict) and "data" in data:
                return [pd.DataFrame(data["data"])]
        except Exception:
            return []
    if suffix in {".html", ".htm"}:
        # Prefer BeautifulSoup if available; otherwise try pandas.read_html on full document
        if BeautifulSoup is not None:
            try:
                soup = BeautifulSoup(Path(p).read_text(encoding="utf-8", errors="ignore"), "html.parser")
                tables = soup.find_all("table")
                dfs: list[pd.DataFrame] = []
                for t in tables:
                    df = pd.read_html(str(t))
                    if df:
                        dfs.extend(df)
                return dfs
            except Exception:
                pass
        try:
            return pd.read_html(str(p))  # type: ignore[return-value]
        except Exception:
            return []
    if suffix in {".pdf"} and pdfplumber is not None:
        try:
            dfs: list[pd.DataFrame] = []
            with pdfplumber.open(str(p)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables() or []
                    for tbl in tables:
                        dfs.append(pd.DataFrame(tbl[1:], columns=tbl[0]))
            return dfs
        except Exception:
            return []
    # Fallback: try pandas
    try:
        return [pd.read_csv(p)]
    except Exception:
        pass
    return []


