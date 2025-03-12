import unittest
from unittest.mock import MagicMock

# Импортируйте ваш класс/модуль отчетов
from app.Report.report_service import ReportService

class TestReportService(unittest.TestCase):
    def setUp(self):
        # Создаем mock для базы данных
        self.db_mock = MagicMock()

        # Создаем экземпляр сервиса отчетов с mock-базой данных
        self.report_service = ReportService(self.db_mock)

        # Подготавливаем тестовые данные
        self.setup_test_data()

    def setup_test_data(self):
        """Устанавливает тестовые данные для отчетов"""
        # Тестовые данные для отчета
        self.test_report_data = [
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

    def test_generate_report_empty_data(self):
        """Тест генерации отчета с пустыми данными"""
        # Настраиваем mock для возврата пустого списка
        self.db_mock.get_report_data.return_value = []

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
        self.assertTrue(df.empty)
        self.assertEqual(summary, {})

        # Проверяем, что метод базы данных был вызван с правильными параметрами
        self.db_mock.get_report_data.assert_called_once_with(
            worker_id=0,
            start_date="20230101",
            end_date="20230131",
            work_type_id=0,
            product_id=0,
            contract_id=0
        )

    def test_generate_report_with_data(self):
        """Тест генерации отчета с данными"""
        # Настраиваем mock для возврата тестовых данных
        self.db_mock.get_report_data.return_value = self.test_report_data

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

        # Проверяем, что у каждого работника правильная сумма
        worker_amounts = df[df["worker_amount"].notnull()]["worker_amount"].tolist()
        self.assertEqual(worker_amounts, [500.0, 500.0])

    def test_generate_report_with_amounts_split(self):
        """Тест генерации отчета с разделением сумм"""
        # Копируем тестовые данные без worker_amount (чтобы проверить логику разделения)
        test_data_without_worker_amount = []
        for item in self.test_report_data:
            item_copy = item.copy()
            del item_copy["worker_amount"]
            test_data_without_worker_amount.append(item_copy)

        # Настраиваем mock для возврата данных без worker_amount
        self.db_mock.get_report_data.return_value = test_data_without_worker_amount

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

        # Проверяем, что сумма была разделена между работниками
        worker_amounts = df["amount"].tolist()
        self.assertEqual(worker_amounts, [500.0, 500.0])

    def test_generate_report_with_stats(self):
        """Тест генерации отчета с дополнительной статистикой"""
        # Настраиваем mock для возврата тестовых данных
        self.db_mock.get_report_data.return_value = self.test_report_data

        # Вызываем метод генерации отчета с запросом доп. статистики
        df, summary = self.report_service.generate_report({
            "workerid": 0,
            "startdate": "20230101",
            "enddate": "20230131",
            "worktypeid": 0,
            "productid": 0,
            "contractid": 0,
            "includeworkscount": True,
            "includeproductscount": True,
            "includecontractscount": True
        })

        # Проверяем результаты
        self.assertEqual(summary["total_amount"], 1000.0)
        self.assertEqual(summary["works_count"], 1)  # Одна работа с двумя сотрудниками
        self.assertEqual(summary["products_count"], 1)  # Одно изделие
        self.assertEqual(summary["contracts_count"], 1)  # Один контракт

    def test_error_handling(self):
        """Тест обработки ошибок при генерации отчета"""
        # Настраиваем mock для вызова исключения
        self.db_mock.get_report_data.side_effect = Exception("Test exception")

        # Вызываем метод генерации отчета
        df, summary = self.report_service.generate_report({
            "workerid": 0,
            "startdate": "20230101",
            "enddate": "20230131"
        })

        # Проверяем результаты (должен вернуть пустой DataFrame и пустой словарь)
        self.assertTrue(df.empty)
        self.assertEqual(summary, {})

if __name__ == "__main__":
    unittest.main()