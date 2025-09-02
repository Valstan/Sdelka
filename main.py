from __future__ import annotations

import logging

from config.settings import CONFIG
from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db
from utils.logging import configure_logging
from gui.app_window import AppWindow
from gui.login_dialog import LoginDialog
from utils.user_prefs import get_current_db_path, set_db_path
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # Проверка наличия БД ДО создания основного окна.
    # Если БД нет — используем простой tkinter-диалог без создания CTk-root,
    # чтобы избежать ошибок Tcl "after script" на первом запуске.
    db_path = get_current_db_path()
    if not db_path.exists():
        try:
            tmp = tk.Tk()
            tmp.withdraw()
            # Спросим: создать новую базу?
            create_new = messagebox.askyesno(
                "База данных",
                "База данных не найдена.\n\nСоздать новую базу данных?\n(Нет — выбрать существующую)",
                parent=tmp,
            )
            chosen: str | None = None
            if create_new:
                # Имя по умолчанию
                initial = "base_sdelka_rmz.db"
                chosen = filedialog.asksaveasfilename(
                    parent=tmp,
                    title="Создать новую базу данных",
                    defaultextension=".db",
                    initialfile=initial,
                    filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
                )
                if chosen:
                    from pathlib import Path as _P
                    p = _P(chosen)
                    try:
                        p.parent.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass
                    set_db_path(p)
                    with get_connection(p) as conn:
                        initialize_schema(conn)
            else:
                chosen = filedialog.askopenfilename(
                    parent=tmp,
                    title="Выберите файл базы данных",
                    filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
                )
                if chosen:
                    from pathlib import Path as _P
                    p = _P(chosen)
                    set_db_path(p)
            try:
                tmp.destroy()
            except Exception:
                pass
        except Exception:
            pass
        # обновим путь после выбора/создания
        from utils.user_prefs import get_current_db_path as _gp
        db_path = _gp()
        # Если по-прежнему файла нет — выходим тихо
        if not db_path.exists():
            logger.error("База данных не выбрана/не создана. Завершение.")
            return

    # Бэкап БД (если файл существует)
    backup_sqlite_db(db_path)

    # Инициализация схемы (идемпотентно, не затирает данные существующей БД)
    with get_connection() as conn:
        initialize_schema(conn)

    # Запуск GUI и диалог выбора режима до отображения основного окна
    app = AppWindow()
    from utils.runtime_mode import set_mode, AppMode
    try:
        dlg = LoginDialog(app)
        app.wait_window(dlg)
    except Exception:
        set_mode(AppMode.FULL)
    try:
        app.mainloop()
    finally:
        # Безопасно отменяем отложенные коллбеки, чтобы не было ошибок after script на первом старте
        try:
            if hasattr(app, "_after_ids"):
                for aid in list(app._after_ids):
                    try:
                        app.after_cancel(aid)
                    except Exception:
                        pass
        except Exception:
            pass


if __name__ == "__main__":
    main()