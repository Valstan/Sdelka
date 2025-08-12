from __future__ import annotations

from pathlib import Path
from typing import Sequence
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _find_font_file() -> tuple[str | None, str | None]:
    # Возвращает (Regular, Bold) пути TTF, если найдены
    candidates = [
        ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
        ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
        ("Arial.ttf", "Arial Bold.ttf"),
        ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"),
        ("FreeSans.ttf", "FreeSansBold.ttf"),
    ]
    search_dirs = [
        Path.cwd() / "assets" / "fonts",
        Path.home() / ".fonts",
        Path("/usr/share/fonts/truetype"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path("C:/Windows/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path.home() / "Library" / "Fonts",
    ]
    for regular_name, bold_name in candidates:
        for d in search_dirs:
            reg = d / regular_name
            bold = d / bold_name
            if reg.exists() and reg.is_file() and bold.exists() and bold.is_file():
                return str(reg), str(bold)
        # Если bold не найден, но есть regular — используем regular для обоих
        for d in search_dirs:
            reg = d / regular_name
            if reg.exists() and reg.is_file():
                return str(reg), str(reg)
    return None, None


def _ensure_font_registered() -> tuple[str, str]:
    # Возвращает имена зарегистрированных шрифтов (regular_name, bold_name)
    reg_path, bold_path = _find_font_file()
    # Имена для использования в ReportLab
    reg_name = "AppFont"
    bold_name = "AppFont-Bold"
    if reg_path:
        if reg_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(reg_name, reg_path))
        if bold_path and bold_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
        else:
            # Нет жирного — маппим bold на regular
            bold_name = reg_name
        return reg_name, bold_name
    # Фоллбэк на встроенный (может ломать кириллицу, но лучше, чем падение)
    return "Helvetica", "Helvetica-Bold"


def save_pdf(df: pd.DataFrame, file_path: str | Path, title: str = "Отчет") -> Path:
    file_path = Path(file_path)
    regular_font, bold_font = _ensure_font_registered()

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story: list = []
    styles = getSampleStyleSheet()

    # Переопределяем стили с нужным шрифтом
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName=bold_font,
    )
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=9,
        leading=11,
    )

    story.append(Paragraph(f"<b>{title}</b>", title_style))
    story.append(Spacer(1, 6 * mm))

    data: list[list] = [list(df.columns)] + df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), regular_font),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )

    story.append(table)

    doc.build(story)
    return file_path