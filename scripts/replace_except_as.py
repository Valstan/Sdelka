#!/usr/bin/env python3
"""
Replace occurrences of bare 'except Exception:' with 'except Exception as exc:' across .py files.
Creates .bak backups. Skips lines that already contain ' as '.

Run locally: py scripts/replace_except_as.py
"""
from __future__ import annotations

from pathlib import Path


def files_to_fix(root: Path):
    for p in root.rglob("*.py"):
        if any(part in ("venv", ".venv", ".git") for part in p.parts):
            continue
        yield p


def fix_file(path: Path) -> int:
    changed = False
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("except Exception:") and " as " not in stripped:
            indent = line[: len(line) - len(stripped)]
            lines[i] = f"{indent}except Exception as exc:"
            changed = True
    if changed:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1
    return 0


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
            print(f"Patched {p}")
            total += n
    print(f"Done. Files patched: {total}")


if __name__ == "__main__":
    main()
