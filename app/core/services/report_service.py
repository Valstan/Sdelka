"""
File: app/core/services/report_service.py
Сервис для генерации отчетов на основе данных из базы данных.
"""

import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
from app.core.database.connections import DatabaseManager
from app.core.models.base_model import BaseModel
from app.core.services.base_service import BaseService


class ReportService:
    """
    Сервис для генерации отчетов и анализа данных.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.work_card_service = WorkCardService(db_manager)
        self.worker_service = WorkerService(db_manager)
        self.contract_service = ContractService(db_manager)
        self.product_service = ProductService(db_manager)

    def generate_report(self, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Генерирует данные для отчета на основе переданных параметров.

        Args:
            params: Параметры фильтрации отчета

        Returns:
            Кортеж (DataFrame с данными, словарь с обобщенными данными)
        """
        try:
            query = self._build_report_query(params)

            with self.db_manager.connect() as conn:
                df = pd.read_sql_query(query, conn)

            # Добавляем форматированные поля
            if not df.empty:
                df["date"] = pd.to_datetime(df["card_date"]).dt.strftime("%d.%m.%Y")
                df["amount"] = df["quantity"] * df["price"]

            summary = self._generate_summary(df, params)
            return df, summary

        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}", exc_info=True)
            return pd.DataFrame(), {}

    def _build_report_query(self, params: Dict[str, Any]) -> str:
        """
        Строит SQL-запрос для получения данных отчета.

        Args:
            params: Параметры фильтрации

        Returns:
            SQL-запрос
        """
        query = """
            SELECT 
                wc.id as card_id,
                wc.card_number,
                wc.card_date,
                p.product_code,
                c.contract_number,
                w.id as worker_id,
                w.last_name,
                w.first_name,
                wt.name as work_type,
                wt.unit,
                wci.quantity,
                wt.price
            FROM work_cards wc
            JOIN work_card_workers wck ON wc.id = wck.work_card_id
            JOIN workers w ON wck.worker_id = w.id
            JOIN work_card_items wci ON wc.id = wci.work_card_id
            JOIN work_types wt ON wci.work_type_id = wt.id
            JOIN products p ON wc.product_id = p.id
            JOIN contracts c ON wc.contract_id = c.id
            WHERE 1=1
        """

        conditions = []
        values = []

        if params.get("start_date"):
            conditions.append("wc.card_date >= ?")
            values.append(params["start_date"].isoformat())

        if params.get("end_date"):
            conditions.append("wc.card_date <= ?")
            values.append(params["end_date"].isoformat())

        if params.get("worker_id"):
            conditions.append("w.id = ?")
            values.append(params["worker_id"])

        if params.get("work_type_id"):
            conditions.append("wt.id = ?")
            values.append(params["work_type_id"])

        if params.get("product_id"):
            conditions.append("p.id = ?")
            values.append(params["product_id"])

        if params.get("contract_id"):
            conditions.append("c.id = ?")
            values.append(params["contract_id"])

        if conditions:
            query += " AND " + " AND ".join(conditions)

        return query

    def _generate_summary(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует обобщенную статистику по отчету.

        Args:
            df: DataFrame с данными
            params: Параметры отчета

        Returns:
            Словарь с обобщенными данными
        """
        summary = {
            "total_amount": 0,
            "total_cards": len(df["card_id"].unique()),
            "total_workers": len(df["worker_id"].unique()) if "worker_id" in df.columns else 0,
            "total_products": len(df["product_code"].unique()) if "product_code" in df.columns else 0,
            "total_contracts": len(df["contract_number"].unique()) if "contract_number" in df.columns else 0,
            "works_count": len(df["work_type"].unique()) if "work_type" in df.columns else 0,
            "total_quantity": df["quantity"].sum() if "quantity" in df.columns else 0
        }

        if "amount" in df.columns:
            summary["total_amount"] = df["amount"].sum()

        return summary