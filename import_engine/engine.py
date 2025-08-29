from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal

import sqlite3
from datetime import datetime
import os

from db.sqlite import get_connection
from utils.text import normalize_for_search
from .readers import read_any_tabular
from .resolve import split_and_route
from .parsers import parse_job_types, parse_products, parse_contracts, parse_workers
from .commit import upsert_job_types, upsert_products, upsert_contracts, upsert_workers
from .reporting import write_html_report
from .backup import make_backup_copy
from .orders_csv import detect_orders_csv, import_orders_from_csv
from import_export.products_contracts_import import import_products_from_contracts_csv  # type: ignore


ProgressCb = Callable[[int, int, str], None]


@dataclass
class DryRunReport:
    added: int = 0
    updated: int = 0
    skipped: int = 0
    warnings: list[str] | None = None
    details_html: str | None = None


@dataclass
class ImportResult:
    added: int
    updated: int
    skipped: int
    errors: int
    report_html_path: str | None = None


def import_data(
    path: str | Path,
    *,
    dry_run: bool = True,
    preset: Literal["auto", "price", "orders", "refs"] = "auto",
    progress_cb: ProgressCb | None = None,
    backup_before: bool = True,
) -> DryRunReport | ImportResult:
    """Unified import entrypoint."""
    p = Path(path)
    if progress_cb:
        progress_cb(0, 1, f"Открытие файла: {p.name}")
    # Special-case CSV work orders like provided samples
    if p.suffix.lower() == ".csv" and detect_orders_csv(p):
        if dry_run:
            # parse and render small HTML summary
            from .orders_csv import parse_orders_csv
            parsed = parse_orders_csv(p)
            rows = [
                f"<p>Обнаружен наряд (CSV). Работников: {len(parsed.workers)}, изделий: {len(parsed.products)}, позиций: {len(parsed.items)}.</p>",
            ]
            Path("data").mkdir(exist_ok=True)
            report_path = Path("data") / f"import_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            write_html_report(report_path, f"Предварительный отчёт по импорту — {p.name}", rows)
            return DryRunReport(added=0, updated=0, skipped=0, warnings=None, details_html=str(report_path))
        if backup_before:
            make_backup_copy(None)
        res = import_orders_from_csv(p, progress_cb)
        return ImportResult(added=int(res.get("orders", 0)), updated=0, skipped=0, errors=0, report_html_path=None)

    # Special-case CSV ledger with products and contracts (Оборотно-сальдовая ведомость 002)
    if p.suffix.lower() == ".csv" and _detect_ledger_csv(p):
        if dry_run:
            rows = _summarize_ledger_csv(p)
            Path("data").mkdir(exist_ok=True)
            report_path = Path("data") / f"import_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            write_html_report(report_path, f"Предварительный отчёт по импорту — {p.name}", rows)
            return DryRunReport(added=0, updated=0, skipped=0, warnings=None, details_html=str(report_path))
        if backup_before:
            make_backup_copy(None)
        stats = import_products_from_contracts_csv(str(p), progress_cb)
        return ImportResult(added=int(stats.get("products", 0)), updated=0, skipped=0, errors=int(stats.get("errors", 0)), report_html_path=None)

    # Generic tabular readers
    dfs = read_any_tabular(p)
    routes = split_and_route(dfs)
    adds = 0
    ups = 0
    skips = 0
    warn: list[str] = []

    # Dry-run: just count and present summary
    if dry_run:
        html_parts: list[str] = []
        for kind, idx in routes:
            if kind == "job_types":
                jt = parse_job_types(dfs[idx])
                html_parts.append(f"<div>Виды работ: найдено строк: {len(jt)}</div>")
            elif kind == "products":
                pr = parse_products(dfs[idx])
                html_parts.append(f"<div>Изделия: найдено строк: {len(pr)}</div>")
            elif kind == "contracts":
                ct = parse_contracts(dfs[idx])
                html_parts.append(f"<div>Контракты: найдено строк: {len(ct)}</div>")
            elif kind == "workers":
                wk = parse_workers(dfs[idx])
                html_parts.append(f"<div>Работники: найдено строк: {len(wk)}</div>")
            elif kind == "orders":
                html_parts.append("<div>Наряды: обнаружен лист (используйте CSV-формат нарядов или XLSX с колонками)</div>")
            else:
                skips += 1
        Path("data").mkdir(exist_ok=True)
        report_path = Path("data") / f"import_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        write_html_report(report_path, f"Предварительный отчёт по импорту — {p.name}", html_parts)
        return DryRunReport(added=adds, updated=ups, skipped=skips, warnings=warn or None, details_html=str(report_path))

    # Real import
    if backup_before:
        make_backup_copy(None)
    with get_connection() as conn:
        for kind, idx in routes:
            if kind == "job_types":
                rows = parse_job_types(dfs[idx])
                a, u = upsert_job_types(conn, rows)
                adds += a
                ups += u
            elif kind == "products":
                rows = parse_products(dfs[idx])
                a, u = upsert_products(conn, rows)
                adds += a
                ups += u
            elif kind == "contracts":
                rows = parse_contracts(dfs[idx])
                a, u = upsert_contracts(conn, rows)
                adds += a
                ups += u
            elif kind == "workers":
                rows = parse_workers(dfs[idx])
                a, u = upsert_workers(conn, rows)
                adds += a
                ups += u
            elif kind == "orders":
                warn.append("Импорт нарядов из общих таблиц будет добавлен отдельно. Для CSV используйте текущую поддержку.")

    return ImportResult(added=adds, updated=ups, skipped=skips, errors=0, report_html_path=None)


def _detect_ledger_csv(p: Path) -> bool:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    head = "\n".join(text.splitlines()[:50])
    if "Оборотно-сальдовая ведомость" in head and "002" in head:
        return True
    # heuristic: many lines with "Двигатель" and "БУ"
    cnt = 0
    for line in text.splitlines()[:200]:
        if "Двигатель" in line and "БУ" in line:
            cnt += 1
    return cnt >= 5


def _summarize_ledger_csv(p: Path) -> list[str]:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ["<div>Не удалось прочитать файл</div>"]
    lines = text.splitlines()
    prod = 0
    contracts = 0
    for line in lines:
        if "Двигатель" in line and "№" in line:
            prod += 1
        if "Договор" in line or "договор" in line:
            contracts += 1
    return [f"<div>Обнаружена оборотно-сальдовая ведомость.</div>", f"<div>Строк с изделиями: {prod}</div>", f"<div>Строк с договорами: {contracts}</div>"]


