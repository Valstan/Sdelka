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


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # Проверка наличия БД; при отсутствии — запросить путь/создать
    db_path = get_current_db_path()
    if not db_path.exists():
        try:
            setup = DbSetupDialog(app)
            app.wait_window(setup)
        except Exception:
            # если диалог не удалось показать, продолжим с дефолтным путём
            pass
        # обновим путь
        from utils.user_prefs import get_current_db_path as _gp
        db_path = _gp()

    # Бэкап БД (если файл существует)
    backup_sqlite_db(db_path)

    # Инициализация схемы
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
    app.mainloop()


if __name__ == "__main__":
    main()