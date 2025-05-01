"""
File: app/core/services/report_generator.py
Модуль для расчета статистики отчетов по нарядам.
"""

import pandas as pd
from typing import Any, Dict, List, Tuple
from app.core.services.work_card_service import WorkCardsService
from app.config import DATE_FORMATS
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Класс для расчета статистики и анализа данных отчета.
    """

    def __init__(self, work_card_service: WorkCardsService):
        """
        Инициализация генератора отчетов.

        Args:
            work_card_service: Сервис для работы с нарядами
        """
        self.work_card_service = work_card_service

    def generate_report(self, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Генерирует отчет на основе переданных параметров.

        Args:
            params: Параметры фильтрации отчета

        Returns:
            Кортеж (DataFrame с данными, словарь со статистикой)
        """
        try:
            # Получаем данные из сервиса
            raw_data = self._get_filtered_data(params)

            if not raw_data:
                logger.info("Нет данных для отчета")
                return pd.DataFrame(), {}

            # Преобразуем в DataFrame
            df = pd.DataFrame(raw_data)

            # Добавляем дополнительные поля
            df["date"] = pd.to_datetime(df["card_date"], format=DATE_FORMATS["default"])
            df["date_str"] = df["date"].dt.strftime(DATE_FORMATS["ui"])

            # Выполняем расчеты
            summary = self._calculate_summary(df, params)

            return df, summary

        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}", exc_info=True)
            raise

    def _get_filtered_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получает данные из БД с учетом фильтров.

        Args:
            params: Параметры фильтрации

        Returns:
            Список данных из базы
        """
        try:
            # Формируем SQL-запрос
            query = self._build_query(params)
            logger.debug(f"Формирование SQL-запроса: {query}")

            # Выполняем запрос
            return self.work_card_service.execute_query(query, self._build_query_params(params))

        except Exception as e:
            logger.error(f"Ошибка получения данных: {e}", exc_info=True)
            raise

    def _build_query(self, params: Dict[str, Any]) -> str:
        """
        Строит SQL-запрос для отчета.

        Args:
            params: Параметры фильтрации

        Returns:
            SQL-запрос
        """
        base_query = """
            SELECT 
                wc.id,
                wc.card_number,
                wc.card_date,
                p.product_code,
                c.contract_number,
                w.last_name,
                w.first_name,
                w.middle_name,
                wt.name AS work_type,
                wt.unit,
                wci.quantity,
                wt.price,
                wci.amount,
                wck.amount AS worker_amount
            FROM work_cards wc
            JOIN work_card_items wci ON wc.id = wci.work_card_id
            JOIN work_types wt ON wci.work_type_id = wt.id
            JOIN products p ON wc.product_id = p.id
            JOIN contracts c ON wc.contract_id = c.id
            JOIN work_card_workers wck ON wc.id = wck.work_card_id
            JOIN workers w ON wck.worker_id = w.id
            WHERE 1=1
        """

        conditions = []
        values = []

        # Фильтр по периоду
        if "start_date" in params and "end_date" in params:
            conditions.append("wc.card_date BETWEEN ? AND ?")
            values.extend([params["start_date"].strftime(DATE_FORMATS["default"]),
                           params["end_date"].strftime(DATE_FORMATS["default"])])

        # Фильтр по работнику
        if "worker_id" in params:
            conditions.append("w.id = ?")
            values.append(params["worker_id"])

        # Фильтр по виду работы
        if "work_type_id" in params:
            conditions.append("wt.id = ?")
            values.append(params["work_type_id"])

        # Фильтр по изделию
        if "product_id" in params:
            conditions.append("p.id = ?")
            values.append(params["product_id"])

        # Фильтр по контракту
        if "contract_id" in params:
            conditions.append("c.id = ?")
            values.append(params["contract_id"])

        # Собираем запрос
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        return base_query

    def _build_query_params(self, params: Dict[str, Any]) -> Tuple[Any, ...]:
        """
        Строит параметры для SQL-запроса.

        Args:
            params: Параметры фильтрации

        Returns:
            Кортеж с параметрами запроса
        """
        values = []

        # Период
        if "start_date" in params and "end_date" in params:
            values.append(params["start_date"].strftime(DATE_FORMATS["default"]))
            values.append(params["end_date"].strftime(DATE_FORMATS["default"]))

        # Работник
        if "worker_id" in params:
            values.append(params["worker_id"])

        # Вид работы
        if "work_type_id" in params:
            values.append(params["work_type_id"])

        # Изделие
        if "product_id" in params:
            values.append(params["product_id"])

        # Контракт
        if "contract_id" in params:
            values.append(params["contract_id"])

        return tuple(values)

    def _calculate_summary(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитывает сводную статистику.

        Args:
            df: DataFrame с данными
            params: Параметры отчета

        Returns:
            Словарь со статистикой
        """
        summary = {
            "total_amount": df["amount"].sum() if "amount" in df.columns else 0.0,
            "total_cards": df["id"].nunique() if "id" in df.columns else 0,
            "total_workers": df["worker_id"].nunique() if "worker_id" in df.columns else 0,
            "total_products": df["product_id"].nunique() if "product_id" in df.columns else 0,
            "total_contracts": df["contract_id"].nunique() if "contract_id" in df.columns else 0,
            "works_count": df["work_type_id"].nunique() if "work_type_id" in df.columns else 0,
            "total_quantity": df["quantity"].sum() if "quantity" in df.columns else 0,
            "start_date": params.get("start_date").strftime(DATE_FORMATS["ui"]) if "start_date" in params else "",
            "end_date": params.get("end_date").strftime(DATE_FORMATS["ui"]) if "end_date" in params else ""
        }

        # Условия включения
        if not params.get("include_works_count", False):
            summary.pop("works_count", None)
        if not params.get("include_products_count", False):
            summary.pop("total_products", None)
        if not params.get("include_contracts_count", False):
            summary.pop("total_contracts", None)

        return summary