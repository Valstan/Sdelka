#!/usr/bin/env python3
"""
Simple script to replace occurrences of:

    except Exception as exc:`n        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

with a logged form:

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

The script makes a *.bak copy of each changed file. Run locally and review diffs before committing.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


PATTERN = re.compile(r"except\s+Exception\s*:\n(\s*)pass\b", flags=re.M)


def files_to_fix(root: Path, exts: Iterable[str] = (".py",)) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        # skip venv and .git
        if any(part in ("venv", ".venv", ".git") for part in p.parts):
            continue
        yield p


def fix_file(path: Path) -> int:
    txt = path.read_text(encoding="utf-8")
    new_txt, n = PATTERN.subn(
        lambda m: f'except Exception as exc:\n{m.group(1)}logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)',
        txt,
    )
    if n > 0:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)
        path.write_text(new_txt, encoding="utf-8")
    return n


def main() -> None:
    root = Path(".")
    total = 0
    for p in files_to_fix(root):
        n = fix_file(p)
        if n:
            print(f"patched {p} -> {n} replacements")
            total += n
    print(f"Done. Total replacements: {total}")


if __name__ == "__main__":
    main()
