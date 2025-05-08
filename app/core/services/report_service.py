# app/core/services/report_service.py
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict
from datetime import datetime, date

import pandas as pd

from app.config import DATE_FORMATS
from app.core.models.base_model import WorkCard, WorkType, Worker, Product, Contract
from app.core.database.repositories.work_card_repository import WorkCardRepository
from app.core.database.repositories.work_type_repository import WorkTypeRepository
from app.core.database.repositories.worker_repository import WorkerRepository
from app.core.database.repositories.product_repository import ProductRepository
from app.core.database.repositories.contract_repository import ContractRepository
from app.core.services.base_service import BaseService
from app.core.services.worker_service import WorkerService
from app.core.services.work_type_service import WorkTypeService
from app.core.services.product_service import ProductService
from app.core.services.contract_service import ContractService
from app.utils.validators import validate_date_range
from app.utils.formatters import format_currency

logger = logging.getLogger(__name__)

class ReportService:
    """
    Сервис для генерации отчетов.
    """
    
    def __init__(self, db_manager: Any):
        """
        Инициализирует сервис отчетов.
        
        Args:
            db_manager: Менеджер базы данных
        """
        self.db_manager = db_manager
        
        # Инициализируем репозитории
        self.work_card_repo = WorkCardRepository(db_manager)
        self.work_type_repo = WorkTypeRepository(db_manager)
        self.worker_repo = WorkerRepository(db_manager)
        self.product_repo = ProductRepository(db_manager)
        self.contract_repo = ContractRepository(db_manager)
        
        # Инициализируем сервисы
        self.worker_service = WorkerService(db_manager)
        self.work_type_service = WorkTypeService(db_manager)
        self.product_service = ProductService(db_manager)
        self.contract_service = ContractService(db_manager)
        
    def generate_report(self, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Генерирует отчет на основе переданных параметров.
        
        Args:
            params: Параметры для генерации отчета
            
        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: DataFrame с данными и словарь со статистикой
        """
        try:
            # Валидация параметров
            self._validate_params(params)
            
            # Получаем данные
            df = self._get_report_data(params)
            
            # Формируем статистику
            summary = self._generate_summary(df, params)
            
            return df, summary
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}", exc_info=True)
            return pd.DataFrame(), {}
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Валидирует параметры отчета.
        
        Args:
            params: Параметры для валидации
        """
        # Проверка дат
        if params.get("start_date") and params.get("end_date"):
            start_date = datetime.strptime(params["start_date"], DATE_FORMATS["default"]).date()
            end_date = datetime.strptime(params["end_date"], DATE_FORMATS["default"]).date()
            if start_date > end_date:
                raise ValueError("Дата начала не может быть позже даты окончания")
                
        # Проверка других параметров
        if params.get("workerid") and not self.worker_service.exists(params["workerid"]):
            raise ValueError(f"Работник с ID {params['workerid']} не найден")
            
        if params.get("worktypeid") and not self.work_type_service.exists(params["worktypeid"]):
            raise ValueError(f"Вид работы с ID {params['worktypeid']} не найден")
            
        if params.get("productid") and not self.product_service.exists(params["productid"]):
            raise ValueError(f"Изделие с ID {params['productid']} не найдено")
            
        if params.get("contractid") and not self.contract_service.exists(params["contractid"]):
            raise ValueError(f"Контракт с ID {params['contractid']} не найден")
    
    def _get_report_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Получает данные для отчета на основе переданных параметров.
        
        Args:
            params: Параметры фильтрации
            
        Returns:
            pd.DataFrame: DataFrame с данными
        """
        try:
            # Формируем условия фильтрации
            criteria = self._build_criteria(params)
            
            # Получаем данные
            work_cards = self.work_card_repo.search(criteria)
            
            # Преобразуем в DataFrame
            data = []
            for card in work_cards:
                card_details = self.work_card_repo.get_with_details(card.id)
                if not card_details:
                    continue
                    
                for item in card_details.items:
                    for worker in card_details.workers:
                        data.append({
                            "card_id": card_details.id,
                            "card_number": card_details.card_number,
                            "card_date": card_details.card_date,
                            "worker_id": worker.worker_id,
                            "worker_name": self.worker_service.get_by_id(worker.worker_id).full_name(),
                            "work_type_id": item.work_type_id,
                            "work_type_name": self.work_type_service.get_by_id(item.work_type_id).name,
                            "product_id": card_details.product_id,
                            "product_name": self.product_service.get_by_id(card_details.product_id).name,
                            "contract_id": card_details.contract_id,
                            "contract_number": self.contract_service.get_by_id(card_details.contract_id).contract_number,
                            "quantity": item.quantity,
                            "price": item.amount / item.quantity if item.quantity else 0,
                            "amount": item.amount,
                            "worker_amount": worker.amount
                        })
                        
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Ошибка получения данных отчета: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _build_criteria(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Формирует условия фильтрации на основе параметров.
        
        Args:
            params: Параметры фильтрации
            
        Returns:
            Dict[str, Any]: Условия фильтрации
        """
        criteria = {}
        
        # Дата
        if params.get("start_date") and params.get("end_date"):
            start_date = datetime.strptime(params["start_date"], DATE_FORMATS["default"]).date()
            end_date = datetime.strptime(params["end_date"], DATE_FORMATS["default"]).date()
            criteria["card_date"] = {"$between": (start_date, end_date)}
        
        # Работник
        if params.get("workerid"):
            criteria["worker_id"] = params["workerid"]
            
        # Вид работы
        if params.get("worktypeid"):
            criteria["work_type_id"] = params["worktypeid"]
            
        # Изделие
        if params.get("productid"):
            criteria["product_id"] = params["productid"]
            
        # Контракт
        if params.get("contractid"):
            criteria["contract_id"] = params["contractid"]
            
        return criteria
    
    def _generate_summary(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует статистику по отчету.
        
        Args:
            df: DataFrame с данными
            params: Параметры отчета
            
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        summary = {
            "total_amount": 0,
            "total_cards": 0,
            "total_workers": 0,
            "total_products": 0,
            "total_contracts": 0,
            "start_date": "",
            "end_date": "",
            "works_count": 0
        }
        
        if df.empty:
            return summary
            
        # Общая сумма
        if "amount" in df.columns:
            summary["total_amount"] = df["amount"].sum()
            
        # Количество нарядов
        if "card_id" in df.columns:
            summary["total_cards"] = df["card_id"].nunique()
            
        # Количество работников
        if "worker_id" in df.columns:
            summary["total_workers"] = df["worker_id"].nunique()
            
        # Количество изделий
        if "product_id" in df.columns:
            summary["total_products"] = df["product_id"].nunique()
            
        # Количество контрактов
        if "contract_id" in df.columns:
            summary["total_contracts"] = df["contract_id"].nunique()
            
        # Количество работ
        if "work_type_id" in df.columns:
            summary["works_count"] = df["work_type_id"].nunique()
            
        # Даты
        if "card_date" in df.columns and not df["card_date"].empty:
            summary["start_date"] = df["card_date"].min().strftime(DATE_FORMATS["ui"])
            summary["end_date"] = df["card_date"].max().strftime(DATE_FORMATS["ui"])
            
        # Условия включения
        if not params.get("include_works_count", False):
            summary.pop("works_count", None)
        if not params.get("include_products_count", False):
            summary.pop("total_products", None)
        if not params.get("include_contracts_count", False):
            summary.pop("total_contracts", None)
            
        return summary
    
    def export_to_excel(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует отчет в Excel.
        
        Args:
            df: DataFrame с данными
            summary: Словарь со статистикой
            file_path: Путь для сохранения файла
            
        Returns:
            bool: True если экспорт успешен, иначе False
        """
        try:
            with pd.ExcelWriter(file_path) as writer:
                # Основной отчет
                df.to_excel(writer, sheet_name="Отчет", index=False)
                
                # Статистика
                pd.DataFrame.from_dict(summary, orient="index", columns=["Значение"]).to_excel(writer, sheet_name="Статистика")
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}", exc_info=True)
            return False
    
    def export_to_pdf(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует отчет в PDF.
        
        Args:
            df: DataFrame с данными
            summary: Словарь со статистикой
            file_path: Путь для сохранения файла
            
        Returns:
            bool: True если экспорт успешен, иначе False
        """
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.platypus import PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            
            # Создаем документ
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Заголовок
            elements.append(Paragraph("Отчет", styles["Title"]))
            elements.append(Spacer(1, 24))
            
            # Статистика
            elements.append(Paragraph("Статистика", styles["Heading2"]))
            for key, value in summary.items():
                elements.append(Paragraph(f"<b>{key}</b>: {value}", styles["Normal"]))
                elements.append(Spacer(1, 12))
                
            elements.append(Spacer(1, 24))
            
            # Данные
            elements.append(Paragraph("Данные", styles["Heading2"]))
            elements.append(Spacer(1, 12))
            
            # Преобразуем DataFrame в список списков
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Создаем таблицу
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Строим PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в PDF: {e}", exc_info=True)
            return False
    
    def export_to_html(self, df: pd.DataFrame, summary: Dict[str, Any], file_path: str) -> bool:
        """
        Экспортирует отчет в HTML.
        
        Args:
            df: DataFrame с данными
            summary: Словарь со статистикой
            file_path: Путь для сохранения файла
            
        Returns:
            bool: True если экспорт успешен, иначе False
        """
        try:
            template_path = Path("templates/report_template.html")
            
            # Чтение шаблона
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    template = f.read()
            else:
                template = self._generate_default_template()
                
            # Подготовка данных
            df_html = df.to_html(index=False, classes='report-table')
            summary_html = self._dict_to_html(summary)
            
            # Замена плейсхолдеров
            report_content = template.replace("{{summary}}", summary_html).replace("{{data}}", df_html)
            
            # Сохранение файла
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_content)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в HTML: {e}", exc_info=True)
            return False
    
    def _generate_default_template(self) -> str:
        """
        Генерирует стандартный шаблон HTML.
        
        Returns:
            str: HTML-шаблон
        """
        return """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Отчет</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #2c3e50; }
                .summary { margin-bottom: 30px; }
                .summary h2 { color: #34495e; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Отчет</h1>
            <div class="summary">{{summary}}</div>
            <div class="data">{{data}}</div>
        </body>
        </html>
        """
    
    def _dict_to_html(self, data: Dict[str, Any]) -> str:
        """
        Преобразует словарь в HTML.
        
        Args:
            data: Словарь данных
            
        Returns:
            str: HTML-представление словаря
        """
        html = "<h2>Статистика</h2><ul>"
        for key, value in data.items():
            html += f"<li><b>{key}</b>: {value}</li>"
        html += "</ul>"
        return html