from __future__ import annotations

import pandas as pd
from typing import Any

import logging

_ABBR = {
    "Количество": "Кол-во",
    "Номер": "№",
    "Номер изделия": "№ изд.",
    "Номер_изделия": "№ изд.",
}


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    # Сначала применим известные сокращения
    df1 = df.rename(columns={c: _ABBR.get(str(c), c) for c in df.columns})

    # Затем общий постпроцессинг: подчеркивания -> пробелы, слова -> аббревиатуры
    def norm(name: str) -> str:
        s = str(name).replace("_", " ")
        s = s.replace("Номер изделия", "№ изд.")
        s = s.replace("Номер", "№")
        s = s.replace("Количество", "Кол-во")
        return s

    return df1.rename(columns={c: norm(c) for c in df1.columns})


def dataframe_to_html(
    df: pd.DataFrame, title: str | None = None, context: dict[str, Any] | None = None
) -> str:
    df2 = normalize_headers(df)
    # Если отчет по одному работнику — убираем колонки Работник/Цех из таблицы
    if context and context.get("single_worker_short"):
        for c in ("Работник", "Цех"):
            if c in df2.columns:
                try:
                    df2 = df2.drop(columns=[c])
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
    html = df2.to_html(index=False)
    parts: list[str] = []
    if title:
        parts.append(f"<h2>{title}</h2>")
    if context:
        header_lines: list[str] = []
        created = context.get("created_at")
        if created:
            header_lines.append(f"Дата составления: {created}")
        period = context.get("period")
        if period:
            header_lines.append(period)
        single_worker = context.get("single_worker_short")
        dept = context.get("dept_name")
        # Если один работник — показываем только его цех, иначе общий цех фильтра
        if single_worker:
            single_worker_dept = context.get("single_worker_dept")
            header_lines.append(f"Работник: {single_worker}")
            if single_worker_dept:
                header_lines.append(f"Цех: {single_worker_dept}")
        else:
            if dept:
                header_lines.append(f"Цех: {dept}")
        if header_lines:
            parts.append("<p>" + "<br/>".join(header_lines) + "</p>")
    parts.append(html)
    if context:
        parts.append("<hr/>")
        total = context.get("total_amount")
        if total is not None:
            parts.append(f"<p><b>Итого по отчету: {float(total):.2f}</b></p>")
        workers = context.get("worker_signatures") or []
        single_worker = context.get("single_worker_short")
        if single_worker:
            parts.append("<p><b>Подписи:</b></p>")
            parts.append(f"<p>{single_worker} _____________</p>")
        elif workers:
            parts.append("<p><b>Подписи работников:</b></p>")
            parts.append("<p>" + ", &nbsp;".join(workers) + "</p>")
        dept_head = context.get("dept_head")
        hr_head = context.get("hr_head")
        parts.append(f"<p>Начальник цеха: {dept_head or ''} _____________</p>")
        parts.append(f"<p>Начальник отдела кадров: {hr_head or ''} _____________</p>")
    return "\n".join(parts)


def save_html(
    df: pd.DataFrame,
    title: str | None,
    path: str,
    context: dict[str, Any] | None = None,
) -> str:
    df2 = normalize_headers(df)
    html = dataframe_to_html(df2, title=title, context=context)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
