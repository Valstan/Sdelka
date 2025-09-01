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
try:
    from import_export.excel_io import analyze_orders_workbook, import_xlsx_full  # type: ignore
except Exception:
    analyze_orders_workbook = None  # type: ignore[assignment]
    import_xlsx_full = None  # type: ignore[assignment]


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
    # Special-case CSV work orders like provided samples (лист один)
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

    # Special-case multi-sheet Excel workbooks with orders
    if p.suffix.lower() in {".xlsx", ".xls", ".ods"}:
        # Спец-обработка нарядов запускается, только если реально обнаружены листы с нарядами
        if preset in ("orders", "auto") and analyze_orders_workbook is not None and import_xlsx_full is not None:
            summary: list[dict] = []
            has_orders = False
            try:
                summary = analyze_orders_workbook(str(p))
                has_orders = any("date" in entry for entry in summary)
            except Exception:
                summary = []
                has_orders = False
            if dry_run and has_orders:
                parts: list[str] = ["<div>Обнаружены листы:</div>"]
                for entry in summary:
                    sheet = entry.get("sheet")
                    if "date" in entry:
                        parts.append(f"<div>Лист '{sheet}': наряды (дат: {entry.get('date')}, изделий: {len(entry.get('products') or [])}, работников: {len(entry.get('workers') or [])}, позиций: {len(entry.get('items') or [])})</div>")
                    elif "jobtypes_count" in entry:
                        parts.append(f"<div>Лист '{sheet}': прайс-лист (позиций: {entry.get('jobtypes_count')})</div>")
                    else:
                        parts.append(f"<div>Лист '{sheet}': пропущен</div>")
                Path("data").mkdir(exist_ok=True)
                report_path = Path("data") / f"import_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                write_html_report(report_path, f"Предварительный отчёт по импорту — {p.name}", parts)
                return DryRunReport(added=0, updated=0, skipped=0, warnings=None, details_html=str(report_path))
            if not dry_run and has_orders:
                if backup_before:
                    make_backup_copy(None)
                try:
                    # Если профиль 'orders' — импортируем только наряды, без справочников; в 'auto' включаем оба
                    include_jobtypes = (preset == "auto")
                    include_orders = True
                    jt_count, products_count, orders_count = import_xlsx_full(str(p), progress_cb, include_jobtypes=include_jobtypes, include_orders=include_orders)
                except Exception as exc:
                    raise RuntimeError(f"Ошибка импорта XLSX: {exc}")
                return ImportResult(added=int(orders_count), updated=0, skipped=0, errors=0, report_html_path=None)

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

    # Generic tabular readers (много листов/таблиц)
    dfs = read_any_tabular(p)
    forced_routes: list[tuple[str, int]] | None = None
    # Если единичная таблица (CSV/XLSX/ODS) со списком работников — принудительно маршрут как workers
    if len(dfs) == 1 and dfs and dfs[0] is not None:
        # Принудительно маршрутизируем как "workers", если обнаружены маркеры 'ФИО' + 'Табель' в колонках или первых строках
        df0 = dfs[0]
        cols_low = [str(c).strip().lower() for c in df0.columns]
        text_head = " ".join([";".join([str(x).strip().lower() for x in (list(df0.iloc[i, :]) if i < len(df0) else [])]) for i in range(min(5, len(df0)))])
        def has_worker_markers(s: str) -> bool:
            return (("фио" in s) and ("таб" in s or "табел" in s or "табель" in s or "персонал" in s)) or ("список" in s and ("работник" in s or "сотрудник" in s))
        if has_worker_markers(" ".join(cols_low)) or has_worker_markers(text_head):
            forced_routes = [("workers", 0)]
    routes = forced_routes if forced_routes is not None else split_and_route(dfs)
    # Если детектор посчитал все листы unknown (score=0), предупредим пользователя в dry-run
    detected = None
    try:
        from .detect import detect_file as _detect_file
        detected = _detect_file(dfs)
    except Exception:
        detected = None
    # Отфильтровать по профилю импорта
    if preset == "orders":
        routes = [(k, i) for (k, i) in routes if k == "orders"]
    elif preset == "price":
        routes = [(k, i) for (k, i) in routes if k == "job_types"]
    elif preset == "refs":
        routes = [(k, i) for (k, i) in routes if k in ("workers", "products", "contracts", "job_types")]
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
                # Подсветим, сколько строк с датой окончания распознано
                end_marked = sum(1 for r in ct if r.get("end_date"))
                html_parts.append(f"<div>Контракты: найдено строк: {len(ct)} (с датой окончания: {end_marked})</div>")
            elif kind == "workers":
                wk = parse_workers(dfs[idx])
                # Подсветим полноту данных
                with_tn = sum(1 for r in wk if r.get("personnel_no"))
                html_parts.append(f"<div>Работники: найдено строк: {len(wk)} (с таб. номером: {with_tn})</div>")
            elif kind == "orders":
                html_parts.append("<div>Наряды: обнаружен лист (используйте CSV-формат нарядов или XLSX с колонками)</div>")
            else:
                skips += 1
        # Если ничего не распознано
        if not routes and detected is not None:
            html_parts.append("<div><b>Файл не распознан.</b> Не найдено таблиц со структурами для импорта. Проверьте заголовки и формат.</div>")
        # Подсказки от детектора
        if detected is not None and any(d.hints for d in detected if d.kind != "unknown"):
            html_parts.append("<hr><div><b>Подсказки детектора:</b></div>")
            for d in detected:
                if d.kind == "unknown" or not d.hints:
                    continue
                html_parts.append(f"<div>Лист #{d.sheet_index+1}: тип {d.kind} (уверенность {d.score}). Подсказки: {d.hints}</div>")
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


