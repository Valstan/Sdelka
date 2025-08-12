from __future__ import annotations

import logging

from config.settings import CONFIG
from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db
from utils.logging import configure_logging
from gui.app_window import AppWindow


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # Бэкап БД (если файл существует)
    backup_sqlite_db(CONFIG.db_path)

    # Инициализация схемы
    with get_connection(CONFIG.db_path) as conn:
        initialize_schema(conn)

    # Запуск GUI
    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()