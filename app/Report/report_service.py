"""
Сервис для генерации отчетов.
Обрабатывает данные из базы данных и формирует отчеты в различных форматах.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from app.db_manager import DatabaseManager
from app.base import BaseService

logger = logging.getLogger(__name__)

class ReportService(BaseService):
    """
    Сервис для генерации отчетов по работе сотрудников.
    """

    def __init__(self, db_manager, worker_service, contract_service):
        super().__init__(db_manager)
        self.worker_service = worker_service
        self.contract_service = contract_service

    def get_report_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получение данных для отчета из базы данных.

        Args:
            params: Параметры отчета (даты, фильтры и т.д.)

        Returns:
            Список словарей с данными для отчета
        """
        try:
            # Получаем данные для отчета
            report_data = self.db.get_report_data(
                worker_id=params.get('worker_id', 0),
                start_date=params.get('start_date'),
                end_date=params.get('end_date'),
                work_type_id=params.get('work_type_id', 0),
                product_id=params.get('product_id', 0),
                contract_id=params.get('contract_id', 0)
            )

            return report_data if report_data else []

        except Exception as e:
            logger.error(f"Ошибка при получении данных для отчета: {e}")
            return []

    def generate_report(self, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Генерация отчета на основе указанных параметров.

        Args:
            params: Параметры отчета (даты, фильтры и т.д.)

        Returns:
            Кортеж (DataFrame с данными отчета, словарь со сводными данными)
        """
        try:
            report_data = self.get_report_data(params)

            if not report_data:
                return pd.DataFrame(), {}

            df = pd.DataFrame(report_data)

            summary_data = {
                'total_amount': df['amount'].sum()
            }

            if params.get('include_works_count', False):
                summary_data['works_count'] = df['work_item_id'].nunique()

            if params.get('include_products_count', False):
                summary_data['products_count'] = df['product_id'].nunique()

            if params.get('include_contracts_count', False):
                summary_data['contracts_count'] = df['contract_id'].nunique()

            return df, summary_data

        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            return pd.DataFrame(), {}

