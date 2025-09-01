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
from utils.user_prefs import (
    load_prefs,
    save_prefs,
    UserPrefs,
    get_current_db_path,
    set_db_path,
    get_enable_wal,
    set_enable_wal,
    get_busy_timeout_ms,
    set_busy_timeout_ms,
)
from utils.ui_theming import apply_user_fonts
from db.sqlite import get_connection
from utils.versioning import get_version


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
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

        self._btn_export_db = ctk.CTkButton(btns, text="Сохранить копию базы...", command=self._export_db)
        self._btn_export_db.pack(side="left", padx=6)
        self._btn_merge_db = ctk.CTkButton(btns, text="Слить с другой базой...", command=self._merge_db)
        self._btn_merge_db.pack(side="left", padx=6)
        self._btn_build_exe = ctk.CTkButton(btns, text="Собрать .exe...", command=self._build_exe)
        self._btn_build_exe.pack(side="left", padx=6)
        self._btn_changelog = ctk.CTkButton(btns, text="Версии программы", command=self._show_changelog)
        self._btn_changelog.pack(side="left", padx=6)

        # ---- Настройки базы данных и совместной работы ----
        db_box = ctk.CTkFrame(self)
        db_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(db_box, text="Настройки базы данных (для совместной работы)").pack(anchor="w", pady=(0, 8))

        # Путь к БД
        row_db = ctk.CTkFrame(db_box)
        row_db.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(row_db, text="Путь к файлу БД (.db)").pack(side="left", padx=6)
        self._db_path_var = ctk.StringVar(value=str(get_current_db_path()))
        self._db_path_entry = ctk.CTkEntry(row_db, textvariable=self._db_path_var, width=560)
        self._db_path_entry.pack(side="left", padx=6, fill="x", expand=True)
        ctk.CTkButton(row_db, text="Выбрать...", command=self._choose_existing_db).pack(side="left", padx=6)
        ctk.CTkButton(row_db, text="Создать...", command=self._create_new_db).pack(side="left", padx=6)
        ctk.CTkButton(row_db, text="Применить", command=self._apply_db_settings).pack(side="left", padx=6)
        ctk.CTkButton(row_db, text="Проверить подключение", command=self._test_db_connection).pack(side="left", padx=6)

        # WAL и таймауты
        row_wal = ctk.CTkFrame(db_box)
        row_wal.pack(fill="x", pady=(2, 6))
        self._wal_var = ctk.BooleanVar(value=get_enable_wal())
        self._wal_chk = ctk.CTkCheckBox(row_wal, text="Включить WAL (рекомендуется для совместной работы)", variable=self._wal_var, command=lambda: None)
        self._wal_chk.pack(side="left", padx=6)

        row_to = ctk.CTkFrame(db_box)
        row_to.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(row_to, text="Таймаут ожидания блокировок (мс)").pack(side="left", padx=6)
        self._busy_var = ctk.StringVar(value=str(get_busy_timeout_ms()))
        self._busy_entry = ctk.CTkEntry(row_to, textvariable=self._busy_var, width=120)
        self._busy_entry.pack(side="left", padx=6)
        ctk.CTkButton(row_to, text="Сохранить", command=self._apply_db_settings).pack(side="left", padx=6)

        # UI Preferences
        ui_box = ctk.CTkFrame(self)
        ui_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ui_box, text="Настройки интерфейса").pack(anchor="w", pady=(0, 8))
        row = ctk.CTkFrame(ui_box)
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Размер шрифта списков").pack(side="left", padx=6)
        self._list_font_var = ctk.StringVar(value=str(self._prefs.list_font_size))
        self._opt_list_font = ctk.CTkOptionMenu(row, values=[str(i) for i in range(10, 21)], variable=self._list_font_var, command=lambda _: self._save_prefs())
        self._opt_list_font.pack(side="left")
        ctk.CTkLabel(row, text="Размер шрифта кнопок/надписей").pack(side="left", padx=(16, 6))
        self._ui_font_var = ctk.StringVar(value=str(self._prefs.ui_font_size))
        self._opt_ui_font = ctk.CTkOptionMenu(row, values=[str(i) for i in range(10, 21)], variable=self._ui_font_var, command=lambda _: self._save_prefs())
        self._opt_ui_font.pack(side="left")

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(fill="x", padx=10, pady=10)

        # --- Импорт / Экспорт ---
        io_box = ctk.CTkFrame(self)
        io_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(io_box, text="Импорт данных").pack(anchor="w")
        row1 = ctk.CTkFrame(io_box)
        row1.pack(fill="x", pady=(4, 8))
        self._btn_import_unified = ctk.CTkButton(row1, text="Импорт данных", command=self._import_unified)
        self._btn_import_unified.pack(side="left", padx=5)

        ctk.CTkLabel(io_box, text="Экспорт таблиц").pack(anchor="w")
        row2 = ctk.CTkFrame(io_box)
        row2.pack(fill="x", pady=(4, 8))
        self._btn_exp_workers = ctk.CTkButton(row2, text="Экспорт Работников", command=lambda: self._export_table("workers"))
        self._btn_exp_workers.pack(side="left", padx=5)
        self._btn_exp_jobs = ctk.CTkButton(row2, text="Экспорт Видов работ", command=lambda: self._export_table("job_types"))
        self._btn_exp_jobs.pack(side="left", padx=5)
        self._btn_exp_products = ctk.CTkButton(row2, text="Экспорт Изделий", command=lambda: self._export_table("products"))
        self._btn_exp_products.pack(side="left", padx=5)
        self._btn_exp_contracts = ctk.CTkButton(row2, text="Экспорт Контрактов", command=lambda: self._export_table("contracts"))
        self._btn_exp_contracts.pack(side="left", padx=5)
        self._btn_exp_contracts_csv = ctk.CTkButton(row2, text="Экспорт CSV Контрактов", command=self._export_contracts_csv)
        self._btn_exp_contracts_csv.pack(side="left", padx=5)
        self._btn_exp_all = ctk.CTkButton(row2, text="Экспорт всего набора", command=self._export_all)
        self._btn_exp_all.pack(side="left", padx=5)

        ctk.CTkLabel(io_box, text="Шаблоны Excel").pack(anchor="w")
        row3 = ctk.CTkFrame(io_box)
        row3.pack(fill="x", pady=(4, 8))
        self._btn_tpl_workers = ctk.CTkButton(row3, text="Шаблон Работники", command=lambda: self._save_template("workers"))
        self._btn_tpl_workers.pack(side="left", padx=5)
        self._btn_tpl_jobs = ctk.CTkButton(row3, text="Шаблон Виды работ", command=lambda: self._save_template("job_types"))
        self._btn_tpl_jobs.pack(side="left", padx=5)
        self._btn_tpl_products = ctk.CTkButton(row3, text="Шаблон Изделия", command=lambda: self._save_template("products"))
        self._btn_tpl_products.pack(side="left", padx=5)
        self._btn_tpl_contracts = ctk.CTkButton(row3, text="Шаблон Контракты", command=lambda: self._save_template("contracts"))
        self._btn_tpl_contracts.pack(side="left", padx=5)
        self._btn_tpl_contracts_csv = ctk.CTkButton(row3, text="Шаблон CSV Контрактов", command=self._save_contracts_csv_template)
        self._btn_tpl_contracts_csv.pack(side="left", padx=5)

        # Применить ограничения режима только просмотра
        if self._readonly:
            # Запретить изменяющие БД и системные действия
            for b in (
                self._btn_merge_db,
                self._btn_build_exe,
                self._btn_changelog,
                self._db_path_entry,
                self._btn_import_unified,
                self._opt_list_font,
                self._opt_ui_font,
            ):
                try:
                    b.configure(state="disabled")
                except Exception:
                    pass

    def _save_prefs(self) -> None:
        try:
            prefs = UserPrefs(list_font_size=int(self._list_font_var.get()), ui_font_size=int(self._ui_font_var.get()))
            save_prefs(prefs)
            # Применить на лету
            try:
                root = self.winfo_toplevel()
                apply_user_fonts(root, prefs)
                self.status.configure(text="Настройки интерфейса применены и сохранены.")
            except Exception:
                self.status.configure(text="Настройки сохранены. Перезапуск может потребоваться для полного применения.")
        except Exception as exc:
            self.status.configure(text=f"Ошибка сохранения настроек: {exc}")

    def _choose_existing_db(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        if not p.exists():
            messagebox.showerror("База данных", "Файл не найден")
            return
        self._db_path_var.set(str(p))
        set_db_path(p)
        self.status.configure(text="Путь к существующей БД применён. Перезапустите приложение.")

    def _create_new_db(self) -> None:
        initial_name = "app.db"
        cur = Path(get_current_db_path())
        try:
            if cur.parent.exists():
                initial_name = cur.name
        except Exception:
            pass
        path = filedialog.asksaveasfilename(
            title="Создать новую базу данных",
            defaultextension=".db",
            initialfile=initial_name,
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            set_db_path(p)
            with get_connection(p) as conn:
                from db.schema import initialize_schema
                initialize_schema(conn)
            self._db_path_var.set(str(p))
            self.status.configure(text="Новая база создана и путь сохранён. Перезапустите приложение.")
        except Exception as exc:
            messagebox.showerror("Создание БД", f"Не удалось создать БД: {exc}")

    def _apply_db_settings(self) -> None:
        try:
            # Сохранить путь
            new_path = Path(self._db_path_var.get().strip())
            if not new_path:
                raise ValueError("Путь к базе не указан")

            # Если путь существует — просто используем его, ничего не копируем и не сливаем
            if new_path.exists():
                set_db_path(new_path)
            else:
                # Предложить создать новую БД
                from tkinter import messagebox
                if not messagebox.askyesno("База данных", f"Файл не найден:\n{new_path}\n\nСоздать новую базу по этому пути?"):
                    self.status.configure(text="Создание отменено. Путь к БД не изменён.")
                    return
                try:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                set_db_path(new_path)
                # Создаём пустую БД с нужной схемой
                from db.sqlite import get_connection
                from db.schema import initialize_schema
                with get_connection(new_path) as conn:
                    initialize_schema(conn)

            # Сохранить WAL и таймаут (влияют на будущие подключения)
            set_enable_wal(bool(self._wal_var.get()))
            try:
                to_ms = int(self._busy_var.get())
                if to_ms < 1000:
                    to_ms = 1000
            except Exception:
                to_ms = 10000
            set_busy_timeout_ms(to_ms)

            self.status.configure(text="Путь к БД применён. Перезапустите приложение, чтобы все окна использовали новую БД.")
        except Exception as exc:
            self.status.configure(text=f"Ошибка применения настроек БД: {exc}")

    def _test_db_connection(self) -> None:
        try:
            p = Path(self._db_path_var.get().strip())
            with get_connection(p if p else None) as conn:
                conn.execute("SELECT 1")
            messagebox.showinfo("База данных", "Подключение успешно")
        except Exception as exc:
            messagebox.showerror("База данных", f"Не удалось подключиться: {exc}")

    def _export_db(self) -> None:
        src = Path(get_current_db_path())
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
        from utils.user_prefs import get_current_db_path
        try:
            refs, orders = merge_from_file(get_current_db_path(), path)
        except Exception as exc:
            messagebox.showerror("Слияние", f"Не удалось выполнить слияние: {exc}")
            return
        messagebox.showinfo("Слияние", f"Готово. Обновлено справочников: {refs}, добавлено нарядов: {orders}")

    # ---- Import/Export/Template handlers ----
    def _ask_open(self, title: str | None = None, default_ext: str | None = None, filter_name: str | None = None, patterns: str | None = None) -> str | None:
        title = title or "Выберите файл"
        filetypes = []
        if filter_name:
            pat = patterns or (f"*{default_ext}" if default_ext else "*.xlsx;*.xls;*.ods")
            filetypes = [(filter_name, pat)]
        else:
            filetypes = [("Книги", "*.xlsx;*.xls;*.ods"), ("Все файлы", "*.*")]
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

    def _ask_save(self, title: str, default_ext: str, filter_name: str, initialfile: str | None = None) -> str | None:
        return filedialog.asksaveasfilename(title=title, defaultextension=default_ext, initialfile=initialfile or "", filetypes=[(filter_name, f"*{default_ext}")])

    def _import_unified(self) -> None:
        if self._readonly:
            messagebox.showwarning("Импорт", "Режим только для чтения — импорт недоступен")
            return
        from import_engine import import_data
        path = filedialog.askopenfilename(
            title="Выберите файл для импорта",
            filetypes=[
                ("Поддерживаемые", "*.txt;*.csv;*.xls;*.xlsx;*.ods;*.docx;*.odt;*.html;*.xml;*.pdf;*.dbf;*.json"),
                ("Все файлы", "*.*"),
            ],
        )
        if not path:
            return
        # Диалог dry-run/настройки
        dry = tk.BooleanVar(value=True)
        preset = tk.StringVar(value="Авто")

        dlg = ctk.CTkToplevel(self)
        dlg.title("Импорт данных — параметры")
        ctk.CTkLabel(dlg, text="Режим").pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkCheckBox(dlg, text="Черновой прогон (без записи в БД)", variable=dry).pack(anchor="w", padx=12)
        ctk.CTkLabel(dlg, text="Профиль").pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkOptionMenu(dlg, values=["Авто", "Наряды", "Цена-лист", "Справочники"], variable=preset).pack(anchor="w", padx=12)
        ctk.CTkLabel(dlg, text="Подсказка: Авто — определить автоматически; Наряды — импорт нарядов; Цена-лист — виды работ с ценами; Справочники — работники/изделия/контракты.").pack(anchor="w", padx=12, pady=(6, 0))

        btns = ctk.CTkFrame(dlg)
        btns.pack(fill="x", padx=10, pady=10)
        done = tk.BooleanVar(value=False)

        def _ok():
            done.set(True)
            dlg.destroy()

        ctk.CTkButton(btns, text="OK", command=_ok).pack(side="right", padx=6)
        ctk.CTkButton(btns, text="Отмена", command=dlg.destroy).pack(side="right", padx=6)
        dlg.transient(self)
        dlg.grab_set()
        self.wait_window(dlg)
        if not done.get():
            return

        # Окно прогресса
        win = ctk.CTkToplevel(self)
        win.title("Импорт данных")
        win.geometry("480x160")
        ctk.CTkLabel(win, text="Выполняется импорт...").pack(anchor="w", padx=10, pady=(10, 6))
        pb = ctk.CTkProgressBar(win)
        pb.pack(fill="x", padx=10)
        pb.set(0)
        note_var = tk.StringVar(value="")
        ctk.CTkLabel(win, textvariable=note_var).pack(anchor="w", padx=10, pady=(6, 10))

        def progress_cb(step: int, total: int, note: str):
            # Обновляем UI из главного потока через after, безопасно для Tk
            def _do():
                try:
                    # окно могло быть закрыто
                    if not tk.Toplevel.winfo_exists(win):
                        return
                    pb.set(step / max(total, 1))
                    note_var.set(note)
                except Exception:
                    pass
            try:
                self.after(0, _do)
            except Exception:
                pass

        def run():
            import os
            try:
                preset_code = {"Авто": "auto", "Наряды": "orders", "Цена-лист": "price", "Справочники": "refs"}.get(preset.get(), "auto")
                res = import_data(path, dry_run=bool(dry.get()), preset=preset_code, progress_cb=progress_cb, backup_before=True)
                report_path = getattr(res, "details_html", None)
                def _show_success():
                    try:
                        if report_path:
                            if os.name == "nt":
                                try:
                                    os.startfile(report_path)  # type: ignore[attr-defined]
                                except Exception:
                                    pass
                            messagebox.showinfo("Импорт (черновой)", f"Готово. Отчёт: {report_path}")
                        else:
                            messagebox.showinfo("Импорт", "Готово.")
                    except Exception:
                        pass
                try:
                    self.after(0, _show_success)
                except Exception:
                    pass
            except Exception as e:
                def _show_err():
                    try:
                        messagebox.showerror("Импорт", str(e))
                    except Exception:
                        pass
                try:
                    self.after(0, _show_err)
                except Exception:
                    pass
            finally:
                def _close():
                    try:
                        if tk.Toplevel.winfo_exists(win):
                            win.destroy()
                    except Exception:
                        pass
                try:
                    self.after(0, _close)
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    def _export_table(self, table: str) -> None:
        from import_export.excel_io import export_table_to_excel
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_rus = {
            "workers": "работники",
            "job_types": "виды_работ",
            "products": "изделия",
            "contracts": "контракты",
        }.get(table, table)
        initial = sanitize_filename(f"экспорт_{table_rus}_{stamp}") + ".xlsx"
        path = self._ask_save(f"Сохранить {table_rus}", ".xlsx", "Excel", initialfile=initial)
        if not path:
            return
        try:
            with get_connection() as conn:
                export_table_to_excel(conn, table, path)
            messagebox.showinfo("Экспорт", "Готово")
        except Exception as exc:
            messagebox.showerror("Экспорт", str(exc))

    def _export_all(self) -> None:
        from import_export.excel_io import export_all_tables_to_excel
        directory = filedialog.askdirectory(title="Выберите папку для экспорта")
        if not directory:
            return
        try:
            with get_connection() as conn:
                export_all_tables_to_excel(conn, directory)
            messagebox.showinfo("Экспорт", "Готово")
        except Exception as exc:
            messagebox.showerror("Экспорт", str(exc))

    def _save_template(self, kind: str) -> None:
        from import_export.excel_io import (
            generate_workers_template,
            generate_job_types_template,
            generate_products_template,
            generate_contracts_template,
        )
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        map_rus = {
            "workers": "работники",
            "job_types": "виды_работ",
            "products": "изделия",
            "contracts": "контракты",
        }
        initial = sanitize_filename(f"шаблон_{map_rus.get(kind, kind)}_{stamp}") + ".xlsx"
        path = self._ask_save(f"Шаблон {map_rus.get(kind, kind)}", ".xlsx", "Excel", initialfile=initial)
        if not path:
            return
        try:
            if kind == "workers":
                generate_workers_template(path)
            elif kind == "job_types":
                generate_job_types_template(path)
            elif kind == "products":
                generate_products_template(path)
            elif kind == "contracts":
                generate_contracts_template(path)
            messagebox.showinfo("Шаблон", "Шаблон сохранен")
        except Exception as exc:
            messagebox.showerror("Шаблон", str(exc))

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

    # ----- Changelog window -----
    def _show_changelog(self) -> None:
        """Отображает окно с историей изменений программы"""
        win = ctk.CTkToplevel(self)
        win.title("История изменений программы")
        win.geometry("800x600")
        win.attributes("-topmost", True)
        
        # Заголовок
        header = ctk.CTkFrame(win)
        header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header, text="История изменений программы", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        try:
            cur_ver = get_version()
        except Exception:
            cur_ver = "3.2"
        ctk.CTkLabel(header, text=f"СДЕЛКА РМЗ {cur_ver} — список изменений, исправлений и улучшений", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        
        # Основной контент с прокруткой
        content_frame = ctk.CTkFrame(win)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Создаем текстовый виджет с прокруткой
        try:
            text_widget = ctk.CTkTextbox(content_frame)
            text_widget.pack(expand=True, fill="both", padx=8, pady=8)
        except Exception:
            # Fallback для старых версий CustomTkinter
            frame = ctk.CTkFrame(content_frame)
            frame.pack(expand=True, fill="both", padx=8, pady=8)
            sb = tk.Scrollbar(frame)
            sb.pack(side="right", fill="y")
            text_widget = tk.Text(frame, yscrollcommand=sb.set, wrap="word", font=("Consolas", 10))
            text_widget.pack(expand=True, fill="both")
            sb.config(command=text_widget.yview)
        
        # Заполняем содержимое
        changelog_content = self._get_changelog_content()
        text_widget.insert("1.0", changelog_content)
        text_widget.configure(state="disabled")  # Только для чтения
        
        # Кнопка закрытия
        btn_frame = ctk.CTkFrame(win)
        btn_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkButton(btn_frame, text="Закрыть", command=win.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Копировать в буфер", command=lambda: self._copy_changelog_to_clipboard(changelog_content)).pack(side="right", padx=5)
    
    def _get_changelog_content(self) -> str:
        """Возвращает содержимое changelog в текстовом формате"""
        content = []
        content.append("ИСТОРИЯ ИЗМЕНЕНИЙ ПРОГРАММЫ")
        content.append("=" * 50)
        content.append("")
        
        # Версия 3.7 (текущая)
        content.append("ВЕРСИЯ 3.7 от 29 августа 2025 года")
        content.append("-" * 40)
        content.append("✨ НОВОЕ:")
        content.append("• Единый модуль импорта данных и одна кнопка ‘Импорт данных’")
        content.append("• Русские пресеты профилей: ‘Авто’, ‘Наряды’, ‘Цена-лист’, ‘Справочники’")
        content.append("• Черновой прогон (dry-run) с HTML-отчётом и автозапуском отчёта")
        content.append("• Автобэкап БД перед реальным импортом")
        content.append("")
        content.append("🔁 ИЗМЕНЕНО:")
        content.append("• Улучшено определение типа документов (контракты/изделия/наряды)")
        content.append("• Безопасное обновление прогресса импорта в UI")
        content.append("")
        
        # Версия 3.6 (текущая)
        content.append("ВЕРСИЯ 3.6 от 28 августа 2025 года")
        content.append("-" * 40)
        content.append("🔧 ИСПРАВЛЕНИЯ:")
        content.append("• Исправлена проблема с импортом изделий и контрактов из CSV")
        content.append("• Улучшен алгоритм парсинга оборотно-сальдовой ведомости")
        content.append("• Оптимизирована логика группировки данных по изделиям и контрактам")
        content.append("• Убраны отладочные сообщения для production-использования")
        content.append("")
        
        # Версия 3.5
        content.append("ВЕРСИЯ 3.5 от 28 августа 2025 года")
        content.append("-" * 40)
        content.append("✨ НОВЫЕ ВОЗМОЖНОСТИ:")
        content.append("• Новый модуль импорта изделий с привязкой к контрактам из CSV файлов")
        content.append("• Автоматический парсинг оборотно-сальдовой ведомости по счету 002")
        content.append("• Извлечение информации об изделиях (двигатели) и контрактах")
        content.append("• Автоматическое связывание изделий с соответствующими контрактами")
        content.append("• Создание системного контракта 'Без контракта' для изделий без привязки")
        content.append("• Поддержка прогресс-бара для длительных операций импорта")
        content.append("")
        
        # Версия 3.4
        content.append("ВЕРСИЯ 3.4 от 28 августа 2025 года")
        content.append("-" * 40)
        content.append("✨ НОВЫЕ ВОЗМОЖНОСТИ:")
        content.append("• Полная поддержка всех полей контрактов в интерфейсе справочника")
        content.append("• Новые поля контрактов: Наименование, Вид контракта, Исполнитель, ИГК, Номер контракта, Отдельный счет")
        content.append("• Расширенная таблица контрактов с отображением всех полей")
        content.append("• Улучшенная форма редактирования контрактов с 5 строками полей")
        content.append("")
        content.append("🔁 ИЗМЕНЕНО:")
        content.append("• Интерфейс справочника контрактов полностью переработан для отображения всех полей")
        content.append("• 'Отмена' всегда активна; очистка формы возвращает режим ввода")
        content.append("• Фильтры 'Вид работ' и 'Изделие' не ломают генерацию отчётов")
        content.append("• PDF: перенос длинных текстов, сжатие 'Вид работ', разбиение больших таблиц")
        content.append("")
        content.append("🔁 ИЗМЕНЕНО:")
        content.append("• Диалог выбора файла для импорта принимает форматы: .xlsx, .xls, .ods")
        content.append("")
        
        # Версия 3.0
        content.append("ВЕРСИЯ 3.0 от 18 августа 2025 года")
        content.append("-" * 40)
        content.append("✨ НОВЫЕ ВОЗМОЖНОСТИ:")
        content.append("• Новый формат версионирования '3 сетевая от [дата]'")
        content.append("• Русские названия месяцев в версии")
        content.append("• Автоматическое обновление даты при изменениях в коде")
        content.append("• Поддержка веток разработки (v2 стабильная, v3 основная)")
        content.append("")
        content.append("🔧 ИСПРАВЛЕНИЯ:")
        content.append("• КРИТИЧЕСКОЕ: Проблема с добавлением нескольких работников в наряды")
        content.append("  - Улучшена валидация работников в форме создания/редактирования нарядов")
        content.append("  - Добавлена автоматическая обработка дублирующихся ID работников")
        content.append("  - Улучшена обработка ошибок с подробным логированием")
        content.append("  - Добавлены проверки корректности ID работников")
        content.append("  - Исправлена ошибка 'Найдены некорректные работники в составе бригады'")
        content.append("")
        
        # Версия 2.9
        content.append("ВЕРСИЯ 2.9 - 2025 год")
        content.append("-" * 40)
        content.append("✨ НОВЫЕ ВОЗМОЖНОСТИ:")
        content.append("• Система ролей пользователей (Полный доступ / Только просмотр)")
        content.append("• Режим 'только чтение' с защитой на уровне БД")
        content.append("• Диалог выбора режима при запуске")
        content.append("• Настройки размера шрифта UI с живым применением")
        content.append("• Кнопка 'Печать' для отчетов")
        content.append("• Оптимизация PDF отчетов (авто-ориентация, умное масштабирование шрифтов)")
        content.append("• Нормализация заголовков колонок во всех отчетах")
        content.append("• Улучшенная компоновка в разделе 'Наряды'")
        content.append("• Перенос функционала 'Импорт/Экспорт' в 'Настройки'")
        content.append("• Кнопка 'Собрать .exe' с окном логов в реальном времени")
        content.append("• Система версионирования 2.Y.M.N на основе изменений файлов")
        content.append("• Автоматическое скрытие подсказок через 5 секунд")
        content.append("• Подсказки появляются сразу при фокусе на поле")
        content.append("• Точное позиционирование подсказок автодополнения")
        content.append("• История использования для автодополнения")
        content.append("• Календарь для выбора дат во всех полях")
        content.append("• Кнопки 'Отмена' во всех режимах редактирования")
        content.append("• Загрузка, редактирование и удаление существующих нарядов")
        content.append("• Раздел 'Отчеты' с фильтрами и экспортом (HTML, PDF, Excel)")
        content.append("• Импорт/экспорт Excel для справочных данных")
        content.append("• Поиск без учета регистра в базе данных")
        content.append("• Слияние баз данных")
        content.append("• Создание резервных копий БД")
        content.append("")
        content.append("🔧 ИСПРАВЛЕНИЯ:")
        content.append("• Проблемы с шрифтами в PDF (поддержка кириллицы)")
        content.append("• Переполнение текста в отчетах")
        content.append("• Позиционирование элементов интерфейса")
        content.append("• Валидация внешних ключей при создании нарядов")
        content.append("• Проблемы с календарем (блокировка интерфейса)")
        content.append("• Автоматическое скрытие подсказок")
        content.append("")
        
        # Версия 2.0
        content.append("ВЕРСИЯ 2.0 - 2025 год")
        content.append("-" * 40)
        content.append("✨ БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ:")
        content.append("• Учет сдельной работы бригад")
        content.append("• GUI на CustomTkinter")
        content.append("• SQLite база данных")
        content.append("• Система отчетов")
        content.append("• Экспорт в различные форматы")
        content.append("")
        
        content.append("=" * 50)
        content.append("Для получения подробной информации см. файл CHANGELOG.md")
        content.append("")
        
        return "\n".join(content)
    
    def _copy_changelog_to_clipboard(self, content: str) -> None:
        """Копирует содержимое changelog в буфер обмена"""
        try:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Копирование", "История изменений скопирована в буфер обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать в буфер обмена: {e}")

    def _import_contracts_csv(self) -> None:
        """Импорт контрактов из CSV файла"""
        try:
            from import_export.excel_io import import_contracts_from_csv
            path = filedialog.askopenfilename(
                title="Выберите CSV файл с контрактами",
                filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            )
            if not path:
                return
            with get_connection() as conn:
                imported, updated = import_contracts_from_csv(conn, path)
                self.status.configure(text=f"Импорт CSV контрактов завершен. Импортировано: {imported}, обновлено: {updated}")
        except Exception as e:
            self.status.configure(text=f"Ошибка импорта CSV контрактов: {e}")

    def _export_contracts_csv(self) -> None:
        """Экспорт контрактов в CSV файл"""
        try:
            from import_export.excel_io import export_contracts_to_csv
            path = filedialog.asksaveasfilename(
                title="Сохранить контракты как CSV",
                defaultextension=".csv",
                filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            )
            if not path:
                return
            with get_connection() as conn:
                result_path = export_contracts_to_csv(conn, path)
                self.status.configure(text=f"Экспорт CSV контрактов завершен: {result_path}")
        except Exception as e:
            self.status.configure(text=f"Ошибка экспорта CSV контрактов: {e}")

    def _save_contracts_csv_template(self) -> None:
        """Создание шаблона CSV файла для импорта контрактов"""
        try:
            from import_export.excel_io import generate_contracts_template
            path = filedialog.asksaveasfilename(
                title="Сохранить шаблон CSV контрактов",
                defaultextension=".csv",
                filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            )
            if not path:
                return
            result_path = generate_contracts_template(path)
            self.status.configure(text=f"Шаблон CSV контрактов создан: {result_path}")
        except Exception as e:
            self.status.configure(text=f"Ошибка создания шаблона CSV контрактов: {e}")

    def _import_products_contracts(self) -> None:
        """Импорт изделий с привязкой к контрактам из CSV файла"""
        try:
            from import_export.products_contracts_import import import_products_from_contracts_csv
            path = filedialog.askopenfilename(
                title="Выберите CSV файл с изделиями и контрактами",
                filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            )
            if not path:
                return
            
            # Создаем окно прогресса
            win = ctk.CTkToplevel(self)
            win.title("Импорт изделий с контрактами")
            win.geometry("420x140")
            ctk.CTkLabel(win, text="Выполняется импорт...").pack(anchor="w", padx=10, pady=(10, 6))
            pb = ctk.CTkProgressBar(win)
            pb.pack(fill="x", padx=10)
            pb.set(0)
            note_var = tk.StringVar(value="")
            ctk.CTkLabel(win, textvariable=note_var).pack(anchor="w", padx=10, pady=(6, 10))

            def progress_cb(step: int, total: int, note: str):
                # Обновление прогресса только из главного потока
                def _do():
                    try:
                        if not tk.Toplevel.winfo_exists(win):
                            return
                        pb.set(step / max(total, 1))
                        note_var.set(note)
                    except Exception:
                        pass
                try:
                    self.after(0, _do)
                except Exception:
                    pass

            def run():
                try:
                    result = import_products_from_contracts_csv(path, progress_cb)
                    def _success():
                        try:
                            messagebox.showinfo("Импорт",
                                f"Импорт завершен.\n"
                                f"Изделий: {result['products']}\n"
                                f"Контрактов: {result['contracts']}\n"
                                f"Ошибок: {result['errors']}")
                            self.status.configure(text=f"Импорт изделий с контрактами завершен. Изделий: {result['products']}, контрактов: {result['contracts']}")
                        except Exception:
                            pass
                    try:
                        self.after(0, _success)
                    except Exception:
                        pass
                except Exception as e:
                    def _err():
                        try:
                            messagebox.showerror("Импорт", str(e))
                            self.status.configure(text=f"Ошибка импорта изделий с контрактами: {e}")
                        except Exception:
                            pass
                    try:
                        self.after(0, _err)
                    except Exception:
                        pass
                finally:
                    def _close():
                        try:
                            if tk.Toplevel.winfo_exists(win):
                                win.destroy()
                        except Exception:
                            pass
                    try:
                        self.after(0, _close)
                    except Exception:
                        pass

            threading.Thread(target=run, daemon=True).start()
            
        except Exception as e:
            self.status.configure(text=f"Ошибка импорта изделий с контрактами: {e}")