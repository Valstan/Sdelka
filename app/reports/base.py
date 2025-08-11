from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd


@dataclass(slots=True)
class ReportContext:
    title: str
    filters: dict[str, str]


class ReportStrategy(Protocol):
    def generate(self, df: pd.DataFrame, output_path: Path, context: ReportContext) -> Path:
        ...