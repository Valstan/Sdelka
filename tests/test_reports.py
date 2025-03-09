import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

# Импортируйте ваш класс/модуль отчетов
from app.services.report_service import ReportService

class TestReports(unittest.TestCase):
    def setUp(self):
        # Создаем mock для репозитория работ
        self.work_repository_mock = MagicMock()

        # Создаем экземпляр сервиса отчетов с mock-репозиторием
        self.report_service = ReportService(self.work_repository_mock)

        # Подготавливаем тестовые данные
        self.setup_test_data()

    def setup_test_data(self):
        """Устанавливает тестовые данные для отчетов"""
        # Тестовые данные для отчета по работникам
        self.worker_report_data = [
            {
                "last_name": "Иванов",
                "first_name": "Иван",
                "middle_name": "Иванович",
                "card_number": "N001",
                "card_date": "2023-01-01",
                "work_item_id": 1,
                "quantity": 2.0,
                "amount": 1000.0,
                "work_name": "Сборка",
                "product_number": "P001",
                "product_type": "Изделие А",
                "contract_number": "C001",
                "product_id": 1,
                "contract_id": 1,
                "worker_amount": 500.0
            },
            {
                "last_name": "Петров",
                "first_name": "Петр",
                "middle_name": "Петрович",
                "card_number": "N001",
                "card_date": "2023-01-01",
                "work_item_id": 1,
                "quantity": 2.0,
                "amount": 1000.0,
                "work_name": "Сборка",
                "product_number": "P001",
                "product_type": "Изделие А",
                "contract_number": "C001",
                "product_id": 1,
                "contract_id": 1,
                "worker_amount": 500.0
            }
        ]

    def test_worker_report_generation(self):
        """Тест генерации отчета по работникам"""
        # Настраиваем mock для возврата тестовых данных
        self.work_repository_mock.get_report_data.return_value = self.worker_report_data

        # Вызываем метод генерации отчета
        df, summary = self.report_service.generate_report({
            "workerid": 0,
            "startdate": "20230101",
            "enddate": "20230131",
            "worktypeid": 0,
            "productid": 0,
            "contractid": 0
        })

        # Проверяем результаты
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)  # Два работника в тесте
        self.assertEqual(summary["total_amount"], 1000.0)  # Общая сумма должна быть 1000

        # Проверяем суммы для работников
        self.assertTrue("worker_amount" in df.columns or "amount" in df.columns)

        # Формируем имена работников
        if "worker_name" in df.columns:
            worker_names = df["worker_name"].tolist()
        else:
            # Создаем имена вручную, если их нет в DataFrame
            worker_names = []
            for _, row in df.iterrows():
                if all(col in df.columns for col in ["last_name", "first_name", "middle_name"]):
                    name = f"{row['last_name']} {row['first_name'][0]}.{row['middle_name'][0] if row['middle_name'] else ''}"
                    worker_names.append(name)

        # Проверяем, что все работники представлены в отчете
        self.assertEqual(len(set(worker_names)), 2)

    def test_worker_report_with_split_amounts(self):
        """Тест разделения сумм между работниками в отчете"""
        # Копируем тестовые данные без worker_amount (чтобы проверить логику разделения)
        test_data_without_worker_amount = []
        for item in self.worker_report_data:
            item_copy = item.copy()
            if "worker_amount" in item_copy:
                del item_copy["worker_amount"]
            test_data_without_worker_amount.append(item_copy)

        # Настраиваем mock для возврата данных без worker_amount
        self.work_repository_mock.get_report_data.return_value = test_data_without_worker_amount

        # Вызываем метод генерации отчета
        df, summary = self.report_service.generate_report({
            "workerid": 0,
            "startdate": "20230101",
            "enddate": "20230131",
            "worktypeid": 0,
            "productid": 0,
            "contractid": 0
        })

        # Проверяем, что сумма была разделена между работниками
        if "amount" in df.columns:
            amounts = df["amount"].tolist()
            # Суммы должны быть разделены поровну между двумя работниками
            total_sum = sum(amounts)
            self.assertEqual(total_sum, 1000.0)

            # Проверяем, что суммы для всех работников одинаковы
            # (поскольку у нас одинаковая работа для всех)
            self.assertEqual(amounts[0], amounts[1])

if __name__ == "__main__":
    unittest.main()