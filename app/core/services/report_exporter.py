"""
File: app/core/services/report_exporter.py
Экспорт отчетов в различные форматы (Excel, PDF, HTML) с использованием паттерна Strategy.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from app.core.utils.utils import write_file, read_file
from app.config import REPORT_SETTINGS  # Предполагается, что EXPORT_DIR указан в config

logger = logging.getLogger(__name__)


class ExportStrategy(ABC):
    """
    Абстрактный класс для стратегий экспорта.

    Args:
        ABC: базовый класс для абстрактных классов
    """

    @abstractmethod
    def export(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует данные в указанный формат.

        Args:
            df: DataFrame с данными отчета
            summary: Обобщенная статистика
            file_path: Путь для сохранения файла

        Returns:
            True если экспорт успешен, иначе False
        """
        pass


class ExcelExportStrategy(ExportStrategy):
    """
    Стратегия экспорта в Excel.
    """

    def export(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует данные в Excel.

        Args:
            df: DataFrame с данными отчета
            summary: Обобщенная статистика
            file_path: Путь для сохранения файла

        Returns:
            True если экспорт успешен, иначе False
        """
        try:
            export_path = Path(file_path).with_suffix('.xlsx')
            with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
                # Основные данные
                df.to_excel(writer, sheet_name='Детализация', index=False)

                # Сводка
                summary_df = pd.DataFrame.from_dict(summary, orient='index', columns=['Значение'])
                summary_df.index.name = 'Метрика'
                summary_df.to_excel(writer, sheet_name='Сводка')

                # Форматирование
                workbook = writer.book
                worksheet = writer.sheets['Детализация']
                worksheet.set_column('A:Z', 15)

                logger.info(f"Отчет успешно экспортирован в Excel: {export_path}")
                return True

        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}", exc_info=True)
            return False


class PdfExportStrategy(ExportStrategy):
    """
    Стратегия экспорта в PDF.
    """

    def export(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует данные в PDF.

        Args:
            df: DataFrame с данными отчета
            summary: Обобщенная статистика
            file_path: Путь для сохранения файла

        Returns:
            True если экспорт успешен, иначе False
        """
        try:
            export_path = Path(file_path).with_suffix('.pdf')
            doc = SimpleDocTemplate(str(export_path), pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Заголовок
            title_style = styles['Title']
            elements.append(Paragraph("Отчет о выполненных работах", title_style))
            elements.append(Spacer(1, 24))

            # Сводная информация
            summary_style = styles['Normal']
            elements.append(Paragraph("Сводная информация:", summary_style))
            elements.append(Spacer(1, 12))

            summary_data = [["Метрика", "Значение"]]
            for key, value in summary.items():
                summary_data.append([key, str(value)])

            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 24))

            # Детализация
            elements.append(Paragraph("Детализация:", summary_style))
            elements.append(Spacer(1, 12))

            df_data = [df.columns.tolist()] + df.values.tolist()
            data_table = Table(df_data)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(data_table)

            # Создаем документ
            doc.build(elements)
            logger.info(f"Отчет успешно экспортирован в PDF: {export_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта в PDF: {e}", exc_info=True)
            return False


class HtmlExportStrategy(ExportStrategy):
    """
    Стратегия экспорта в HTML.
    """

    def export(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует данные в HTML.

        Args:
            df: DataFrame с данными отчета
            summary: Обобщенная статистика
            file_path: Путь для сохранения файла

        Returns:
            True если экспорт успешен, иначе False
        """
        try:
            export_path = Path(file_path).with_suffix('.html')
            template_path = Path("templates/report_template.html")

            # Чтение шаблона
            if template_path.exists():
                template = read_file(template_path)
            else:
                template = self._generate_default_template()

            # Подготовка данных
            df_html = df.to_html(index=False, classes='report-table')
            summary_html = self._dict_to_html(summary)

            # Замена плейсхолдеров
            report_content = template.replace("{{summary}}", summary_html).replace("{{data}}", df_html)

            # Сохранение файла
            if not write_file(export_path, report_content):
                raise IOError(f"Не удалось сохранить файл {export_path}")

            logger.info(f"Отчет успешно экспортирован в HTML: {export_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта в HTML: {e}", exc_info=True)
            return False

    def _generate_default_template(self) -> str:
        """Генерирует базовый HTML-шаблон."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Отчет</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #1976D2; }
                .summary { margin-bottom: 20px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { padding: 8px; text-align: center; border: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Отчет о выполненных работах</h1>
            <div class="summary">{{summary}}</div>
            <div class="data">{{data}}</div>
        </body>
        </html>
        """

    def _dict_to_html(self, data: Dict[str, Any]) -> str:
        """Преобразует словарь в HTML."""
        html = "<table>\n  <tr><th>Метрика</th><th>Значение</th></tr>\n"

        for key, value in data.items():
            html += f"  <tr><td>{key}</td><td>{value}</td></tr>\n"

        html += "</table>"
        return html


class ReportExporter:
    """
    Контекстный класс для экспорта отчетов в различные форматы.
    Реализует паттерн Strategy для динамического выбора стратегии экспорта.
    """

    def __init__(self):
        """Инициализирует ReportExporter с доступными стратегиями."""
        self.strategies = {
            "excel": ExcelExportStrategy(),
            "pdf": PdfExportStrategy(),
            "html": HtmlExportStrategy()
        }
        self.export_dir = Path(REPORT_SETTINGS)
        self.export_dir.mkdir(exist_ok=True)

    def export(self, df: pd.DataFrame, summary: Dict[str, Any], export_format: str) -> Optional[str]:
        """
        Экспортирует отчет в указанный формат.

        Args:
            df: DataFrame с данными отчета
            summary: Словарь с обобщенной статистикой
            export_format: Формат экспорта ('excel', 'pdf', 'html')

        Returns:
            Путь к экспортированному файлу или None в случае ошибки
        """
        if export_format.lower() not in self.strategies:
            raise ValueError(f"Неподдерживаемый формат экспорта: {export_format}")

        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"report_{timestamp}.{export_format.lower()}"
        file_path = self.export_dir / file_name

        strategy = self.strategies[export_format.lower()]
        success = strategy.export(df, summary, str(file_path))

        if success:
            return str(file_path)

        return None