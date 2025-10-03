from __future__ import annotations

import logging
import threading
from typing import Optional
from gui.sync_progress_dialog import SyncProgressManager

logger = logging.getLogger(__name__)


class SyncManager:
    """Управляет синхронизацией данных."""
    
    def __init__(self, parent):
        self.parent = parent
        self._sync_progress_manager = SyncProgressManager(parent)
        self._sync_thread: Optional[threading.Thread] = None
        self._sync_running = False
        self._after_ids: set[str] = set()
        
    def start_background_sync(self) -> None:
        """Запускает фоновую синхронизацию при старте."""
        try:
            logger.info("Запуск фоновой синхронизации при старте...")
            
            def background_sync():
                try:
                    # Импортируем здесь, чтобы избежать циклических импортов
                    from services.auto_sync import sync_on_startup
                    sync_on_startup()
                    # После завершения обновляем статус
                    self._schedule_status_update("Синхронизация завершена")
                except Exception as exc:
                    logger.exception("Ошибка фоновой синхронизации: %s", exc)
                    self._schedule_status_update("Ошибка синхронизации")

            self._sync_thread = threading.Thread(target=background_sync, daemon=True)
            self._sync_thread.start()

            # Показываем статус синхронизации
            self._schedule_status_update("Синхронизация в фоне...")

        except Exception as exc:
            logger.exception("Ошибка запуска фоновой синхронизации: %s", exc)
    
    def start_periodic_sync(self) -> None:
        """Запускает периодическую синхронизацию."""
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from services.auto_sync import start_periodic_sync
            start_periodic_sync(self.parent)
            logger.info("Периодическая синхронизация запущена")
        except ImportError:
            logger.warning("Функция start_periodic_sync не найдена в services.auto_sync")
        except Exception as exc:
            logger.exception("Ошибка запуска периодической синхронизации: %s", exc)
    
    def _schedule_status_update(self, status: str) -> None:
        """Планирует обновление статуса синхронизации."""
        def update_status():
            self._update_sync_status(status)
        
        try:
            if hasattr(self.parent, 'after') and hasattr(self.parent, 'winfo_exists'):
                # Проверяем, что окно еще существует
                try:
                    if self.parent.winfo_exists():
                        after_id = self.parent.after(1000, update_status)
                        self._after_ids.add(str(after_id))
                except RuntimeError:
                    # Окно уже уничтожено, игнорируем
                    logger.debug("Окно уже уничтожено, пропускаем обновление статуса")
        except Exception as exc:
            logger.debug("Ошибка планирования обновления статуса: %s", exc)
    
    def _update_sync_status(self, status: str) -> None:
        """Обновляет статус синхронизации."""
        try:
            if hasattr(self.parent, '_update_sync_status'):
                self.parent._update_sync_status(status)
        except Exception as exc:
            logger.exception("Ошибка обновления статуса синхронизации: %s", exc)
    
    def show_sync_dialog(self) -> None:
        """Показывает диалог синхронизации."""
        try:
            self._sync_progress_manager.show_sync_dialog()
        except Exception as exc:
            logger.exception("Ошибка показа диалога синхронизации: %s", exc)
    
    def cancel_sync(self) -> None:
        """Отменяет синхронизацию."""
        try:
            self._sync_running = False
            if self._sync_thread and self._sync_thread.is_alive():
                # Не можем принудительно остановить поток, но можем установить флаг
                logger.info("Запрос на отмену синхронизации")
        except Exception as exc:
            logger.exception("Ошибка отмены синхронизации: %s", exc)
    
    def cleanup(self) -> None:
        """Очищает ресурсы."""
        try:
            # Отменяем все запланированные задачи
            for after_id in self._after_ids:
                try:
                    self.parent.after_cancel(int(after_id))
                except Exception:
                    pass
            
            self._after_ids.clear()
            
            # Отменяем синхронизацию
            self.cancel_sync()
            
        except Exception as exc:
            logger.exception("Ошибка очистки SyncManager: %s", exc)
