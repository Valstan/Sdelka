"""
Главный модуль приложения. Точка входа в программу.
Создает главное окно и запускает приложение.
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from app.app_gui import AppGUI
from app.core.database.connections import DatabaseManager
from app.config import APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_THEME, LOGGING_SETTINGS, DB_SETTINGS


def configure_logging():
    log_dir = Path(LOGGING_SETTINGS['log_dir'])
    log_dir.mkdir(parents=True, exist_ok=True)  # Создаем директорию

    log_file = str(log_dir / f"{LOGGING_SETTINGS['log_file_prefix']}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(
        filename=log_file,
        mode=LOGGING_SETTINGS.get('log_mode', 'a'),
        encoding='utf-8'
    )

    logging.basicConfig(
        level=LOGGING_SETTINGS['log_level'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, logging.StreamHandler()]
    )

def main() -> None:
    """Основная функция инициализации и запуска приложения."""

    # Инициализация системы логирования
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Запуск приложения")

    try:
        # Инициализация базы данных
        db_manager = DatabaseManager(DB_SETTINGS['database_path'])

        # Создаем директорию, если ее нет
        Path(db_manager.db_path).parent.mkdir(parents=True, exist_ok=True)

        if DB_SETTINGS['create_backup_on_start']:
            db_manager.create_backup()

        # Настройка графического интерфейса
        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme("blue")

        # Создание главного окна
        root = ctk.CTk()
        root.title(APP_TITLE)
        root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        root.minsize(int(APP_WIDTH * 0.7), int(APP_HEIGHT * 0.7))

        # Инициализация основного интерфейса
        AppGUI(root, db_manager)

        # Запуск главного цикла
        root.mainloop()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'db_manager' in locals():
            db_manager.close()
        logger.info("Приложение завершило работу")

if __name__ == "__main__":
    main()