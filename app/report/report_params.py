from datetime import datetime, date
from tkinter import messagebox
from typing import Dict, Any
from app.config import DATE_FORMATS


class ReportParams:
    @staticmethod
    def get_params(form) -> Dict[str, Any]:
        params = {}

        # Даты
        if form.period_combo.get() == "Произвольный период":
            try:
                from_date = date(
                    int(form.from_year.get()),
                    int(form.from_month.get()),
                    int(form.from_day.get())
                )
                to_date = date(
                    int(form.to_year.get()),
                    int(form.to_month.get()),
                    int(form.to_day.get())
                )
                if from_date > to_date:
                    messagebox.showerror("Ошибка", "Дата начала не может быть позже даты окончания")
                    return None

                params['start_date'] = from_date.strftime(DATE_FORMATS['default'])
                params['end_date'] = to_date.strftime(DATE_FORMATS['default'])
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректная дата")
                return None
        else:
            try:
                params['start_date'] = date(
                    int(form.from_year.get()),
                    int(form.from_month.get()),
                    int(form.from_day.get())
                ).strftime(DATE_FORMATS['default'])
                params['end_date'] = date(
                    int(form.to_year.get()),
                    int(form.to_month.get()),
                    int(form.to_day.get())
                ).strftime(DATE_FORMATS['default'])
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректная дата")
                return None

        # Работник
        worker_item = form.worker_combo.get_selected_item()
        if worker_item and worker_item.get('id', 0) != 0:
            params['worker_id'] = worker_item['id']

        # Вид работы
        work_type_item = form.work_type_combo.get_selected_item()
        if work_type_item and work_type_item.get('id', 0) != 0:
            params['work_type_id'] = work_type_item['id']

        # Изделие
        product_item = form.product_combo.get_selected_item()
        if product_item and product_item.get('id', 0) != 0:
            params['product_id'] = product_item['id']

        # Контракт
        contract_item = form.contract_combo.get_selected_item()
        if contract_item and contract_item.get('id', 0) != 0:
            params['contract_id'] = contract_item['id']

        # Дополнительные параметры
        params['include_works_count'] = form.include_works_count_var.get()
        params['include_products_count'] = form.include_products_count_var.get()
        params['include_contracts_count'] = form.include_contracts_count_var.get()

        return params

    @staticmethod
    def validate_dates(start_date: str, end_date: str) -> bool:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start <= end
        except ValueError:
            return False
