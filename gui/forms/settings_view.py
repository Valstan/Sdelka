from __future__ import annotations

import shutil
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import threading
import re

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
from utils.backup import backup_sqlite_db
from datetime import datetime
from tkinter import simpledialog
from utils.security import user_password_is_set, verify_user_password, save_user_password


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self._prefs = load_prefs()
        self._build_ui()

    def _build_ui(self) -> None:
        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(box, text="База данных").pack(anchor="w", pady=(0, 8))

        btns = ctk.CTkFrame(box)
        btns.pack(fill="x")

        self._btn_export_db = ctk.CTkButton(btns, text="Сохранить копию базы...", command=self._export_db)
        self._btn_export_db.pack(side="left", padx=6)
        self._btn_merge_db = ctk.CTkButton(btns, text="Слить с другой базой...", command=self._merge_db)
        self._btn_merge_db.pack(side="left", padx=6)
        # Импорт данных перенесён сюда
        self._btn_import_unified = ctk.CTkButton(btns, text="Импорт данных", command=self._import_unified)
        self._btn_import_unified.pack(side="left", padx=6)

        # Путь к БД (перенесено сюда)
        row_db = ctk.CTkFrame(box)
        row_db.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(row_db, text="Путь к файлу БД (.db)").pack(anchor="w", padx=6)
        self._db_path_var = ctk.StringVar(value=str(get_current_db_path()))
        self._db_path_entry = ctk.CTkEntry(row_db, textvariable=self._db_path_var)
        self._db_path_entry.pack(fill="x", padx=6)
        btns_db = ctk.CTkFrame(box)
        btns_db.pack(fill="x", pady=(4, 6))
        ctk.CTkButton(btns_db, text="Выбрать...", command=self._choose_existing_db).pack(side="left", padx=6)
        ctk.CTkButton(btns_db, text="Создать...", command=self._create_new_db).pack(side="left", padx=6)
        ctk.CTkButton(btns_db, text="Применить", command=self._apply_db_settings).pack(side="left", padx=6)
        ctk.CTkButton(btns_db, text="Проверить подключение", command=self._test_db_connection).pack(side="left", padx=6)

        # Версии базы данных (откат к бэкапу) — перенесено сюда
        backups_box = ctk.CTkFrame(box)
        backups_box.pack(fill="x", pady=(6, 6))
        self._backups_row = ctk.CTkFrame(backups_box)
        self._backups_row.pack(fill="x")
        ctk.CTkLabel(self._backups_row, text="Выберите версию:").pack(side="left", padx=6)
        self._backup_choice = ctk.StringVar(value="")
        self._backup_map = {}
        self._opt_backups = ctk.CTkOptionMenu(self._backups_row, values=["(бэкапы не найдены)"], variable=self._backup_choice)
        self._opt_backups.pack(side="left", padx=6)
        ctk.CTkButton(self._backups_row, text="Обновить список", command=self._refresh_backup_list).pack(side="left", padx=6)
        ctk.CTkButton(self._backups_row, text="Перейти на эту версию данных", fg_color="#2563eb", command=self._restore_selected_backup).pack(side="left", padx=6)
        try:
            self._refresh_backup_list()
        except Exception:
            pass

        # Статусная строка
        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(fill="x", padx=10, pady=10)

        # ---- Пароль пользователя ----
        pw_box = ctk.CTkFrame(self)
        pw_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(pw_box, text="Пароль пользователя (Полный доступ)").pack(anchor="w", pady=(0, 8))

        rowp = ctk.CTkFrame(pw_box)
        rowp.pack(fill="x", pady=(2, 6))
        ctk.CTkButton(rowp, text="Сменить пароль...", command=self._change_user_password).pack(side="left", padx=6)
        ctk.CTkLabel(rowp, text="Для смены требуется текущий пароль").pack(side="left", padx=6)

        rowps = ctk.CTkFrame(pw_box)
        rowps.pack(fill="x")
        ctk.CTkButton(rowps, text="Установить пароль...", command=self._set_user_password).pack(side="left", padx=6)
        ctk.CTkLabel(rowps, text="Если пароль ещё не установлен").pack(side="left", padx=6)

        # ---- Настройки интерфейса (перенесены ниже пароля) ----
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

        # Применить ограничения режима только просмотра
        if self._readonly:
            # Запретить изменяющие БД и системные действия
            for b in (
                self._btn_merge_db,
                self._db_path_entry,
                self._btn_import_unified,
                self._opt_list_font,
                self._opt_ui_font,
                # пароль менять нельзя в readonly
                # кнопки оставляем активными только при полном доступе
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
        initial_name = "base_sdelka_rmz.db"
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

            # Применить значения по умолчанию для WAL/таймаута без UI
            set_enable_wal(True)
            set_busy_timeout_ms(10000)

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
        # Стандарт: backup_base_sdelka_MMDD_HHMM
        stamp = datetime.now().strftime("%m%d_%H%M")
        initial = f"backup_base_sdelka_{stamp}.db"
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
                        # После успешного импорта/чернового прогона — освежить списки в открытых формах
                        try:
                            root = self.winfo_toplevel()
                            # Простой способ: отправим виртуальные событие для всех слушателей
                            root.event_generate('<<DataImported>>', when='tail')
                        except Exception:
                            pass
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

    # ---- Password handlers ----
    def _set_user_password(self) -> None:
        if self._readonly:
            messagebox.showwarning("Пароль", "Режим 'Просмотр' — операция недоступна")
            return
        if user_password_is_set():
            messagebox.showinfo("Пароль", "Пароль уже установлен. Используйте 'Сменить пароль...'.")
            return
        new1 = simpledialog.askstring("Установка пароля", "Введите новый пароль:", parent=self, show="*")
        if new1 is None or new1.strip() == "":
            return
        new2 = simpledialog.askstring("Установка пароля", "Повторите новый пароль:", parent=self, show="*")
        if new2 is None:
            return
        if new1 != new2:
            messagebox.showerror("Пароль", "Пароли не совпадают.")
            return
        try:
            save_user_password(new1)
            messagebox.showinfo("Пароль", "Пароль установлен.")
        except Exception as exc:
            messagebox.showerror("Пароль", f"Ошибка сохранения: {exc}")

    def _change_user_password(self) -> None:
        if self._readonly:
            messagebox.showwarning("Пароль", "Режим 'Просмотр' — операция недоступна")
            return
        if not user_password_is_set():
            messagebox.showinfo("Пароль", "Пароль ещё не установлен. Используйте 'Установить пароль...'.")
            return
        cur = simpledialog.askstring("Смена пароля", "Введите текущий пароль:", parent=self, show="*")
        if cur is None:
            return
        if not verify_user_password(cur):
            messagebox.showerror("Пароль", "Текущий пароль неверен.")
            return
        new1 = simpledialog.askstring("Смена пароля", "Введите новый пароль:", parent=self, show="*")
        if new1 is None or new1.strip() == "":
            return
        new2 = simpledialog.askstring("Смена пароля", "Повторите новый пароль:", parent=self, show="*")
        if new2 is None:
            return
        if new1 != new2:
            messagebox.showerror("Пароль", "Пароли не совпадают.")
            return
        try:
            save_user_password(new1)
            messagebox.showinfo("Пароль", "Пароль изменён.")
        except Exception as exc:
            messagebox.showerror("Пароль", f"Ошибка сохранения: {exc}")

    # --- Backups list/restore ---
    def _parse_backup_timestamp(self, path: Path) -> datetime | None:
        # Шаблон нового имени: backup_base_sdelka_MMDD_HHMM
        stem = path.stem
        m = re.fullmatch(r"backup_base_sdelka_(\d{2})(\d{2})_(\d{2})(\d{2})", stem)
        if not m:
            return None
        month, day, hour, minute = m.groups()
        try:
            now = datetime.now()
            return datetime(year=now.year, month=int(month), day=int(day), hour=int(hour), minute=int(minute))
        except Exception:
            return None

    def _format_ru_dt(self, dt: datetime) -> str:
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        ]
        d = dt.day
        m = months[dt.month - 1]
        y = dt.year
        hh = dt.hour
        mm = dt.minute
        return f"База от {d} {m} {y} года {hh} часов {mm:02d} минут"

    def _list_backups(self) -> list[Path]:
        """Ищет бэкапы только в каталоге backups приложения."""
        search_dirs: list[Path] = []
        try:
            search_dirs.append(CONFIG.backups_dir)
        except Exception:
            pass
        seen: set[str] = set()
        found: list[Path] = []
        for d in search_dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            try:
                # Прямые файлы в каталоге
                for p in d.iterdir():
                    if not p.is_file():
                        continue
                    if p.suffix.lower() != ".db":
                        continue
                    if re.fullmatch(r"backup_base_sdelka_\d{4}_\d{4}", p.stem):
                        key = str(p.resolve()).lower()
                        if key not in seen:
                            seen.add(key)
                            found.append(p)
                # Вложенные (если есть подпапки)
                for sub in d.rglob("*.db"):
                    try:
                        if sub.is_file() and re.fullmatch(r"backup_base_sdelka_\d{4}_\d{4}", sub.stem):
                            key = str(sub.resolve()).lower()
                            if key not in seen:
                                seen.add(key)
                                found.append(sub)
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        except Exception:
            pass
        return found

    def _refresh_backup_list(self) -> None:
        try:
            self._backup_map.clear()
            files = self._list_backups()
            options: list[str] = []
            used_labels: set[str] = set()
            for p in files:
                dt = self._parse_backup_timestamp(p)
                if dt is None:
                    try:
                        dt = datetime.fromtimestamp(p.stat().st_mtime)
                    except Exception:
                        dt = None
                base_label = self._format_ru_dt(dt) if dt else p.stem
                label = base_label
                if label in used_labels:
                    label = f"{base_label} — {p.name}"
                used_labels.add(label)
                self._backup_map[label] = str(p)
                options.append(label)
            if not options:
                options = ["(бэкапы не найдены)"]
            # Обновление UI должно происходить в главном потоке
            def _apply():
                try:
                    # Перед применением убедимся, что карта отображает только реально существующие файлы
                    for k in list(self._backup_map.keys()):
                        try:
                            if not Path(self._backup_map[k]).exists():
                                self._backup_map.pop(k, None)
                        except Exception:
                            self._backup_map.pop(k, None)
                    self._rebuild_backups_ui(options)
                except Exception:
                    pass
            try:
                self.after(0, _apply)
            except Exception:
                _apply()
        except Exception:
            pass

    def _rebuild_backups_ui(self, options: list[str]) -> None:
        """Полностью пересобирает строку выбора бэкапов, чтобы исключить дубли и устаревшие элементы."""
        row = getattr(self, "_backups_row", None)
        if row is None or not row.winfo_exists():
            return
        # Найти все кнопки справа, чтобы перепаковать их после OptionMenu
        children = list(row.winfo_children())
        right_buttons: list[ctk.CTkButton] = []
        for w in children:
            try:
                if isinstance(w, ctk.CTkButton) and w.cget("text") in {"Обновить список", "Перейти на эту версию данных"}:
                    right_buttons.append(w)
            except Exception:
                pass
        # Удалить все существующие OptionMenu в строке
        for w in children:
            try:
                if isinstance(w, ctk.CTkOptionMenu):
                    w.destroy()
            except Exception:
                pass
        # Снять и перепаковать кнопки справа, чтобы Order: [Label] [OptionMenu] [Buttons...]
        for b in right_buttons:
            try:
                b.pack_forget()
            except Exception:
                pass
        # Создать новый OptionMenu
        self._backup_choice = ctk.StringVar(value=options[0])
        self._opt_backups = ctk.CTkOptionMenu(row, values=options, variable=self._backup_choice)
        self._opt_backups.pack(side="left", padx=6)
        # Вернуть кнопки справа
        for b in right_buttons:
            try:
                b.pack(side="left", padx=6)
            except Exception:
                pass

    def _restore_selected_backup(self) -> None:
        if self._readonly:
            messagebox.showwarning("Восстановление БД", "Режим только для чтения — действие недоступно")
            return
        label = self._backup_choice.get().strip()
        backup_path = self._backup_map.get(label)
        if not backup_path or "не найдены" in label:
            messagebox.showwarning("Восстановление БД", "Выберите доступную версию из списка")
            return
        backup_file = Path(backup_path)
        if not backup_file.exists():
            messagebox.showerror("Восстановление БД", "Файл бэкапа не найден на диске")
            return
        if not messagebox.askyesno("Восстановление БД", "Перейти на выбранную версию?\nТекущая база будет сохранена как бэкап."):
            return
        try:
            # 1) Сохранить текущую БД в бэкап
            cur = Path(get_current_db_path())
            backup_sqlite_db(cur)
            # 2) Перезаписать канонический файл основной БД (имя неизменно)
            shutil.copy2(backup_file, cur)
            # 3) Обновить статус и поле пути (оно не меняется)
            self._db_path_var.set(str(cur))
            self.status.configure(text="База восстановлена из бэкапа. Перезапустите приложение для применения во всех окнах.")
        except Exception as exc:
            messagebox.showerror("Восстановление БД", f"Ошибка восстановления: {exc}")


    # История версий отключена
    def _show_changelog(self) -> None:
        messagebox.showinfo("Версии программы", "История версий отключена.")

    def _get_changelog_content(self) -> str:
        return ""

    def _copy_changelog_to_clipboard(self, content: str) -> None:
        return

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