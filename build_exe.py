from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import argparse
import os
import importlib

def _data_arg(src: Path, dst: str) -> list[str]:
    sep = ';' if os.name == 'nt' else ':'
    return ["--add-data", f"{str(src)}{sep}{dst}"]


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # type: ignore  # noqa: F401
        return
    except Exception:
        pass
    print("Installing PyInstaller...")
    rc = subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"]) 
    if rc != 0:
        raise SystemExit("Failed to install pyinstaller")


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    entry = root_dir / "main.py"
    if not entry.exists():
        raise SystemExit(f"main.py not found at {entry}")

    parser = argparse.ArgumentParser(description="Build Sdelka executable with PyInstaller")
    parser.add_argument("--name", default=None, help="Executable name (default: Sdelka_RMZ_<version>)")
    parser.add_argument("--icon", default=None, help="Path to .ico icon (Windows)")
    parser.add_argument("--dist", default=str(root_dir / "dist"), help="Output dist directory")
    parser.add_argument("--onefile", action="store_true", help="Build as onefile (default)")
    parser.add_argument("--onedir", action="store_true", help="Build as onedir (for debugging)")
    args = parser.parse_args()

    # Determine versioned name
    try:
        from utils.versioning import get_version  # type: ignore
        ver = get_version()
    except Exception:
        ver = ""
    def _sanitize(n: str) -> str:
        n = n.replace(" ", "_")
        n = n.replace("/", "_").replace("\\", "_")
        return n
    ver_tag = ver.replace(".", "_") if ver else ""
    default_name = _sanitize(f"Sdelka_RMZ_{ver_tag}") if ver_tag else "Sdelka_RMZ"
    exe_name = args.name or default_name

    ensure_pyinstaller()

    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--log-level=DEBUG",
        "--name", exe_name,
        "--windowed",
        "--collect-all", "tkcalendar",
        "--collect-all", "customtkinter",
        str(entry),
    ]

    # onefile/onedir
    if args.onedir and not args.onefile:
        build_mode = "--onedir"
        is_onedir = True
    else:
        build_mode = "--onefile"
        is_onedir = False
    build_cmd.insert(6, build_mode)

    # icon if provided or default exists
    icon_path: Path | None = None
    if args.icon:
        ip = Path(args.icon)
        if ip.exists():
            icon_path = ip
    else:
        cand = root_dir / "assets" / "app.ico"
        if cand.exists():
            icon_path = cand
    if icon_path is not None and os.name == 'nt':
        build_cmd.extend(["--icon", str(icon_path)])

    # bundle optional assets folders if present
    for folder, dst in [(root_dir / "assets", "assets"), (root_dir / "resources", "resources")]:
        if folder.exists():
            build_cmd.extend(_data_arg(folder, dst))

    # add hidden-imports / collect-all for optional modules if installed
    def _has(mod: str) -> bool:
        try:
            importlib.import_module(mod)
            return True
        except Exception:
            return False
    hidden = [
        "openpyxl", "xlrd", "xlsxwriter",
        "pdfplumber", "docx", "odf", "dbfread",
        "bs4", "lxml", "pandas",
    ]
    for mod in hidden:
        if _has(mod):
            # prefer collect-all where data files are important
            if mod in {"bs4", "lxml", "pandas", "odf", "dbfread", "pdfplumber", "docx"}:
                build_cmd.extend(["--collect-all", mod])
            else:
                build_cmd.extend(["--hidden-import", mod])

    # custom dist directory
    if args.dist:
        build_cmd.extend(["--distpath", str(Path(args.dist))])

    print("Running:", " ".join(build_cmd))
    rc = subprocess.call(build_cmd, cwd=str(root_dir))
    if rc != 0:
        raise SystemExit("Build failed")

    dist_dir = Path(args.dist)
    # Expected paths
    candidate_top = dist_dir / f"{exe_name}.exe"
    candidate_nested = dist_dir / exe_name / f"{exe_name}.exe"
    if candidate_top.exists():
        print(f"Build complete: {candidate_top}")
        return
    if candidate_nested.exists():
        print(f"Build complete: {candidate_nested}")
        return
    # Fallback: search recursively for any exe with this name
    found = None
    try:
        for p in dist_dir.rglob("*.exe"):
            if p.name.lower() == f"{exe_name}.exe".lower():
                found = p
                break
    except Exception:
        pass
    if found is not None and found.exists():
        print(f"Build complete: {found}")
        return
    # Show what's available to help debugging
    try:
        print("Dist contents:")
        for p in dist_dir.rglob("*.exe"):
            print(" -", p)
    except Exception:
        pass
    raise SystemExit(f"Built exe not found: {dist_dir / (exe_name + '.exe')}")


if __name__ == "__main__":
    main()
