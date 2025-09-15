#!/usr/bin/env python3
"""
More robust fixer for misplaced try/except indentation.

For every `try:` line, it ensures that the following block lines up to the matching
`except`/`finally` (or blank line) are indented one level deeper than the `try:` line.
Creates .bak backups before modifying files.

Run: py scripts/fix_try_block_indent2.py
"""
from __future__ import annotations
from pathlib import Path
import re


def fix_file(path: Path) -> int:
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines()
    changed = False
    i = 0
    out = []
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]*)(try:\s*)(#.*)?$", line)
        if m:
            indent = m.group("indent")
            out.append(line)
            j = i + 1
            # collect block until an except/finally at same indent or until EOF
            while j < len(lines):
                ln = lines[j]
                # stop if line is except/finally at same indent
                if re.match(rf"^{re.escape(indent)}(except\b|finally\b)", ln):
                    break
                # if blank line, keep as is
                if ln.strip() == "":
                    out.append(ln)
                    j += 1
                    continue
                # if line starts with same indent or less, and is not further indented, indent it
                if re.match(rf"^{re.escape(indent)}\S", ln):
                    out.append(indent + "    " + ln[len(indent) :])
                    changed = True
                else:
                    out.append(ln)
                j += 1
            i = j
            continue
        out.append(line)
        i += 1
    if changed:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
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
            print(f"Fixed try-block indent in {p}")
            total += n
    print(f"Done. Files modified: {total}")


if __name__ == "__main__":
    main()
