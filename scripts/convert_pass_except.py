#!/usr/bin/env python3
"""
Convert occurrences of `except ...: pass` or
``except ...:\n    pass`` to a logged form that preserves indentation.

It will create a .bak backup of modified files.

Run: py scripts/convert_pass_except.py
"""
from __future__ import annotations

import re
from pathlib import Path


PAT_SINGLE = re.compile(r"(^[ \t]*except\s+[^:\n]+:\s*)pass\s*$", flags=re.M)
PAT_MULTI = re.compile(r"(^[ \t]*except\s+[^:\n]+:\s*\n)([ \t]*)pass\b", flags=re.M)


def files_to_fix(root: Path):
    for p in root.rglob("*.py"):
        if any(part in ("venv", ".venv", ".git") for part in p.parts):
            continue
        yield p


def replace_in_text(text: str) -> tuple[str, int]:
    count = 0

    def single_repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        prefix = m.group(1)
        indent = " " * 4 if prefix.count("\t") == 0 else "\t"
        return f'{prefix}import logging\n{prefix}logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)'

    def multi_repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        header = m.group(1)
        indent = m.group(2)
        # transform 'except X:' -> 'except X as exc:'
        header_new = re.sub(
            r"except(\s+[^:]+):",
            lambda mm: mm.group(0).replace(":", " as exc:"),
            header,
        )
        return f'{header_new}{indent}import logging\n{indent}logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)'

    # First handle multi-line patterns where 'pass' is on next line
    new_text, n1 = PAT_MULTI.subn(multi_repl, text)
    # Then handle single-line 'except ...: pass'
    new_text, n2 = PAT_SINGLE.subn(
        lambda m: m.group(1).rstrip()
        + " as exc:\n"
        + m.group(1).lstrip().replace("except", "").rstrip()
        + "import logging\n"
        + m.group(1).lstrip().replace("except", "").rstrip(),
        new_text,
    )

    # The above single-line replacement is tricky; instead do another approach
    # Re-run single-line replacement more carefully
    def single_repl2(m: re.Match) -> str:
        nonlocal count
        count += 1
        prefix = m.group(1)
        # prefix contains 'except X: '
        header = prefix.rstrip()
        header_new = header[:-1] + " as exc:"  # replace trailing ':' with ' as exc:'
        # compute indent for following lines
        indent = " " * (len(prefix) - len(prefix.lstrip())) + "    "
        return f'{header_new}\n{indent}import logging\n{indent}logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)'

    new_text, n3 = PAT_SINGLE.subn(single_repl2, new_text)
    return new_text, count


def fix_file(path: Path) -> int:
    txt = path.read_text(encoding="utf-8")
    new_txt, cnt = replace_in_text(txt)
    if cnt > 0:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)
        path.write_text(new_txt, encoding="utf-8")
    return cnt


def main() -> None:
    total = 0
    for p in files_to_fix(Path(".")):
        try:
            n = fix_file(p)
        except Exception as exc:
            print(f"Failed {p}: {exc}")
            continue
        if n:
            print(f"Patched {p}: {n}")
            total += n
    print(f"Done. Total patched: {total}")


if __name__ == "__main__":
    main()
