from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable


def write_html_report(path: str | Path, title: str, rows: Iterable[str]) -> str:
    p = Path(path)
    html = [
        "<html><head><meta charset='utf-8'><title>Импорт данных</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ccc;padding:6px} th{background:#f5f5f5}</style>",
        "</head><body>",
        f"<h2>{title}</h2>",
        f"<div>Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
        "<hr>",
    ]
    html.extend(rows)
    html.append("</body></html>")
    p.write_text("\n".join(html), encoding="utf-8")
    return str(p)
