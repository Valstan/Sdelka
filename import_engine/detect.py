from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

import pandas as pd
from utils.text import normalize_for_search


DocKind = Literal["orders", "job_types", "products", "contracts", "workers", "unknown"]


@dataclass
class Detected:
    kind: DocKind
    score: int
    sheet_index: int


def detect_sheet(df: pd.DataFrame) -> DocKind:
    cols_raw = [str(c) for c in df.columns]
    cols = [normalize_for_search(c) for c in cols_raw]

    def has_any(keys: list[str]) -> bool:
        return any(any(k in c for c in cols) for k in keys)

    # Orders first
    if has_any(["номер наряда", "order", "наряд"]) and has_any(["вид", "работ"]) and has_any(["кол", "qty"]) and has_any(["цена"]) and has_any(["сумма"]):
        return "orders"
    # Contracts before products to avoid misclassifying contracts as products
    if has_any(["номер контракта", "контракт", "договор", "шифр"]) and (has_any(["наименование"]) or has_any(["исполн", "игк", "вид контракт"])):
        return "contracts"
    # Job types (price list)
    if has_any(["вид", "наименование"]) and has_any(["ед", "unit"]) and has_any(["цена", "тариф"]):
        return "job_types"
    # Products: require explicit product markers to avoid catching 'номер контракта'
    if (has_any(["изделие", "зав", "серийн", "изд."])) and has_any(["№"]) and has_any(["контракт", "договор", "шифр", "номер контракта"]):
        return "products"
    # Workers
    if has_any(["фио", "сотрудник", "работник"]) and (has_any(["таб", "персонал"]) or has_any(["разряд", "должн"])):
        return "workers"
    return "unknown"


def detect_file(dfs: list[pd.DataFrame]) -> list[Detected]:
    out: list[Detected] = []
    for idx, df in enumerate(dfs):
        kind = detect_sheet(df)
        score = 1 if kind != "unknown" else 0
        out.append(Detected(kind=kind, score=score, sheet_index=idx))
    return out


