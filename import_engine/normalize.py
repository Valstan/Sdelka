from __future__ import annotations

import re
from datetime import datetime, timedelta


import logging

RU_MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}


def normalize_number_text(val: str | float | int | None) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("\xa0", " ").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def normalize_date_text(val: str | None) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    # Try to interpret Excel serial dates
    try:
        # pandas may pass floats for Excel dates; reject huge or tiny values safely
        if s.replace(".", "", 1).isdigit():
            num = float(s)
            # Excel serial dates start at 1899-12-30; valid range safeguard
            if 1 <= num <= 80000:
                base = datetime(1899, 12, 30)
                return (base + timedelta(days=int(num))).strftime("%Y-%m-%d")
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
    # dd.mm.yyyy or dd.mm.yy
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{2,4})$", s)
    if m:
        day, mon, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, mon, day).strftime("%Y-%m-%d")
        except Exception:
            return None
    # yyyy-mm-dd
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    # text months (ru/eng), e.g. 12 марта 2025
    m = re.match(r"^(\d{1,2})\s+([A-Za-zА-Яа-я\.]+)\s+(\d{4})$", s)
    if m:
        day = int(m.group(1))
        mon_name = m.group(2).lower()
        year = int(m.group(3))
        mon = None
        for key, num in RU_MONTHS.items():
            if mon_name.startswith(key):
                mon = num
                break
        if mon is None:
            # try english
            try:
                mon = datetime.strptime(mon_name[:3], "%b").month
            except Exception:
                return None
        try:
            return datetime(year, mon, day).strftime("%Y-%m-%d")
        except Exception:
            return None
    return None
