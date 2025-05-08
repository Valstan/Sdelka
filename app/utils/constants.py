# app/utils/constants.py
from datetime import date

DATE_FORMATS = {
    "default": "%Y-%m-%d",
    "ui": "%d.%m.%Y",
    "report": "%d %B %Y"
}

CURRENCY_FORMATS = {
    "default": "руб.",
    "short": "руб."
}

DEFAULT_REPORT_PARAMS = {
    "start_date": date.today().replace(day=1),
    "end_date": date.today(),
    "include_works_count": True,
    "include_products_count": True,
    "include_contracts_count": True
}