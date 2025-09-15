from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Any

import pandas as pd
from utils.text import normalize_for_search


DocKind = Literal["orders", "job_types", "products", "contracts", "workers", "unknown"]


@dataclass
class Detected:
    kind: DocKind
    score: int
    sheet_index: int
    hints: dict[str, Any] | None = None


def detect_sheet(df: pd.DataFrame) -> tuple[DocKind, int, dict[str, Any] | None]:
    cols_raw = [str(c) for c in df.columns]
    cols = [normalize_for_search(c) for c in cols_raw]

    def has_any(keys: list[str]) -> bool:
        return any(any(k in c for c in cols) for k in keys)

    # Scoring approach
    scores: dict[DocKind, int] = {
        "orders": 0,
        "job_types": 0,
        "products": 0,
        "contracts": 0,
        "workers": 0,
        "unknown": 0,
    }
    hints: dict[str, Any] = {}

    # Scan first lines as loose header text
    try:
        scan_limit = min(8, len(df))
        head_lines: list[str] = []
        for i in range(scan_limit):
            try:
                row_vals = [str(x).strip().lower() for x in df.iloc[i].tolist()]
            except Exception:
                row_vals = []
            head_lines.append(" ".join(row_vals))
        head_text = "\n".join(head_lines)
    except Exception:
        head_text = ""

    # Orders
    if has_any(["номер наряда", "order", "наряд"]):
        scores["orders"] += 2
    if has_any(["дата"]):
        scores["orders"] += 1
    if (
        has_any(["вид", "работ"])
        and has_any(["ед"])
        and has_any(["цена", "расценка"])
        and has_any(["сумма"])
    ):
        scores["orders"] += 3

    # Contracts
    if has_any(["номер контракта", "контракт", "договор", "шифр"]):
        scores["contracts"] += 2
    if has_any(
        [
            "игк",
            "исполнител",
            "вид контракт",
            "начал",
            "заключ",
            "оконч",
            "действует до",
        ]
    ):
        scores["contracts"] += 2

    # Job types (price list)
    unit_keys = ["ед", "unit", "единиц", "изм"]
    price_keys = ["цена", "тариф", "расцен", "стоим"]
    if has_any(["вид", "наимен"]) and has_any(unit_keys):
        scores["job_types"] += 2
    if has_any(price_keys):
        scores["job_types"] += 2
    if (
        ("вид" in head_text or "наимен" in head_text)
        and any(k in head_text for k in unit_keys)
        and any(k in head_text for k in price_keys)
    ):
        scores["job_types"] += 2

    # Products
    if has_any(["изделие", "зав", "серийн", "изд."]):
        scores["products"] += 2
    if has_any(["№", "номер"]) and has_any(
        ["контракт", "договор", "шифр", "номер контракта"]
    ):
        scores["products"] += 2

    # Workers
    if has_any(["фио", "сотрудник", "работник"]) and (
        has_any(["таб", "персонал"]) or has_any(["разряд", "должн"])
    ):
        scores["workers"] += 3
    has_fio_split = (
        any("фамил" in c for c in cols) and any(c.strip() == "имя" for c in cols_raw)
    ) or any("отче" in c for c in cols)
    has_worker_attrs = (
        has_any(["таб", "табел", "табель", "персонал", "tn", "personnel"])
        or has_any(["разряд", "должн"])
        or has_any(["цех", "отдел", "подраздел", "участок", "бригада"])
    )
    if has_fio_split and has_worker_attrs:
        scores["workers"] += 2
    if "список" in head_text and ("работник" in head_text or "сотрудник" in head_text):
        scores["workers"] += 1

    # Hints for best kind
    def _guess_job_types_hints() -> dict[str, Any]:
        name_col = next(
            (
                c
                for c in df.columns
                if "вид" in str(c).lower() or "наимен" in str(c).lower()
            ),
            None,
        )
        unit_col = next(
            (c for c in df.columns if any(k in str(c).lower() for k in unit_keys)), None
        )
        price_col = next(
            (c for c in df.columns if any(k in str(c).lower() for k in price_keys)),
            None,
        )
        return {"name_col": name_col, "unit_col": unit_col, "price_col": price_col}

    def _guess_workers_hints() -> dict[str, Any]:
        fio_col = next(
            (
                c
                for c in df.columns
                if "фио" in str(c).lower()
                or "сотрудник" in str(c).lower()
                or "работник" in str(c).lower()
            ),
            None,
        )
        fam_col = next((c for c in df.columns if "фамил" in str(c).lower()), None)
        im_col = next(
            (c for c in df.columns if str(c) and "имя" == str(c).strip().lower()), None
        )
        otch_col = next((c for c in df.columns if "отче" in str(c).lower()), None)
        tab_col = next(
            (
                c
                for c in df.columns
                if any(
                    k in str(c).lower()
                    for k in ("таб", "табел", "табель", "персонал", "tn", "personnel")
                )
            ),
            None,
        )
        dept_col = next(
            (
                c
                for c in df.columns
                if any(
                    k in str(c).lower()
                    for k in ("цех", "отдел", "подраздел", "участок", "бригада")
                )
            ),
            None,
        )
        return {
            "fio_col": fio_col or "+Ф/И/О",
            "fam_col": fam_col,
            "im_col": im_col,
            "otch_col": otch_col,
            "personnel_no_col": tab_col,
            "dept_col": dept_col,
        }

    best_kind: DocKind = max(scores, key=lambda k: scores[k])  # type: ignore[arg-type]
    best_score = scores[best_kind]
    if best_score < 3:
        return ("unknown", 0, None)
    if best_kind == "job_types":
        hints = _guess_job_types_hints()
    elif best_kind == "workers":
        hints = _guess_workers_hints()
    else:
        hints = {}
    return (best_kind, best_score, hints or None)


def detect_file(dfs: list[pd.DataFrame]) -> list[Detected]:
    out: list[Detected] = []
    for idx, df in enumerate(dfs):
        kind, score, hints = detect_sheet(df)
        out.append(Detected(kind=kind, score=score, sheet_index=idx, hints=hints))
    return out
