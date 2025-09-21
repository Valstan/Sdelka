"""Диалог прогресса синхронизации с Яндекс.Диском"""

from __future__ import annotations

import customtkinter as ctk
import threading
from typing import Optional, Callable


class SyncProgressDialog(ctk.CTkToplevel):
    """Всплывающее окно с прогрессом синхронизации"""

    def __init__(self, parent, title: str = "Синхронизация данных"):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        # Центрируем окно
        self.transient(parent)
        self.grab_set()

        # Позиционируем по центру родительского окна
        if parent:
            parent.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
            self.geometry(f"400x200+{x}+{y}")

        self._cancelled = False
        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса диалога"""

        # Основной фрейм
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            main_frame,
            text="Синхронизация с Яндекс.Диском",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.title_label.pack(pady=(10, 20))

        # Статус операции
        self.status_label = ctk.CTkLabel(
            main_frame, text="Подготовка к синхронизации...", font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(0, 15))

        # Прогресс-бар
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=300)
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)

        # Детальная информация
        self.details_label = ctk.CTkLabel(
            main_frame, text="", font=ctk.CTkFont(size=10), text_color="gray"
        )
        self.details_label.pack(pady=(0, 15))

        # Кнопки
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 0))

        self.cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            width=100,
            command=self._on_cancel,
            fg_color="gray",
            hover_color="darkgray",
        )
        self.cancel_button.pack(side="left", padx=(0, 10))

        self.close_button = ctk.CTkButton(
            buttons_frame,
            text="Закрыть",
            width=100,
            command=self._on_close,
            state="disabled",
        )
        self.close_button.pack(side="left")

    def update_status(self, status: str, progress: float = None, details: str = ""):
        """Обновить статус синхронизации"""
        try:
            self.status_label.configure(text=status)
            if progress is not None:
                self.progress_bar.set(max(0, min(1, progress)))
            if details:
                self.details_label.configure(text=details)
            self.update_idletasks()
        except Exception:
            pass  # Игнорируем ошибки обновления UI

    def set_completed(self, success: bool = True, message: str = ""):
        """Отметить синхронизацию как завершенную"""
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"Устанавливаем завершение диалога: success={success}, message={message}"
            )

            if success:
                self.status_label.configure(text="Синхронизация завершена успешно")
                self.progress_bar.set(1.0)
                self.title_label.configure(text="✅ Синхронизация завершена")
            else:
                self.status_label.configure(text="Ошибка синхронизации")
                self.title_label.configure(text="❌ Ошибка синхронизации")

            if message:
                self.details_label.configure(text=message)

            self.cancel_button.configure(state="disabled")
            self.close_button.configure(state="normal")

            # Автоматически закрыть через 3 секунды при успехе
            if success:
                logger.info("Планируем автозакрытие диалога через 3 секунды")
                self.after(3000, self._on_close)
            else:
                logger.info("Ошибка - диалог не закроется автоматически")

        except Exception as exc:
            import logging

            logging.getLogger(__name__).exception(f"Ошибка в set_completed: {exc}")

    def _on_cancel(self):
        """Обработка отмены синхронизации"""
        self._cancelled = True
        self.update_status(
            "Отмена синхронизации...", details="Завершение текущих операций..."
        )
        self.cancel_button.configure(state="disabled")

    def _on_close(self):
        """Закрытие диалога"""
        try:
            import logging

            logging.getLogger(__name__).info("Закрываем диалог синхронизации")
            self.destroy()
        except Exception as exc:
            import logging

            logging.getLogger(__name__).exception(f"Ошибка закрытия диалога: {exc}")

    def is_cancelled(self) -> bool:
        """Проверить, была ли отменена синхронизация"""
        return self._cancelled


class SyncProgressManager:
    """Менеджер для управления диалогом прогресса синхронизации"""

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.dialog: Optional[SyncProgressDialog] = None
        self._sync_thread: Optional[threading.Thread] = None

    def start_sync(
        self, sync_function: Callable[[], bool], title: str = "Синхронизация данных"
    ) -> None:
        """
        Запустить синхронизацию с диалогом прогресса

        Args:
            sync_function: Функция синхронизации, должна возвращать bool (успех/неудача)
            title: Заголовок диалога
        """
        if self.dialog:
            return  # Уже идет синхронизация

        # Создаем диалог
        self.dialog = SyncProgressDialog(self.parent_window, title)

        # Запускаем синхронизацию в отдельном потоке
        self._sync_thread = threading.Thread(
            target=self._sync_worker, args=(sync_function,), daemon=True
        )
        self._sync_thread.start()

    def _sync_worker(self, sync_function: Callable[[], bool]):
        """Рабочий поток синхронизации"""
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info("Начало работы потока синхронизации")

            # Начальный статус
            if self.dialog:
                self.dialog.update_status("Подготовка к синхронизации...", 0.1)

            # Устанавливаем callback для обновления статуса
            from services.auto_sync import set_sync_status_callback

            def status_callback(status: str):
                logger.info(f"Callback статуса: {status}")
                if self.dialog and not self.dialog.is_cancelled():
                    # Определяем прогресс по статусу
                    progress = 0.1
                    if "Скачивание" in status or "скачивание" in status:
                        progress = 0.3
                    elif "Объединение" in status or "объединение" in status:
                        progress = 0.6
                    elif "Загрузка" in status or "загрузка" in status:
                        progress = 0.9
                    elif "завершена" in status or "завершено" in status:
                        progress = 1.0

                    self.dialog.update_status(status, progress)

            # Устанавливаем callback
            set_sync_status_callback(status_callback)
            logger.info("Callback установлен, запускаем синхронизацию")

            # Выполняем синхронизацию (callback'и будут вызываться автоматически)
            logger.info("Вызываем функцию синхронизации...")
            try:
                success = sync_function()
                logger.info(f"Функция синхронизации вернула результат: {success}")
            except Exception as sync_exc:
                logger.exception(f"Ошибка в функции синхронизации: {sync_exc}")
                success = False

            # Финальное обновление статуса
            if self.dialog:
                if success:
                    self.dialog.update_status("Синхронизация завершена успешно!", 1.0)
                else:
                    self.dialog.update_status("Ошибка синхронизации", 0.5)

            if self.dialog and not self.dialog.is_cancelled():
                if success:
                    logger.info("Устанавливаем статус завершения (успех)")
                    self.dialog.set_completed(True, "Данные успешно синхронизированы")
                else:
                    logger.info("Устанавливаем статус завершения (ошибка)")
                    self.dialog.set_completed(
                        False, "Не удалось завершить синхронизацию"
                    )

        except Exception as exc:
            import logging

            logging.getLogger(__name__).exception(
                f"Ошибка в потоке синхронизации: {exc}"
            )
            if self.dialog:
                self.dialog.set_completed(False, f"Ошибка: {exc}")
        finally:
            # Очищаем callback
            try:
                from services.auto_sync import set_sync_status_callback

                set_sync_status_callback(None)
            except Exception:
                pass

            # Очищаем ссылки
            self._sync_thread = None
            # Планируем очистку диалога через 5 секунд
            if self.dialog:
                self.dialog.after(5000, self._cleanup_dialog)

    def _cleanup_dialog(self):
        """Очистка диалога (вызывается автоматически)"""
        if self.dialog:
            try:
                self.dialog.destroy()
            except Exception:
                pass
            self.dialog = None

    def cleanup(self):
        """Очистка ресурсов"""
        if self.dialog:
            try:
                self.dialog.destroy()
            except Exception:
                pass
            self.dialog = None
