from __future__ import annotations

import logging

from config.settings import CONFIG
from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db
from utils.logging import configure_logging
from gui.app_window import AppWindow
from gui.login_dialog import LoginDialog
from utils.user_prefs import get_current_db_path
from gui.db_setup_dialog import DbSetupDialog
import customtkinter as ctk


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # Проверка наличия БД ДО создания основного окна.
    # Если БД нет — показываем диалог выбора/создания на временном скрытом корне.
    db_path = get_current_db_path()
    if not db_path.exists():
        try:
            tmp_root = ctk.CTk()
            tmp_root.withdraw()
            setup = DbSetupDialog(tmp_root)
            tmp_root.wait_window(setup)
            try:
                tmp_root.destroy()
            except Exception:
                pass
        except Exception:
            pass
        # обновим путь после диалога
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

    # Запуск GUI
    app = AppWindow()
    # Диалог выбора режима до показа основного окна
    from utils.runtime_mode import get_mode, set_mode, AppMode
    try:
        dlg = LoginDialog(app)
        app.wait_window(dlg)
    except Exception:
        # по умолчанию полный доступ
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