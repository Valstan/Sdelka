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

    def generate_report(self, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Генерирует отчет на основе указанных параметров.

        Args:
            params: Параметры отчета (даты, фильтры и т.д.)

        Returns:
            DataFrame с данными отчета и словарь с сводными данными
        """
        try:
            # Получаем данные для отчета
            report_data = self.work_repository.get_report_data(
                start_date=params.get('startdate'),
                end_date=params.get('enddate'),
                worker_id=params.get('workerid', 0),
                worktype_id=params.get('worktypeid', 0),
                product_id=params.get('productid', 0),
                contract_id=params.get('contractid', 0)
            )

            if not report_data:
                return pd.DataFrame(), {}

            # Конвертируем данные в DataFrame
            df = pd.DataFrame(report_data)

            # Важно: разделяем суммы по работникам, если требуется
            if 'Сумма' in df.columns and 'Работник' in df.columns and 'ID работы' in df.columns:
                # Группируем данные по ID работы
                work_groups = df.groupby('ID работы')

                # Для каждой работы считаем количество уникальных работников
                for work_id, group in work_groups:
                    if len(group['Работник'].unique()) > 1:
                        # Если у работы несколько работников, делим сумму поровну
                        worker_count = len(group['Работник'].unique())
                        # Сумма за одну работу (берем из первой строки группы)
                        total_amount = group['Сумма'].iloc[0]
                        # Разделенная сумма
                        divided_amount = total_amount / worker_count

                        # Обновляем суммы для всех строк с этим ID работы
                        df.loc[df['ID работы'] == work_id, 'Сумма'] = divided_amount

            # Рассчитываем итоговые суммы
            total_amount = df['Сумма'].sum() if 'Сумма' in df.columns else 0

            # Собираем дополнительную статистику, если запрошена
            summary_data = {
                'total_amount': total_amount,
            }

            if params.get('includeworkscount', False):
                # Подсчет уникальных работ
                summary_data['works_count'] = df['ID работы'].nunique() if 'ID работы' in df.columns else 0

            if params.get('includeproductscount', False):
                # Подсчет уникальных изделий
                summary_data['products_count'] = df['ID изделия'].nunique() if 'ID изделия' in df.columns else 0

            if params.get('includecontractscount', False):
                # Подсчет уникальных контрактов
                summary_data['contracts_count'] = df['ID контракта'].nunique() if 'ID контракта' in df.columns else 0

            # Удаляем служебные колонки с ID перед возвратом
            if 'ID работы' in df.columns:
                df = df.drop(columns=['ID работы'])
            if 'ID изделия' in df.columns:
                df = df.drop(columns=['ID изделия'])
            if 'ID контракта' in df.columns:
                df = df.drop(columns=['ID контракта'])

            return df, summary_data

        except Exception as e:
            logging.error(f"Ошибка при генерации отчета: {str(e)}")
            logging.exception(e)
            return pd.DataFrame(), {}

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