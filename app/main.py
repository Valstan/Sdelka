"""
Главный модуль приложения. Точка входа в программу.
Здесь создается главное окно и запускается приложение.
"""
import os
import logging
import sys
from datetime import datetime

import customtkinter as ctk
from app.config import APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_THEME, LOGGING_SETTINGS
from app.gui.app_gui import AppGUI
from app.db.db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(
                LOGGING_SETTINGS['log_dir'],
                f"{LOGGING_SETTINGS['log_file_prefix']}_{datetime.now().strftime('%Y%m%d')}.log"
            )
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Главная функция запуска приложения.
    Инициализирует базу данных и GUI, настраивает внешний вид приложения.
    """
    try:
        # Инициализация базы данных
        db_manager = DatabaseManager()

        # Настройка интерфейса
        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme("blue")

        # Создание главного окна
        root = ctk.CTk()
        root.title(APP_TITLE)
        root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        root.minsize(APP_WIDTH // 1.5, APP_HEIGHT // 1.5)

        # Инициализация GUI
        app = AppGUI(root, db_manager)

        # Запуск главного цикла обработки событий
        root.mainloop()

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()