from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from .detect import detect_file


def split_and_route(dfs: list[pd.DataFrame]) -> list[tuple[str, int]]:
    """Return list of (kind, index) for each detected block.

    If unknown, skip for now (could prompt user later).
    """
    detected = detect_file(dfs)
    out: list[tuple[str, int]] = []
    for d in detected:
        if d.kind != "unknown":
            out.append((d.kind, d.sheet_index))
    return out


