from __future__ import annotations

from pathlib import Path
from typing import Sequence, List, Tuple
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_ABBR = {
    "Количество": "Кол-во",
    "Номер": "№",
    "Номер изделия": "№ изд.",
    "Номер_изделия": "№ изд.",
    "Вид_работ": "Вид работ",
}


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


def _ensure_font_registered(prefer_family: str | None = None) -> tuple[str, str]:
    # Если просят конкретное семейство, поддерживаем только шрифты с кириллицей из кандидатов
    if prefer_family and prefer_family in ("DejaVu Sans", "Noto Sans", "Arial", "Liberation Sans"):
        # Попытаемся найти ttf по имени семейства среди кандидатов
        family_map = {
            "DejaVu Sans": ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
            "Noto Sans": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
            "Arial": ("Arial.ttf", "Arial Bold.ttf"),
            "Liberation Sans": ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"),
        }
        reg_name, bold_name = "AppFont", "AppFont-Bold"
        reg_path, bold_path = None, None
        reg_file, bold_file = family_map[prefer_family]
        for d in [
            Path.cwd() / "assets" / "fonts",
            Path.home() / ".fonts",
            Path("/usr/share/fonts/truetype"),
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path("C:/Windows/Fonts"),
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
        ]:
            if reg_path is None and (d / reg_file).exists():
                reg_path = str(d / reg_file)
            if bold_path is None and (d / bold_file).exists():
                bold_path = str(d / bold_file)
        if reg_path:
            if reg_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(reg_name, reg_path))
            if bold_path and bold_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            else:
                bold_name = reg_name
            return reg_name, bold_name
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


def _is_long_text_column(name: str) -> bool:
    n = name.casefold()
    return any(k in n for k in ("вид", "работ", "фио", "работник", "издел", "name"))


def _min_word_widths_for_wrap_cols(df: pd.DataFrame, cols: list[str], font_name: str, font_size: int, padding: float = 8.0) -> List[float]:
    """Минимальная ширина для колонок, где разрешен перенос: ширина самого длинного слова + padding.
    Для не-переносимых колонок возвращает 0 (нет минимума кроме общей ширины).
    """
    mins: List[float] = []
    for c in cols:
        if _is_long_text_column(str(c)):
            max_token = 0.0
            for text in df[c].astype(str).head(1000):
                for token in text.split():
                    w = pdfmetrics.stringWidth(token, font_name, font_size)
                    if w > max_token:
                        max_token = w
            mins.append(max_token + padding)
        else:
            mins.append(0.0)
    return mins


def save_pdf(
    df: pd.DataFrame,
    file_path: str | Path,
    title: str = "Отчет",
    orientation: str | None = None,
    font_size: int | None = None,
    font_family: str | None = None,
    margins_mm: Tuple[float, float, float, float] | None = None,
) -> Path:
    """Сохраняет DataFrame в PDF с управлением ориентацией/шрифтом/полями.

    orientation: "portrait" | "landscape" | None (авто)
    font_size: 10..18 или None для авто
    font_family: имя зарегистрированного шрифта (например, "Helvetica") или None для авто
    margins_mm: (left, right, top, bottom) мм
    """
    file_path = Path(file_path)
    regular_font, bold_font = _ensure_font_registered(font_family)

    font_min = 10
    font_base = 14
    font_max = 18

    # Страницы-кандидаты
    if orientation == "portrait":
        page_candidates = [A4]
    elif orientation == "landscape":
        page_candidates = [landscape(A4)]
    else:
        page_candidates = [A4, landscape(A4)]

    # Поля
    if margins_mm is None:
        margins_mm = (15.0, 15.0, 15.0, 15.0)
    left_mm, right_mm, top_mm, bottom_mm = margins_mm

    best_page = None
    best_font = None
    best_widths: List[float] | None = None
    # Кандидат с минимальным переполнением (если ни один не помещается идеально)
    fallback_overflow = None
    fallback_candidate: Tuple | None = None

    cols = list(df.columns)

    # Подбор шрифта/страницы
    for page_size in page_candidates:
        page_w, _ = page_size
        avail_w = page_w - (left_mm + right_mm) * mm
        if font_size is not None:
            fs_iter = [max(font_min, min(font_size, font_max))]
        else:
            fs_iter = [font_base] + list(range(font_base + 1, font_max + 1)) + list(range(font_base - 1, font_min - 1, -1))
        for fs in fs_iter:
            widths = _measure_col_widths(df, regular_font, fs)
            total = sum(widths)
            if total <= avail_w:
                best_page, best_font, best_widths = page_size, fs, widths
                break
            # Попробуем ужать только длинные текстовые колонки (для переносов по словам), соблюдая минимальную ширину слова
            mins = _min_word_widths_for_wrap_cols(df, cols, regular_font, fs)
            nonwrap_total = sum(w for w, c in zip(widths, cols) if not _is_long_text_column(str(c)))
            wrap_total = sum(w for w, c in zip(widths, cols) if _is_long_text_column(str(c)))
            wrap_min_total = sum(m for m, c in zip(mins, cols) if _is_long_text_column(str(c)))
            # доступно под переносимые колонки
            avail_for_wrap = max(0.0, avail_w - nonwrap_total)
            if wrap_total > 0 and avail_for_wrap >= wrap_min_total:
                scale = min(1.0, avail_for_wrap / wrap_total)
                adj_widths = []
                for w, m, c in zip(widths, mins, cols):
                    if _is_long_text_column(str(c)):
                        adj = max(m, w * scale)
                    else:
                        adj = w
                    adj_widths.append(adj)
                if sum(adj_widths) <= avail_w:
                    best_page, best_font, best_widths = page_size, fs, adj_widths
                    break
                else:
                    overflow = sum(adj_widths) - avail_w
                    if fallback_overflow is None or overflow < fallback_overflow:
                        fallback_overflow = overflow
                        fallback_candidate = (page_size, fs, adj_widths)
            else:
                # не можем ужать переносимые или их нет — сохраняем как кандидат с переполнением
                overflow = total - avail_w
                if fallback_overflow is None or overflow < fallback_overflow:
                    fallback_overflow = overflow
                    fallback_candidate = (page_size, fs, widths)
        if best_font is not None:
            break

    if best_page is None:
        # Учитываем желаемую ориентацию при фолбэке
        if fallback_candidate is not None:
            best_page, best_font, best_widths = fallback_candidate
        else:
            if orientation == "landscape":
                best_page = landscape(A4)
            else:
                best_page = A4
    if best_font is None:
        best_font = font_base if font_size is None else max(font_min, min(font_size, font_max))
    if best_widths is None:
        best_widths = _measure_col_widths(df, regular_font, best_font)

    page_w, _ = best_page
    avail_w = page_w - (left_mm + right_mm) * mm
    total = sum(best_widths)
    if total > avail_w:
        # финальный пересчет с учетом минимальной ширины слов
        mins = _min_word_widths_for_wrap_cols(df, cols, regular_font, best_font)
        nonwrap_total = sum(w for w, c in zip(best_widths, cols) if not _is_long_text_column(str(c)))
        wrap_total = sum(w for w, c in zip(best_widths, cols) if _is_long_text_column(str(c)))
        wrap_min_total = sum(m for m, c in zip(mins, cols) if _is_long_text_column(str(c)))
        avail_for_wrap = max(0.0, avail_w - nonwrap_total)
        if wrap_total > 0 and avail_for_wrap >= wrap_min_total:
            scale = min(1.0, avail_for_wrap / wrap_total)
            best_widths = [
                max(m, w * scale) if _is_long_text_column(str(c)) else w
                for w, m, c in zip(best_widths, mins, cols)
            ]

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=best_page,
        leftMargin=left_mm * mm,
        rightMargin=right_mm * mm,
        topMargin=top_mm * mm,
        bottomMargin=bottom_mm * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=min(max(font_base + 2, best_font + 2), font_max + 2),
    )
    body_style_wrap = ParagraphStyle(
        name="ReportBodyWrap",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=best_font,
        leading=int(best_font * 1.2),
        splitLongWords=False,
    )
    body_style_nowrap = ParagraphStyle(
        name="ReportBodyNoWrap",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=best_font,
        leading=int(best_font * 1.2),
        splitLongWords=False,
    )
    header_style = ParagraphStyle(
        name="ReportHeader",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=best_font,
        leading=int(best_font * 1.2),
        splitLongWords=False,
    )

    story: list = []
    story.append(Paragraph(f"<b>{title}</b>", title_style))
    story.append(Spacer(1, 6 * mm))

    # Данные: разрешаем перенос только в длинных текстовых колонках; в остальных заменяем пробелы на неразрывные
    header_row = [Paragraph(str(_ABBR.get(c, c)), header_style) for c in cols]
    data_rows: List[List] = [header_row]
    for _, row in df.iterrows():
        r: List = []
        for c in cols:
            text = str(row[c])
            if _is_long_text_column(str(c)):
                r.append(Paragraph(text, body_style_wrap))
            else:
                safe = text.replace(" ", "\u00A0")
                r.append(Paragraph(safe, body_style_nowrap))
        data_rows.append(r)

    table = Table(data_rows, colWidths=best_widths, repeatRows=1)
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