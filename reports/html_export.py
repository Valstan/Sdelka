from __future__ import annotations

import pandas as pd

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


def dataframe_to_html(df: pd.DataFrame, title: str | None = None) -> str:
    df2 = normalize_headers(df)
    html = df2.to_html(index=False)
    if title:
        return f"<h2>{title}</h2>\n" + html
    return html


def save_html(df: pd.DataFrame, title: str | None, path: str) -> str:
    df2 = normalize_headers(df)
    html = dataframe_to_html(df2, title=title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path