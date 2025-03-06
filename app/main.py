"""
Главный модуль приложения. Точка входа в программу.
Здесь создается главное окно и запускается приложение.
"""
import os
import sys
import logging
from datetime import datetime

import customtkinter as ctk
from app.config import APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_THEME
from app.gui.app_gui import AppGUI
from app.db.db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"app_log_{datetime.now().strftime('%Y%m%d')}.log"),
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
        # Настраиваем тему оформления
        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme("blue")

        # Инициализируем соединение с БД
        db_manager = DatabaseManager()

        # Создаем главное окно приложения
        root = ctk.CTk()
        root.title(APP_TITLE)
        root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")

        # Создаем и размещаем GUI приложения
        app = AppGUI(root, db_manager)

        # Запускаем главный цикл обработки событий
        root.mainloop()

        # Закрываем соединение с БД при выходе
        db_manager.close()

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        # Показываем сообщение об ошибке пользователю
        ctk.CTkMessageBox.show_error("Ошибка", f"Произошла ошибка при запуске приложения:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()