"""
Модуль для экспорта отчетов в различные форматы.
Реализует стратегии экспорта с использованием паттерна Strategy.
"""
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)


class ExportStrategy(ABC):
    """Абстрактный класс стратегии экспорта отчетов."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export(self, df: pd.DataFrame, filename: str) -> Tuple[bool, str]:
        """Экспортирует DataFrame в указанный формат."""
        pass

    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Генерирует уникальное имя файла."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"


class ExcelExportStrategy(ExportStrategy):
    """Стратегия экспорта в Excel."""

    def export(self, df: pd.DataFrame, filename_prefix: str) -> Tuple[bool, str]:
        try:
            filename = self._generate_filename(filename_prefix, "xlsx")
            filepath = self.output_dir / filename

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
                worksheet = writer.sheets['Report']
                worksheet.sheet_view.showGridLines = False

            return True, str(filepath)
        except Exception as e:
            logger.error(f"Excel export error: {e}", exc_info=True)
            return False, str(e)


class HTMLExportStrategy(ExportStrategy):
    """Стратегия экспорта в HTML."""

    def export(self, df: pd.DataFrame, filename_prefix: str) -> Tuple[bool, str]:
        try:
            filename = self._generate_filename(filename_prefix, "html")
            filepath = self.output_dir / filename

            html_content = self._generate_html(df)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return True, str(filepath)
        except Exception as e:
            logger.error(f"HTML export error: {e}", exc_info=True)
            return False, str(e)

    def _generate_html(self, df: pd.DataFrame) -> str:
        """Генерирует полный HTML-документ с таблицей."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Отчет</title>
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Отчет от {datetime.now().strftime('%d.%m.%Y %H:%M')}</h1>
            {df.to_html(index=False)}
        </body>
        </html>
        """


class PDFExportStrategy(ExportStrategy):
    """Стратегия экспорта в PDF."""

    def export(self, df: pd.DataFrame, filename_prefix: str) -> Tuple[bool, str]:
        try:
            filename = self._generate_filename(filename_prefix, "pdf")
            filepath = self.output_dir / filename

            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=landscape(A4),
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            elements = self._create_pdf_elements(df)
            doc.build(elements)

            return True, str(filepath)
        except Exception as e:
            logger.error(f"PDF export error: {e}", exc_info=True)
            return False, str(e)

    def _create_pdf_elements(self, df: pd.DataFrame) -> list:
        """Создает элементы PDF-документа."""
        styles = getSampleStyleSheet()
        elements = []

        # Заголовок
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=14,
            spaceAfter=20
        )
        elements.append(Paragraph("Отчет о выполненных работах", title_style))

        # Таблица данных
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = Table(table_data)

        # Стиль таблицы
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements


class ReportExporter:
    """Контекст экспорта отчетов."""

    def __init__(self, strategy: ExportStrategy):
        self.strategy = strategy

    def export_report(self, df: pd.DataFrame, filename_prefix: str) -> Tuple[bool, str]:
        """Выполняет экспорт отчета с обработкой ошибок."""
        if df.empty:
            logger.warning("Attempted to export empty dataframe")
            return False, "Cannot export empty dataframe"

        try:
            return self.strategy.export(df, filename_prefix)
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return False, str(e)