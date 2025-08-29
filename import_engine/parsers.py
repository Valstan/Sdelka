from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from utils.text import normalize_for_search
from .normalize import normalize_number_text, normalize_date_text


@dataclass
class ParsedBlock:
    kind: str
    rows: list[dict[str, Any]]


def parse_job_types(df: pd.DataFrame) -> list[dict[str, Any]]:
    cols = [str(c).strip().lower() for c in df.columns]
    name_col = next((c for c in df.columns if "вид" in str(c).lower() or "наимен" in str(c).lower()), None)
    unit_col = next((c for c in df.columns if "ед" in str(c).lower()), None)
    price_col = next((c for c in df.columns if "цена" in str(c).lower() or "тариф" in str(c).lower()), None)
    code_col = next((c for c in df.columns if "код" in str(c).lower()), None)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        name = str(r.get(name_col, "")).strip()
        unit = str(r.get(unit_col, "шт.")).strip() or "шт."
        price_raw = str(r.get(price_col, "0")).replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            price = float(price_raw)
        except Exception:
            continue
        if not name:
            continue
        out.append({"name": name, "unit": unit, "price": price, "code": str(r.get(code_col, "")).strip()})
    return out


def parse_products(df: pd.DataFrame) -> list[dict[str, Any]]:
    name_col = next((c for c in df.columns if "издел" in str(c).lower() or "наимен" in str(c).lower()), None)
    no_col = next((c for c in df.columns if "зав" in str(c).lower() or "номер" in str(c).lower() or "№" in str(c).lower()), None)
    contract_col = next((c for c in df.columns if "контракт" in str(c).lower() or "договор" in str(c).lower() or "шифр" in str(c).lower()), None)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        name = str(r.get(name_col, "")).strip()
        prod_no = str(r.get(no_col, "")).strip()
        contract_code = str(r.get(contract_col, "")).strip()
        if not (name and prod_no):
            continue
        out.append({"name": name, "product_no": prod_no, "contract_code": contract_code})
    return out


def parse_contracts(df: pd.DataFrame) -> list[dict[str, Any]]:
    code_col = next((c for c in df.columns if "шифр" in str(c).lower() or "номер" in str(c).lower()), None)
    name_col = next((c for c in df.columns if "наимен" in str(c).lower()), None)
    type_col = next((c for c in df.columns if "вид контракт" in str(c).lower() or "вид" in str(c).lower()), None)
    exec_col = next((c for c in df.columns if "исполн" in str(c).lower()), None)
    igk_col = next((c for c in df.columns if "игк" in str(c).lower()), None)
    cn_col = next((c for c in df.columns if "номер контракт" in str(c).lower()), None)
    acc_col = next((c for c in df.columns if "счет" in str(c).lower()), None)
    start_col = next((c for c in df.columns if "начал" in str(c).lower() or "заключ" in str(c).lower()), None)
    end_col = next((c for c in df.columns if "оконч" in str(c).lower() or "исполн" in str(c).lower()), None)
    desc_col = next((c for c in df.columns if "коммент" in str(c).lower() or "опис" in str(c).lower()), None)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        code = str(r.get(code_col, "")).strip()
        if not code:
            continue
        out.append({
            "code": code,
            "name": str(r.get(name_col, "")).strip() or None,
            "contract_type": str(r.get(type_col, "")).strip() or None,
            "executor": str(r.get(exec_col, "")).strip() or None,
            "igk": str(r.get(igk_col, "")).strip() or None,
            "contract_number": str(r.get(cn_col, "")).strip() or None,
            "bank_account": str(r.get(acc_col, "")).strip() or None,
            "start_date": normalize_date_text(str(r.get(start_col, "")).strip() or None),
            "end_date": normalize_date_text(str(r.get(end_col, "")).strip() or None),
            "description": str(r.get(desc_col, "")).strip() or None,
        })
    return out


def parse_workers(df: pd.DataFrame) -> list[dict[str, Any]]:
    fio_col = next((c for c in df.columns if "фио" in str(c).lower() or "сотрудник" in str(c).lower()), None)
    tab_col = next((c for c in df.columns if "таб" in str(c).lower() or "персонал" in str(c).lower()), None)
    pos_col = next((c for c in df.columns if "должн" in str(c).lower() or "разряд" in str(c).lower()), None)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        fio = str(r.get(fio_col, "")).strip()
        if not fio:
            continue
        out.append({
            "full_name": fio,
            "personnel_no": str(r.get(tab_col, "")).strip() or f"AUTO-{normalize_for_search(fio)}",
            "position": str(r.get(pos_col, "")).strip() or None,
        })
    return out



