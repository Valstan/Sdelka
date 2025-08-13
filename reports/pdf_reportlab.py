from __future__ import annotations

from pathlib import Path
from typing import Sequence, List
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _find_font_file() -> tuple[str | None, str | None]:
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
        for d in search_dirs:
            reg = d / regular_name
            if reg.exists() and reg.is_file():
                return str(reg), str(reg)
    return None, None


def _ensure_font_registered() -> tuple[str, str]:
    reg_path, bold_path = _find_font_file()
    reg_name = "AppFont"
    bold_name = "AppFont-Bold"
    if reg_path:
        if reg_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(reg_name, reg_path))
        if bold_path and bold_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
        else:
            bold_name = reg_name
        return reg_name, bold_name
    return "Helvetica", "Helvetica-Bold"


def _measure_col_widths(df: pd.DataFrame, font_name: str, font_size: int, padding: float = 8.0, sample_rows: int = 200) -> List[float]:
    cols = list(df.columns)
    values = df.head(sample_rows).astype(str).values.tolist()
    widths: List[float] = []
    for j, col in enumerate(cols):
        max_w = pdfmetrics.stringWidth(str(col), font_name, font_size)
        for row in values:
            text = str(row[j])
            w = pdfmetrics.stringWidth(text, font_name, font_size)
            if w > max_w:
                max_w = w
        widths.append(max_w + padding)
    return widths


def save_pdf(df: pd.DataFrame, file_path: str | Path, title: str = "Отчет", orientation: str | None = None) -> Path:
    """Сохраняет DataFrame в PDF с авто-подбором шрифта и ориентации.

    orientation: "portrait" | "landscape" | None (авто)
    """
    file_path = Path(file_path)
    regular_font, bold_font = _ensure_font_registered()

    # Границы шрифта
    font_min = 12
    font_base = 14
    font_max = 18

    # Кандидаты ориентации
    if orientation == "portrait":
        page_candidates = [A4]
    elif orientation == "landscape":
        page_candidates = [landscape(A4)]
    else:
        page_candidates = [A4, landscape(A4)]

    best_page = None
    best_font = None
    best_widths: List[float] | None = None

    for page_size in page_candidates:
        page_width, _ = page_size
        left = right = 15 * mm
        avail_width = page_width - left - right
        test_order = [font_base] + list(range(font_base + 1, font_max + 1)) + list(range(font_base - 1, font_min - 1, -1))
        for fs in test_order:
            widths = _measure_col_widths(df, regular_font, fs)
            total = sum(widths)
            # Даже если total > avail_width, сможем ужать пропорционально — но приоритет отдаём вариантам, где умещается без масштабирования
            fits = total <= avail_width
            best_page = page_size
            best_font = fs
            best_widths = widths
            if fits:
                break
        if best_font is not None:
            break

    # Подготовка документа
    if best_page is None:
        best_page = A4
    if best_font is None:
        best_font = font_base
    page_width, _ = best_page
    left = right = top = bottom = 15 * mm
    avail_width = page_width - left - right

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=best_page,
        rightMargin=right,
        leftMargin=left,
        topMargin=top,
        bottomMargin=bottom,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=min(max(font_base + 2, best_font + 2), font_max + 2),
    )
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=best_font,
        leading=int(best_font * 1.2),
    )
    header_style = ParagraphStyle(
        name="ReportHeader",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=best_font,
        leading=int(best_font * 1.2),
    )

    story: list = []
    story.append(Paragraph(f"<b>{title}</b>", title_style))
    story.append(Spacer(1, 6 * mm))

    # Данные как Paragraph для переноса строк
    cols = list(df.columns)
    data_rows: List[List] = []
    data_rows.append([Paragraph(str(c), header_style) for c in cols])
    for _, row in df.iterrows():
        data_rows.append([Paragraph(str(row[c]), body_style) for c in cols])

    # Ширины столбцов (масштабирование при необходимости)
    widths = best_widths or _measure_col_widths(df, regular_font, best_font)
    total = sum(widths)
    if total > avail_width and total > 0:
        scale = avail_width / total
        widths = [w * scale for w in widths]

    table = Table(data_rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), regular_font),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTSIZE", (0, 0), (-1, -1), best_font),
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