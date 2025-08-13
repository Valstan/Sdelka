from __future__ import annotations

from pathlib import Path
from typing import Sequence, List, Tuple
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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


def _measure_col_widths(df: pd.DataFrame, font_name: str, font_size: int, padding: float = 6.0, sample_rows: int = 200) -> List[float]:
    """Грубая оценка ширины колонок по максимальной строковой ширине (header + до sample_rows)."""
    cols = list(df.columns)
    # Подготовим выборку строк
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


def _chunk_columns_to_fit(widths: List[float], avail_width: float) -> List[Tuple[int, int]]:
    """Разбивает список ширин на группы столбцов, которые помещаются в avail_width.
    Возвращает список кортежей (start_idx, end_idx) включительно.
    """
    chunks: List[Tuple[int, int]] = []
    start = 0
    current_sum = 0.0
    for i, w in enumerate(widths):
        if current_sum + w <= avail_width or i == start:
            current_sum += w
        else:
            chunks.append((start, i - 1))
            start = i
            current_sum = w
    if start < len(widths):
        chunks.append((start, len(widths) - 1))
    return chunks


def save_pdf(df: pd.DataFrame, file_path: str | Path, title: str = "Отчет") -> Path:
    file_path = Path(file_path)
    regular_font, bold_font = _ensure_font_registered()

    # Базовые ограничения шрифта
    font_min = 10
    font_base = 14
    font_max = 18

    # Страницы: сначала портрет A4, потом ландшафт
    page_candidates = [A4, landscape(A4)]

    best_page = None
    best_font = None
    best_widths: List[float] | None = None

    # Подбор страницы и размера шрифта
    for page_size in page_candidates:
        page_width, page_height = page_size
        left = right = top = bottom = 15 * mm
        avail_width = page_width - left - right
        # Сначала пробуем базовый, затем вверх, затем вниз
        test_order = [font_base] + list(range(font_base + 1, font_max + 1)) + list(range(font_base - 1, font_min - 1, -1))
        for fs in test_order:
            widths = _measure_col_widths(df, regular_font, fs)
            total = sum(widths)
            if total <= avail_width:
                best_page = page_size
                best_font = fs
                best_widths = widths
                break
        if best_font is not None:
            break

    # Если ничего не поместилось даже на ландшафте с минимальным шрифтом — разобьём по группам столбцов на минимальном шрифте
    if best_font is None:
        best_page = landscape(A4)
        page_width, page_height = best_page
        left = right = top = bottom = 15 * mm
        avail_width = page_width - left - right
        best_font = font_min
        best_widths = _measure_col_widths(df, regular_font, best_font)

    # Готовим документ
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=best_page,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
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

    # Конвертируем данные в Paragraph, чтобы включить перенос строк
    cols = list(df.columns)
    data_rows: List[List] = []
    data_rows.append([Paragraph(str(c), header_style) for c in cols])
    for _, row in df.iterrows():
        data_rows.append([Paragraph(str(row[c]), body_style) for c in cols])

    page_width, page_height = best_page
    avail_width = page_width - 30 * mm

    # Если все колонки помещаются — одна таблица, иначе — несколько таблиц по группам колонок
    widths = best_widths or _measure_col_widths(df, regular_font, best_font)
    total = sum(widths)
    if total <= avail_width:
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
    else:
        # Делим на группы колонок
        chunks = _chunk_columns_to_fit(widths, avail_width)
        for idx, (start, end) in enumerate(chunks):
            sub_cols = cols[start : end + 1]
            sub_widths = widths[start : end + 1]
            sub_data = [[Paragraph(str(c), header_style) for c in sub_cols]]
            for r in df.itertuples(index=False):
                row_vals = []
                for c in sub_cols:
                    val = getattr(r, c)
                    row_vals.append(Paragraph(str(val), body_style))
                sub_data.append(row_vals)
            sub_table = Table(sub_data, colWidths=sub_widths, repeatRows=1)
            sub_table.setStyle(
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
            # Добавляем подзаголовок для ясности
            if idx > 0:
                story.append(PageBreak())
                story.append(Paragraph(f"<b>{title}</b>", title_style))
                story.append(Spacer(1, 4 * mm))
                story.append(Paragraph(f"Часть столбцов {idx + 1} из {len(chunks)}", styles["Normal"]))
                story.append(Spacer(1, 3 * mm))
            story.append(sub_table)

    doc.build(story)
    return file_path