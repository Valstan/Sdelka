import logging
import os
import pandas as pd
from datetime import datetime

from app.config import REPORT_SETTINGS

logger = logging.getLogger(__name__)

class ReportExporter:
    def __init__(self, report_settings):
        self.report_settings = report_settings
        self.output_dir = report_settings['output_dir']

    def export_to_excel(self, df: pd.DataFrame, filename: str):
        try:
            filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Данные', index=False)
                # Дополнительная настройка листа, если необходимо
            return True
        except Exception as e:
            logger.error(f"Ошибка при экспорте в Excel: {e}")
            return False

    def export_to_html(self, df: pd.DataFrame, filename: str):
        try:
            filepath = os.path.join(self.output_dir, f"{filename}.html")
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Отчет по работе сотрудников</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #444; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Отчет по работе сотрудников</h1>
    <p>Дата формирования: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
    <h2>Основные данные</h2>
    {df.to_html(index=False)}
</body>
</html>"""
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(html_content)
            return True
        except Exception as e:
            logger.error(f"Ошибка при экспорте в HTML: {e}")
            return False

    def export_to_pdf(self, df: pd.DataFrame, filename: str):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            filepath = os.path.join(self.output_dir, f"{filename}.pdf")
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
            elements = []

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='TableHeader', fontSize=10, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='TableData', fontSize=9, fontName='Helvetica'))

            elements.append(Paragraph("Отчет по работе сотрудников", styles['Title']))
            elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            data = [['Работник', 'Дата', 'Вид работы', 'Количество', 'Сумма, руб.', 'Изделие', 'Контракт']]
            for _, row in df.iterrows():
                data.append([
                    Paragraph(str(row['worker']), styles['TableData']),
                    Paragraph(str(row['date']), styles['TableData']),
                    Paragraph(str(row['work_type']), styles['TableData']),
                    Paragraph(str(row['quantity']), styles['TableData']),
                    Paragraph(f"{float(row['amount']):.2f}", styles['TableData']),
                    Paragraph(str(row['product']), styles['TableData']),
                    Paragraph(str(row['contract']), styles['TableData'])
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

            doc.build(elements)
            return True
        except Exception as e:
            logger.error(f"Ошибка при экспорте в PDF: {e}")
            return False

    def export(self, df: pd.DataFrame, format_type: str):
        if format_type not in ['excel', 'html', 'pdf']:
            raise ValueError("Неподдерживаемый формат экспорта")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}"

        if format_type == 'excel':
            return self.export_to_excel(df, filename)
        elif format_type == 'html':
            return self.export_to_html(df, filename)
        elif format_type == 'pdf':
            return self.export_to_pdf(df, filename)
