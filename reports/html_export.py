from __future__ import annotations

import pandas as pd


_ABBR = {
    "Количество": "Кол-во",
    "Номер": "№",
    "Номер изделия": "№ изд.",
    "Номер_изделия": "№ изд.",
}


def _apply_abbreviations(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c: _ABBR.get(str(c), c) for c in df.columns}
    return df.rename(columns=cols)


def dataframe_to_html(df: pd.DataFrame, title: str | None = None) -> str:
    df2 = _apply_abbreviations(df)
    html = df2.to_html(index=False)
    if title:
        return f"<h2>{title}</h2>\n" + html
    return html


def save_html(df: pd.DataFrame, file_path: str, title: str | None = None) -> None:
    html = dataframe_to_html(df, title=title)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)