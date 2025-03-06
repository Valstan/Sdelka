"""
Сервис для генерации отчетов.
Обрабатывает данные из базы данных и формирует отчеты в различных форматах.
"""
import os
from datetime import datetime, date
import logging
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from app.db.db_manager import DatabaseManager
from app.config import REPORTS_DIR

logger = logging.getLogger(__name__)

class ReportService:
    """
    Сервис для генерации отчетов по работе сотрудников.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация сервиса отчетов.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    def generate_report(self,
                       worker_id: int = 0,
                       start_date: str = None,
                       end_date: str = None,
                       work_type_id: int = 0,
                       product_id: int = 0,
                       contract_id: int = 0,
                       include_works_count: bool = False,
                       include_products_count: bool = False,
                       include_contracts_count: bool = False) -> pd.DataFrame:
        """
        Генерация отчета на основе указанных фильтров.

        Args:
            worker_id: ID работника (0 - все работники)
            start_date: Начальная дата отчета
            end_date: Конечная дата отчета
            work_type_id: ID вида работы (0 - все виды работ)
            product_id: ID изделия (0 - все изделия)
            contract_id: ID контракта (0 - все контракты)
            include_works_count: Включать количество работ
            include_products_count: Включать количество изделий
            include_contracts_count: Включать количество контрактов

        Returns:
            pd.DataFrame: Данные отчета в виде DataFrame
        """
        # Получаем данные из БД
        report_data = self.db.get_report_data(
            worker_id=worker_id,
            start_date=start_date,
            end_date=end_date,
            work_type_id=work_type_id,
            product_id=product_id,
            contract_id=contract_id
        )

        if not report_data:
            return pd.DataFrame()

        # Преобразуем данные в DataFrame для удобной обработки
        df = pd.DataFrame(report_data)

        # Переименовываем столбцы для лучшей читаемости
        df = df.rename(columns={
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'card_number': 'Номер карточки',
            'card_date': 'Дата',
            'quantity': 'Количество',
            'amount': 'Сумма',
            'work_name': 'Вид работы',
            'product_number': 'Номер изделия',
            'product_type': 'Тип изделия',
            'contract_number': 'Номер контракта'
        })

        # Создаем полное имя работника
        df['Работник'] = df['Фамилия'] + ' ' + df['Имя'].str[0] + '.'
        df['Работник'] = df.apply(
            lambda row: row['Работник'] + ' ' + row['Отчество'][0] + '.'
            if not pd.isna(row['Отчество']) else row['Работник'],
            axis=1
        )

        # Создаем полное наименование изделия
        df['Изделие'] = df.apply(
            lambda row: f"{row['Номер изделия']} {row['Тип изделия']}"
            if not pd.isna(row['Номер изделия']) else "",
            axis=1
        )

        # Добавляем агрегированные данные если требуется
        summary_data = {}

        if include_works_count:
            work_counts = df.groupby('Вид работы')['Количество'].sum().reset_index()
            work_counts.columns = ['Вид работы', 'Всего выполнено']
            summary_data['works_count'] = work_counts

        if include_products_count:
            product_counts = df.groupby('Изделие').size().reset_index(name='Количество')
            summary_data['products_count'] = product_counts

        if include_contracts_count:
            contract_counts = df.groupby('Номер контракта').size().reset_index(name='Количество')
            summary_data['contracts_count'] = contract_counts

        return df, summary_data

    def export_to_excel(self,
                      df: pd.DataFrame,
                      summary_data: Dict[str, pd.DataFrame] = None,
                      filename: str = None) -> str:
        """
        Экспорт отчета в формат Excel.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с дополнительными данными для отчета
            filename: Имя файла (если None, будет сгенерировано автоматически)

        Returns:
            str: Путь к созданному файлу
        """
        if df.empty:
            return ""

        # Генерируем имя файла, если не указано
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.xlsx"

        # Добавляем расширение, если его нет
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        # Полный путь к файлу
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            # Создаем объект writer для записи в Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Основные данные
                df.to_excel(writer, sheet_name='Отчет', index=False)

                # Дополнительные данные, если есть
                if summary_data:
                    if 'works_count' in summary_data:
                        summary_data['works_count'].to_excel(
                            writer, sheet_name='Виды работ', index=False
                        )

                    if 'products_count' in summary_data:
                        summary_data['products_count'].to_excel(
                            writer, sheet_name='Изделия', index=False
                        )

                    if 'contracts_count' in summary_data:
                        summary_data['contracts_count'].to_excel(
                            writer, sheet_name='Контракты', index=False
                        )

            logger.info(f"Отчет успешно экспортирован в Excel: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Ошибка при экспорте в Excel: {e}")
            return ""

    def export_to_html(self,
                     df: pd.DataFrame,
                     summary_data: Dict[str, pd.DataFrame] = None,
                     filename: str = None) -> str:
        """
        Экспорт отчета в формат HTML.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с дополнительными данными для отчета
            filename: Имя файла (если None, будет сгенерировано автоматически)

        Returns:
            str: Путь к созданному файлу
        """
        if df.empty:
            return ""

        # Генерируем имя файла, если не указано
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.html"

        # Добавляем расширение, если его нет
        if not filename.endswith('.html'):
            filename += '.html'

        # Полный путь к файлу
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            # Формируем HTML-содержимое
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Отчет по работе сотрудников</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2 { color: #444; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>Отчет по работе сотрудников</h1>
                <p>Дата формирования: {date}</p>

                <h2>Основные данные</h2>
                {main_table}
            """.format(
                date=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                main_table=df.to_html(index=False)
            )

            # Добавляем дополнительные таблицы, если есть
            if summary_data:
                if 'works_count' in summary_data:
                    html_content += """
                    <h2>Количество выполненных работ</h2>
                    {table}
                    """.format(table=summary_data['works_count'].to_html(index=False))

                if 'products_count' in summary_data:
                    html_content += """
                    <h2>Количество изделий</h2>
                    {table}
                    """.format(table=summary_data['products_count'].to_html(index=False))

                if 'contracts_count' in summary_data:
                    html_content += """
                    <h2>Количество контрактов</h2>
                    {table}
                    """.format(table=summary_data['contracts_count'].to_html(index=False))

            # Закрываем HTML-документ
            html_content += """
            </body>
            </html>
            """

            # Записываем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Отчет успешно экспортирован в HTML: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Ошибка при экспорте в HTML: {e}")
            return ""

    def export_to_pdf(self,
                    df: pd.DataFrame,
                    summary_data: Dict[str, pd.DataFrame] = None,
                    filename: str = None) -> str:
        """
        Экспорт отчета в формат PDF.

        Args:
            df: DataFrame с данными отчета
            summary_data: Словарь с дополнительными данными для отчета
            filename: Имя файла (если None, будет сгенерировано автоматически)

        Returns:
            str: Путь к созданному файлу
        """
        if df.empty:
            return ""

        try:
            # Сначала создаем HTML-версию
            html_path = self.export_to_html(df, summary_data, filename=None)

            if not html_path:
                return ""

            # Генерируем имя файла для PDF, если не указано
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.pdf"

            # Добавляем расширение, если его нет
            if not filename.endswith('.pdf'):
                filename += '.pdf'

            # Полный путь к файлу
            filepath = os.path.join(REPORTS_DIR, filename)

            # Используем pdfkit для конвертации HTML в PDF
            import pdfkit

            # Если путь к wkhtmltopdf не установлен в системе, нужно указать его
            # config = pdfkit.configuration(wkhtmltopdf='/path/to/wkhtmltopdf')
            # pdfkit.from_file(html_path, filepath, configuration=config)

            # Если wkhtmltopdf установлен в системе
            pdfkit.from_file(html_path, filepath)

            logger.info(f"Отчет успешно экспортирован в PDF: {filepath}")
            return filepath

        except ImportError:
            logger.error("Для экспорта в PDF требуется установить pdfkit и wkhtmltopdf")
            return ""

        except Exception as e:
            logger.error(f"Ошибка при экспорте в PDF: {e}")
            return ""