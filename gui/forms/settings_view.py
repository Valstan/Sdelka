from __future__ import annotations

import shutil
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import threading
import subprocess
import sys

from config.settings import CONFIG
from services.merge_db import merge_from_file
from utils.text import sanitize_filename
from utils.user_prefs import load_prefs, save_prefs, UserPrefs


class SettingsView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._prefs = load_prefs()
        self._build_log_win: ctk.CTkToplevel | None = None
        self._build_log_text = None
        self._build_progress_label: ctk.CTkLabel | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(box, text="Резервное копирование и перенос базы данных").pack(anchor="w", pady=(0, 8))

        btns = ctk.CTkFrame(box)
        btns.pack(fill="x")

        ctk.CTkButton(btns, text="Сохранить копию базы...", command=self._export_db).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Слить с другой базой...", command=self._merge_db).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Собрать .exe...", command=self._build_exe).pack(side="left", padx=6)

        # UI Preferences
        ui_box = ctk.CTkFrame(self)
        ui_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ui_box, text="Настройки интерфейса").pack(anchor="w", pady=(0, 8))
        row = ctk.CTkFrame(ui_box)
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Размер шрифта списков").pack(side="left", padx=6)
        self._list_font_var = ctk.StringVar(value=str(self._prefs.list_font_size))
        ctk.CTkOptionMenu(row, values=[str(i) for i in range(10, 21)], variable=self._list_font_var, command=lambda _: self._save_prefs()).pack(side="left")
        ctk.CTkLabel(row, text="Размер шрифта кнопок/надписей").pack(side="left", padx=(16, 6))
        self._ui_font_var = ctk.StringVar(value=str(self._prefs.ui_font_size))
        ctk.CTkOptionMenu(row, values=[str(i) for i in range(10, 21)], variable=self._ui_font_var, command=lambda _: self._save_prefs()).pack(side="left")

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(fill="x", padx=10, pady=10)

    def _save_prefs(self) -> None:
        try:
            prefs = UserPrefs(list_font_size=int(self._list_font_var.get()), ui_font_size=int(self._ui_font_var.get()))
            save_prefs(prefs)
            self.status.configure(text="Настройки интерфейса сохранены. Перезапустите программу для полного применения.")
        except Exception as exc:
            self.status.configure(text=f"Ошибка сохранения настроек: {exc}")

    def _export_db(self) -> None:
        src = Path(CONFIG.db_path)
        if not src.exists():
            messagebox.showerror("Экспорт", "Файл базы данных не найден")
            return
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        initial = f"{src.stem}_backup_{stamp}.db"
        dest = filedialog.asksaveasfilename(
            title="Сохранить копию базы",
            defaultextension=".db",
            initialfile=initial,
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not dest:
            return
        try:
            shutil.copy2(src, dest)
        except Exception as exc:
            messagebox.showerror("Экспорт", f"Не удалось сохранить копию: {exc}")
            return
        messagebox.showinfo("Экспорт", "Копия базы успешно сохранена")

    def _merge_db(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите файл базы для слияния",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            refs, orders = merge_from_file(CONFIG.db_path, path)
        except Exception as exc:
            messagebox.showerror("Слияние", f"Не удалось выполнить слияние: {exc}")
            return
        messagebox.showinfo("Слияние", f"Готово. Обновлено справочников: {refs}, добавлено нарядов: {orders}")

    # ---- Build EXE ----
    def _build_exe(self) -> None:
        if sys.platform != "win32":
            messagebox.showwarning("Сборка .exe", "Сборка .exe доступна только в Windows.")
            return
        # Выбор имени/места сохранения заранее
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        initial = sanitize_filename(f"sdelka_{stamp}") + ".exe"
        target_path = filedialog.asksaveasfilename(
            title="Сохранить собранный .exe",
            defaultextension=".exe",
            initialfile=initial,
            filetypes=[("Windows Executable", "*.exe"), ("Все файлы", "*.*")],
        )
        if not target_path:
            return
        self.status.configure(text="Сборка .exe запущена, подождите...")
        self._open_build_log_window()
        threading.Thread(target=self._build_exe_worker, args=(target_path,), daemon=True).start()

    def _build_exe_worker(self, target_path: str) -> None:
        try:
            root_dir = Path(__file__).resolve().parents[2]  # проектный корень
            entry = root_dir / "main.py"
            if not entry.exists():
                raise FileNotFoundError(f"Не найден main.py по пути {entry}")

            # Обеспечить наличие pyinstaller
            try:
                import PyInstaller  # noqa: F401
            except Exception:
                pip_cmd = [sys.executable, "-m", "pip", "install", "pyinstaller"]
                rc = self._run_and_stream(pip_cmd, root_dir, title="Установка PyInstaller")
                if rc != 0:
                    raise RuntimeError("Не удалось установить pyinstaller, см. лог выше")

            name = "Sdelka"
            build_cmd = [
                sys.executable, "-m", "PyInstaller",
                "--noconfirm", "--clean",
                "--name", name,
                "--onefile", "--windowed",
                "--collect-all", "tkcalendar",
                "--collect-all", "customtkinter",
                str(entry),
            ]
            rc = self._run_and_stream(build_cmd, root_dir, title="Сборка приложения")
            if rc != 0:
                raise RuntimeError("Ошибка сборки, см. лог выше")

            dist_exe = root_dir / "dist" / f"{name}.exe"
            if not dist_exe.exists():
                raise FileNotFoundError(f"Собранный файл не найден: {dist_exe}")

            # Копируем в выбранное место
            shutil.copy2(dist_exe, target_path)
            # Можно убрать временные артефакты (build, spec)
            try:
                (root_dir / f"{name}.spec").unlink(missing_ok=True)
                shutil.rmtree(root_dir / "build", ignore_errors=True)
                # dist оставим, чтобы не пересобирать заново, если надо
            except Exception:
                pass
        except Exception as exc:
            self.after(0, lambda: self.status.configure(text=""))
            self.after(0, lambda: messagebox.showerror("Сборка .exe", str(exc)))
            self.after(0, lambda: self._append_build_log("\n[ОШИБКА] " + str(exc) + "\n"))
            return
        self.after(0, lambda: self.status.configure(text="Готово: .exe сохранён."))
        self.after(0, lambda: self._append_build_log("\n[ГОТОВО] Файл успешно собран и сохранён.\n"))
        self.after(0, lambda: messagebox.showinfo("Сборка .exe", "Сборка завершена и файл сохранён."))

    # ----- Build log window helpers -----
    def _open_build_log_window(self) -> None:
        if self._build_log_win is not None and tk.Toplevel.winfo_exists(self._build_log_win):
            # Уже открыто — просто очистим/поднимем
            try:
                self._build_log_text.configure(state="normal")
                self._build_log_text.delete("1.0", "end")
                self._build_log_text.configure(state="disabled")
            except Exception:
                pass
            self._build_log_win.lift()
            return
        win = ctk.CTkToplevel(self)
        win.title("Сборка .exe — журнал")
        win.geometry("820x420")
        win.attributes("-topmost", True)
        self._build_log_win = win

        self._build_progress_label = ctk.CTkLabel(win, text="Начало...")
        self._build_progress_label.pack(fill="x", padx=8, pady=(8, 4))

        # Текст с прокруткой
        try:
            text = ctk.CTkTextbox(win)
            text.pack(expand=True, fill="both", padx=8, pady=8)
        except Exception:
            frame = ctk.CTkFrame(win)
            frame.pack(expand=True, fill="both", padx=8, pady=8)
            sb = tk.Scrollbar(frame)
            sb.pack(side="right", fill="y")
            text = tk.Text(frame, yscrollcommand=sb.set)
            text.pack(expand=True, fill="both")
            sb.config(command=text.yview)
        self._build_log_text = text
        try:
            self._build_log_text.configure(state="disabled")
        except Exception:
            pass

        ctk.CTkButton(win, text="Закрыть", command=win.destroy).pack(pady=(0, 8))

    def _append_build_log(self, line: str) -> None:
        if not self._build_log_win or not tk.Toplevel.winfo_exists(self._build_log_win):
            return
        def _do():
            try:
                self._build_log_text.configure(state="normal")
            except Exception:
                pass
            try:
                self._build_log_text.insert("end", line)
                self._build_log_text.see("end")
            finally:
                try:
                    self._build_log_text.configure(state="disabled")
                except Exception:
                    pass
        self.after(0, _do)

    def _set_progress(self, text: str) -> None:
        if not self._build_progress_label:
            return
        self.after(0, lambda: self._build_progress_label.configure(text=text))

    def _run_and_stream(self, cmd: list[str], cwd: Path, title: str) -> int:
        self._append_build_log(f"\n=== {title} ===\n$ {' '.join(cmd)}\n")
        self._set_progress(title)
        try:
            proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except Exception as exc:
            self._append_build_log(f"[ОШИБКА ЗАПУСКА] {exc}\n")
            return -1
        assert proc.stdout is not None
        for line in proc.stdout:
            self._append_build_log(line)
        rc = proc.wait()
        self._append_build_log(f"\n[ЗАВЕРШЕНО] Код выхода: {rc}\n")
        return rc