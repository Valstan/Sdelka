#!/usr/bin/env python3
"""
Scan .py files and insert `import logging` near top if the file uses `logging.` but does not import logging.
Creates .bak backups before editing.

Run: py scripts/add_missing_logging.py
"""
from __future__ import annotations

from pathlib import Path
import re


def needs_logging(text: str) -> bool:
    return "logging." in text or "logging.getLogger" in text


def has_logging_import(text: str) -> bool:
    return (
        re.search(
            r"^\s*(import\s+logging|from\s+logging\s+import\s+)", text, flags=re.M
        )
        is not None
    )


def insert_import(text: str) -> str:
    # Try to insert after __future__ imports or after module docstring, else at top
    lines = text.splitlines(keepends=True)
    insert_at = 0
    # skip shebang
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    # skip a block of __future__ imports
    for i, ln in enumerate(lines[insert_at:], start=insert_at):
        if re.match(r"from __future__ import", ln):
            insert_at = i + 1
            continue
        # if a blank line after docstring, insert later
        if ln.strip() == "":
            insert_at = i + 1
            continue
        # if an import line, move past consecutive imports
        if ln.lstrip().startswith("import") or ln.lstrip().startswith("from"):
            insert_at = i + 1
            continue
        break
    lines.insert(insert_at, "import logging\n")
    return "".join(lines)


def fix_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8")
    if needs_logging(txt) and not has_logging_import(txt):
        bak = p.with_suffix(p.suffix + ".bak")
        p.replace(bak)
        new = insert_import(txt)
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


def main() -> None:
    total = 0
    for p in Path(".").rglob("*.py"):
        if any(part in ("venv", ".venv", ".git") for part in p.parts):
            continue
        try:
            n = fix_file(p)
        except Exception as exc:
            print(f"Failed {p}: {exc}")
            continue
        if n:
            print(f"Inserted logging import in {p}")
            total += n
    print(f"Done. Files modified: {total}")


if __name__ == "__main__":
    main()
