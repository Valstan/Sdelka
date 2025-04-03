"""
Главный модуль приложения. Точка входа в программу.
Создает главное окно и запускает приложение.
"""
import sys
import logging
from datetime import datetime

import customtkinter as ctk

from app.app_gui import AppGUI
from app.db_manager import DatabaseManager
from app.config import APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_THEME, LOGGING_SETTINGS


def configure_logging() -> None:
    """Настройка системы логирования приложения."""
    logging.basicConfig(
        level=LOGGING_SETTINGS['log_level'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                LOGGING_SETTINGS['log_dir'] /
                f"{LOGGING_SETTINGS['log_file_prefix']}_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )

def main() -> None:
    """Основная функция инициализации и запуска приложения."""
    try:
        # Инициализация системы логирования
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.info("Запуск приложения")

        # Инициализация базы данных
        db_manager = DatabaseManager()

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