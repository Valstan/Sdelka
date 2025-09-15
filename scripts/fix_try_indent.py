#!/usr/bin/env python3
"""
Fix cases where a `try:` is followed by a statement on the same indent level
instead of an indented block. Inserts 4 spaces before the next line.

Creates .bak backups before editing a file.
"""
from __future__ import annotations

from pathlib import Path
import re


def fix_file(path: Path) -> int:
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines(keepends=True)
    changed = False
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]*)try:\s*(#.*)?$", line)
        if m and i + 1 < len(lines):
            next_line = lines[i + 1]
            indent = m.group("indent")
            # if next line starts with same indent (i.e., not indented for block)
            if re.match(rf"^{re.escape(indent)}\S", next_line):
                # indent the next line by 4 spaces
                lines[i + 1] = indent + "    " + next_line[len(indent) :]
                changed = True
        out_lines.append(lines[i])
        i += 1
    if changed:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)
        path.write_text("".join(lines), encoding="utf-8")
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
            print(f"Fixed try-indent in {p}")
            total += n
    print(f"Done. Files modified: {total}")


if __name__ == "__main__":
    main()
