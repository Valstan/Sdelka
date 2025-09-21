from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


def run_build(name: str, icon: str | None, dist: str, mode_onedir: bool) -> int:
    root_dir = Path(__file__).resolve().parent
    entry = root_dir / "main.py"
    if not entry.exists():
        messagebox.showerror("Сборка", f"Не найден main.py: {entry}")
        return -1

    cmd = [sys.executable, "build_exe.py"]
    if name:
        cmd.extend(["--name", name])
    if icon:
        cmd.extend(["--icon", icon])
    if dist:
        cmd.extend(["--dist", dist])
    if mode_onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    try:
        proc = subprocess.Popen(cmd, cwd=str(root_dir))
        return proc.wait()
    except Exception as exc:
        messagebox.showerror("Сборка", str(exc))
        return -1


class BuildApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Сборка Sdelka.exe")
        self.geometry("520x260")
        self.resizable(False, False)

        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, **pad)

        # Name
        ttk.Label(frm, text="Имя exe:").grid(row=0, column=0, sticky="w")
        self.var_name = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_name, width=40).grid(
            row=0, column=1, sticky="we"
        )

        # Icon
        ttk.Label(frm, text="Иконка (.ico):").grid(row=1, column=0, sticky="w")
        self.var_icon = tk.StringVar()
        row1 = ttk.Frame(frm)
        row1.grid(row=1, column=1, sticky="we")
        ttk.Entry(row1, textvariable=self.var_icon, width=34).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(row1, text="...", width=3, command=self._pick_icon).pack(
            side="left", padx=(4, 0)
        )

        # Dist
        ttk.Label(frm, text="Папка вывода:").grid(row=2, column=0, sticky="w")
        self.var_dist = tk.StringVar(
            value=str(Path(__file__).resolve().parent / "dist")
        )
        row2 = ttk.Frame(frm)
        row2.grid(row=2, column=1, sticky="we")
        ttk.Entry(row2, textvariable=self.var_dist, width=34).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(row2, text="...", width=3, command=self._pick_dist).pack(
            side="left", padx=(4, 0)
        )

        # Mode
        self.mode_onedir = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frm, text="Собирать в папку (onedir)", variable=self.mode_onedir
        ).grid(row=3, column=1, sticky="w")

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=4, column=1, sticky="e")
        ttk.Button(btns, text="Собрать", command=self._build).pack(side="left", padx=6)
        ttk.Button(btns, text="Выход", command=self.destroy).pack(side="left")

        frm.columnconfigure(1, weight=1)

    def _pick_icon(self) -> None:
        p = filedialog.askopenfilename(
            title="Выберите .ico", filetypes=[["ICO", "*.ico"], ["Все файлы", "*.*"]]
        )
        if p:
            self.var_icon.set(p)

    def _pick_dist(self) -> None:
        d = filedialog.askdirectory(title="Выберите папку вывода")
        if d:
            self.var_dist.set(d)

    def _build(self) -> None:
        name = self.var_name.get().strip()
        icon = self.var_icon.get().strip() or None
        dist = self.var_dist.get().strip()
        onedir = bool(self.mode_onedir.get())
        if dist and not Path(dist).exists():
            try:
                Path(dist).mkdir(parents=True, exist_ok=True)
            except Exception:
                messagebox.showerror("Сборка", f"Не удалось создать папку: {dist}")
                return
        self.withdraw()
        rc = run_build(name=name, icon=icon, dist=dist, mode_onedir=onedir)
        self.deiconify()
        if rc == 0:
            messagebox.showinfo("Сборка", "Готово.")
        else:
            # Попробуем показать tail из pyinstaller лога, если он доступен
            log_path = Path(__file__).resolve().parent / "build" / "warn-create.txt"
            if log_path.exists():
                try:
                    tail = log_path.read_text(encoding="utf-8", errors="ignore")[-1000:]
                except Exception:
                    tail = ""
            else:
                tail = ""
            msg = f"Ошибка (код {rc}). См. вывод консоли."
            if tail:
                msg += "\n\nПоследние строки лога:\n" + tail
            messagebox.showerror("Сборка", msg)


if __name__ == "__main__":
    app = BuildApp()
    app.mainloop()
