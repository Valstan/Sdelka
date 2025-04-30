import logging

import pandas as pd
from typing import Dict, Any

from app.core.services.report_service import ReportService

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, report_service: ReportService):
        self.report_service = report_service

    def generate(self, params: Dict[str, Any]) -> pd.DataFrame:
        try:
            report_data = self.report_service.get_report_data(params)
            if not report_data:
                return pd.DataFrame()

            df = pd.DataFrame(report_data)
            return df

        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            return pd.DataFrame()
