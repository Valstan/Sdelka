from __future__ import annotations

from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.reports.base import ReportContext, ReportStrategy
from app.utils.paths import get_paths


class HtmlReportStrategy(ReportStrategy):
    def generate(self, df: pd.DataFrame, output_path: Path, context: ReportContext) -> Path:
        paths = get_paths()
        env = Environment(
            loader=FileSystemLoader(str(paths.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
        )
        template = env.get_template("base.html")
        html = template.render(title=context.title, filters=context.filters, table=df.to_html(index=False))
        output_path.write_text(html, encoding="utf-8")
        return output_path