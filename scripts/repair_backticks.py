#!/usr/bin/env python3
"""
Replace accidental literal backtick-n sequences (`n) in .py files with real newlines.
Creates .bak backups. Run locally with Python 3.
"""
from __future__ import annotations

from pathlib import Path


def files_to_fix(root: Path):
    for p in root.rglob("*.py"):
        if any(part in ("venv", ".venv", ".git") for part in p.parts):
            continue
        yield p


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if "`n" not in text:
        return 0
    new = text.replace("`n", "\n")
    bak = path.with_suffix(path.suffix + ".bak")
    path.replace(bak)
    path.write_text(new, encoding="utf-8")
    return 1


def main() -> None:
    root = Path(".")
    total = 0
    for p in files_to_fix(root):
        try:
            n = fix_file(p)
        except Exception as exc:
            print(f"Failed to process {p}: {exc}")
            continue
        if n:
            print(f"Fixed {p}")
            total += n
    print(f"Done. Files fixed: {total}")


if __name__ == "__main__":
    main()
