"""Автоматическая синхронизация баз данных через Яндекс.Диск

Этот модуль реализует:
1. Загрузку свежей БД при старте программы
2. Периодическую синхронизацию каждые 30 минут
3. Умное объединение баз данных с разрешением конфликтов
4. Обновление UI в реальном времени
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
import tkinter.messagebox as messagebox
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from config.settings import CONFIG
from services.merge_db import merge_from_file
from utils.backup import backup_sqlite_db
from utils.user_prefs import load_prefs, get_current_db_path
from utils.yadisk import YaDiskClient, YaDiskConfig

logger = logging.getLogger(__name__)

# Глобальные переменные для управления синхронизацией
_sync_thread: Optional[threading.Thread] = None
_sync_stop_event = threading.Event()
_ui_refresh_callback: Optional[Callable[[], None]] = None
_sync_status_callback: Optional[Callable[[str], None]] = None


def _safe_callback(callback: Optional[Callable], *args, **kwargs) -> None:
    """Безопасно вызывает callback функцию, игнорируя ошибки UI."""
    if callback is None:
        return
    
    try:
        callback(*args, **kwargs)
    except Exception as exc:
        logger.debug(f"Ignored callback error: {exc}")
        # Игнорируем ошибки callback (обычно это TclError от UI)


class SyncConflictResolver:
    """Класс для разрешения конфликтов при объединении баз данных"""

    def __init__(self, parent_window=None):
        self.parent_window = parent_window

    def resolve_conflict(
        self,
        conflict_type: str,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
    ) -> str:
        """
        Разрешение конфликта с участием пользователя

        Returns: 'local', 'remote', 'merge' или 'skip'
        """
        if not self.parent_window:
            # Автоматическое разрешение: приоритет удаленным данным
            logger.info(f"Авторазрешение конфликта {conflict_type}: выбираем remote")
            return "remote"

        try:
            # Показываем диалог пользователю
            message = f"""Обнаружен конфликт при синхронизации данных:

Тип конфликта: {conflict_type}

Локальные данные: {local_data}
Удаленные данные: {remote_data}

Что делать?"""

            # Создаем диалог с кнопками
            result = messagebox.askyesnocancel(
                "Конфликт синхронизации",
                message
                + "\n\nДа - использовать удаленные данные\nНет - оставить локальные\nОтмена - пропустить",
            )

            if result is True:
                return "remote"
            elif result is False:
                return "local"
            else:
                return "skip"

        except Exception as exc:
            logger.exception("Ошибка при разрешении конфликта: %s", exc)
            return "remote"  # Безопасный выбор по умолчанию


def _get_yadisk_client() -> Optional[YaDiskClient]:
    """Получить настроенный клиент Яндекс.Диска"""
    try:
        prefs = load_prefs()
        remote_dir = (
            prefs.yandex_remote_dir
            or CONFIG.yandex_default_remote_dir
            or "/SdelkaBackups"
        ).strip()

        token = (
            os.environ.get("YADISK_OAUTH_TOKEN")
            or prefs.yandex_oauth_token
            or CONFIG.yandex_default_oauth_token
            or ""
        ).strip()

        if not token:
            logger.warning("Яндекс.Диск: токен не настроен")
            return None

        # Создаем клиент и проверяем токен
        client = YaDiskClient(YaDiskConfig(oauth_token=token, remote_dir=remote_dir))

        # Проверяем авторизацию
        try:
            is_valid, message = client.test_connection()
            if not is_valid:
                logger.error("Яндекс.Диск: ошибка авторизации - %s", message)
                if "401" in message or "UNAUTHORIZED" in message:
                    logger.error(
                        "Токен Яндекс.Диска недействителен или истек. Обновите токен в настройках."
                    )
                return None
        except Exception as test_exc:
            logger.exception("Ошибка проверки токена Яндекс.Диска: %s", test_exc)
            return None

        return client

    except Exception as exc:
        logger.exception("Ошибка создания клиента Яндекс.Диска: %s", exc)
        return None


def _download_fresh_db() -> Optional[Path]:
    """Скачать свежую версию БД с Яндекс.Диска"""
    client = _get_yadisk_client()
    if not client:
        return None

    try:
        # Временный файл для скачивания
        temp_db = Path(CONFIG.data_dir) / "temp_remote.db"
        remote_path = f"{client.cfg.remote_dir}/sdelka_base.db"

        logger.info("Скачиваем свежую БД с Яндекс.Диска: %s", remote_path)

        # Проверяем, существует ли файл на диске
        if not client._resource_exists(remote_path):
            logger.info("БД не найдена на Яндекс.Диске (первая синхронизация)")
            return None

        client.download_file(remote_path, temp_db)

        # Проверяем, что скачанный файл - это SQLite БД
        if not _is_valid_sqlite_db(temp_db):
            logger.error("Скачанный файл не является валидной SQLite БД")
            temp_db.unlink(missing_ok=True)
            return None

        logger.info("Свежая БД успешно скачана: %s", temp_db)
        return temp_db

    except Exception as exc:
        logger.exception("Ошибка скачивания свежей БД: %s", exc)
        return None


def _is_valid_sqlite_db(db_path: Path) -> bool:
    """Проверить, что файл является валидной SQLite БД"""
    try:
        if not db_path.exists() or db_path.stat().st_size < 100:
            return False

        with sqlite3.connect(str(db_path)) as conn:
            # Простая проверка - выполняем базовый запрос
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
            ).fetchone()
            return True

    except Exception:
        return False


def _merge_databases(
    local_db: Path,
    remote_db: Path,
    conflict_resolver: Optional[SyncConflictResolver] = None,
) -> bool:
    """
    Объединить удаленную БД с локальной

    Returns: True если объединение успешно
    """
    try:
        logger.info("Начинаем объединение БД: local=%s, remote=%s", local_db, remote_db)

        # Создаем бэкап локальной БД перед объединением
        backup_path = backup_sqlite_db(local_db)
        if backup_path:
            logger.info("Создан бэкап локальной БД: %s", backup_path)

        # Выполняем объединение
        refs_upserts, orders_merged = merge_from_file(str(local_db), str(remote_db))

        logger.info(
            "Объединение завершено: refs_upserts=%d, orders_merged=%d",
            refs_upserts,
            orders_merged,
        )

        return True

    except Exception as exc:
        logger.exception("Ошибка объединения БД: %s", exc)
        return False


def _upload_merged_db(db_path: Path) -> bool:
    """Загрузить объединенную БД на Яндекс.Диск"""
    client = _get_yadisk_client()
    if not client:
        return False

    try:
        logger.info("Загружаем объединенную БД на Яндекс.Диск: %s", db_path)

        # Используем rotate_and_upload для создания бэкапа старой версии
        remote_path = client.rotate_and_upload(
            db_path,
            canonical_name="sdelka_base.db",
            backup_prefix="backup_base_sdelka_",
            max_keep=20,
        )

        logger.info("Объединенная БД успешно загружена: %s", remote_path)
        return True

    except Exception as exc:
        logger.exception("Ошибка загрузки объединенной БД: %s", exc)
        return False


def _should_sync() -> bool:
    """
    Простая логика: всегда синхронизируемся если есть доступ к Яндекс.Диску
    Никаких сложных проверок версий - просто всегда объединяем данные
    """
    client = _get_yadisk_client()
    return client is not None


def _safe_remove_temp_file(file_path: Path) -> None:
    """Безопасно удаляет временный файл, принудительно закрывая SQLite соединения"""
    if not file_path or not file_path.exists():
        return

    try:
        # Принудительно закрываем все SQLite соединения к этому файлу
        import gc

        # Запускаем сборщик мусора для закрытия неиспользуемых соединений
        gc.collect()

        # Пытаемся удалить файл
        file_path.unlink(missing_ok=True)
        logger.debug(f"Временный файл удален: {file_path}")

    except PermissionError as exc:
        logger.warning(f"Не удалось удалить временный файл {file_path}: {exc}")

        # Пытаемся переименовать для удаления позже
        try:
            import time

            backup_name = f"{file_path}.delete_me_{int(time.time())}"
            file_path.rename(backup_name)
            logger.info(f"Файл переименован для удаления позже: {backup_name}")
        except Exception:
            logger.warning(f"Временный файл остался: {file_path}")

    except Exception as exc:
        logger.exception(f"Ошибка удаления временного файла {file_path}: {exc}")


def sync_on_startup() -> bool:
    """
    Синхронизация при запуске программы - всегда объединяем локальную и удаленную БД

    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Синхронизация при запуске ===")

    _safe_callback(_sync_status_callback, "Проверка локальной БД...")

    try:
        local_db = Path(get_current_db_path())

        # КАРДИНАЛЬНОЕ ИЗМЕНЕНИЕ: Если локальная БД существует - НЕ синхронизируемся при запуске!
        # Это предотвращает постоянное дублирование данных
        if local_db.exists():
            logger.info("Локальная БД найдена, синхронизация при запуске НЕ НУЖНА")
            _safe_callback(_sync_status_callback, "Локальная БД готова к работе")
            return True

        # Проверяем доступность Яндекс.Диска
        client = _get_yadisk_client()
        if not client:
            logger.warning("Яндекс.Диск недоступен, работаем только с локальной БД")
            if _sync_status_callback:
                _sync_status_callback(
                    "Работаем без синхронизации (Яндекс.Диск недоступен)"
                )

            # Если локальная БД есть, возвращаем True (можем работать)
            return local_db.exists()

        # Скачиваем свежую версию с Яндекс.Диска
        if _sync_status_callback:
            _sync_status_callback("Скачивание данных с облака...")
        remote_db = _download_fresh_db()

        # Если локальная БД не существует
        if not local_db.exists():
            if remote_db:
                logger.info("Локальная БД не найдена, используем удаленную")
                remote_db.replace(local_db)
                if _sync_status_callback:
                    _sync_status_callback("Загружена БД с Яндекс.Диска")
                return True
            else:
                logger.info(
                    "Ни локальной, ни удаленной БД нет - работаем с пустой локальной"
                )
                if _sync_status_callback:
                    _sync_status_callback("Работаем с новой БД")
                return False

        # Локальная БД существует
        if not remote_db:
            # Нет удаленной БД - пытаемся загрузить локальную на диск
            logger.info(
                "Удаленная БД не найдена, пытаемся загрузить локальную на Яндекс.Диск"
            )
            success = _upload_merged_db(local_db)
            if success:
                if _sync_status_callback:
                    _sync_status_callback("Локальная БД загружена на Яндекс.Диск")
            else:
                logger.warning(
                    "Не удалось загрузить БД на Яндекс.Диск, работаем только локально"
                )
                if _sync_status_callback:
                    _sync_status_callback("Работаем только с локальной БД")
            # Возвращаем True, так как локальная БД есть и можем работать
            return True

        # КАРДИНАЛЬНОЕ ИЗМЕНЕНИЕ: НЕ объединяем при каждом запуске!
        # Просто заменяем локальную БД на удаленную, если удаленная новее
        logger.info("Заменяем локальную БД на более свежую с Яндекс.Диска")
        if _sync_status_callback:
            _sync_status_callback("Обновление локальной БД...")

        # Создаем бэкап локальной БД перед заменой
        from utils.backup import backup_sqlite_db

        backup_path = backup_sqlite_db(local_db)
        if backup_path:
            logger.info("Создан бэкап локальной БД: %s", backup_path)

        # Заменяем локальную БД на удаленную
        remote_db.replace(local_db)
        logger.info("Локальная БД заменена на удаленную")

        merge_success = True
        upload_success = True  # Не нужно загружать обратно

        # Удаляем временный файл (с принудительной очисткой)
        _safe_remove_temp_file(remote_db)

        if merge_success:
            logger.info("Синхронизация при запуске завершена успешно")
            if _sync_status_callback:
                _sync_status_callback(
                    "Синхронизация завершена успешно!"
                    if upload_success
                    else "Данные объединены (проблемы с загрузкой)"
                )
        else:
            logger.error("Ошибка синхронизации при запуске")
            if _sync_status_callback:
                _sync_status_callback("Ошибка синхронизации")

        # Обновляем UI если есть коллбэк
        _safe_callback(_ui_refresh_callback)

        # Возвращаем True если хотя бы объединение прошло успешно
        return merge_success

    except Exception as exc:
        logger.exception("Ошибка синхронизации при запуске: %s", exc)
        _safe_callback(_sync_status_callback, "Ошибка синхронизации")

        # Даже при ошибке синхронизации, если локальная БД есть, можем работать
        try:
            local_db = Path(get_current_db_path())
            return local_db.exists()
        except Exception:
            return False


def sync_periodic() -> bool:
    """
    Периодическая синхронизация

    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Периодическая синхронизация ===")

    if _sync_status_callback:
        _sync_status_callback("Синхронизация...")

    try:
        local_db = Path(get_current_db_path())
        if not local_db.exists():
            logger.warning("Локальная БД не найдена")
            return False

        # Скачиваем свежую версию
        remote_db = _download_fresh_db()
        if not remote_db:
            logger.info("Не удалось скачать свежую БД, загружаем локальную на диск")
            # Если не можем скачать, просто загружаем нашу версию
            return _upload_merged_db(local_db)

        # Объединяем базы
        merge_success = _merge_databases(local_db, remote_db)

        # Загружаем объединенную БД обратно на диск
        upload_success = _upload_merged_db(local_db)

        # НЕ проверяем повторно - избегаем зацикливания
        # Версия уже обновлена в _upload_merged_db

        # Удаляем временные файлы (с принудительной очисткой)
        _safe_remove_temp_file(remote_db)

        # Обновляем UI
        if _ui_refresh_callback:
            _ui_refresh_callback()

        if _sync_status_callback:
            _sync_status_callback(
                "Синхронизация завершена"
                if merge_success and upload_success
                else "Синхронизация с ошибками"
            )

        return merge_success and upload_success

    except Exception as exc:
        logger.exception("Ошибка периодической синхронизации: %s", exc)
        if _sync_status_callback:
            _sync_status_callback("Ошибка синхронизации")
        return False


def _sync_loop():
    """Основной цикл синхронизации"""
    logger.info("Запущен цикл автоматической синхронизации (каждые 30 минут)")

    while not _sync_stop_event.is_set():
        try:
            # Ждем 30 минут или сигнал остановки
            if _sync_stop_event.wait(timeout=30 * 60):  # 30 минут
                break

            # Выполняем периодическую синхронизацию
            sync_periodic()

        except Exception as exc:
            logger.exception("Ошибка в цикле синхронизации: %s", exc)
            # Небольшая пауза при ошибке
            time.sleep(60)


def set_sync_status_callback(callback: Optional[Callable[[str], None]]) -> None:
    """Установить callback для обновления статуса синхронизации"""
    global _sync_status_callback
    _sync_status_callback = callback


def start_auto_sync(
    ui_refresh_callback: Optional[Callable[[], None]] = None,
    sync_status_callback: Optional[Callable[[str], None]] = None,
):
    """
    Запустить автоматическую синхронизацию

    Args:
        ui_refresh_callback: Функция для обновления UI
        sync_status_callback: Функция для обновления статуса синхронизации
    """
    global _sync_thread, _ui_refresh_callback, _sync_status_callback

    _ui_refresh_callback = ui_refresh_callback
    _sync_status_callback = sync_status_callback

    # Останавливаем предыдущий поток если он есть
    stop_auto_sync()

    # Выполняем синхронизацию при запуске
    sync_on_startup()

    # Запускаем поток периодической синхронизации
    _sync_stop_event.clear()
    _sync_thread = threading.Thread(
        target=_sync_loop, daemon=True, name="AutoSyncThread"
    )
    _sync_thread.start()

    logger.info("Автоматическая синхронизация запущена")


def stop_auto_sync():
    """Остановить автоматическую синхронизацию"""
    global _sync_thread

    if _sync_thread and _sync_thread.is_alive():
        logger.info("Останавливаем автоматическую синхронизацию")
        _sync_stop_event.set()
        _sync_thread.join(timeout=5)
        _sync_thread = None


def force_sync() -> bool:
    """
    Принудительная синхронизация (для красной кнопки) - РЕАЛЬНОЕ объединение данных

    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Принудительная синхронизация ===")

    if _sync_status_callback:
        _sync_status_callback("Принудительная синхронизация...")

    try:
        local_db = Path(get_current_db_path())
        if not local_db.exists():
            logger.warning("Локальная БД не найдена")
            if _sync_status_callback:
                _sync_status_callback("Ошибка: локальная БД не найдена")
            return False

        client = _get_yadisk_client()
        if not client:
            logger.warning("Яндекс.Диск недоступен")
            if _sync_status_callback:
                _sync_status_callback("Ошибка: Яндекс.Диск недоступен")
            return False

        # Скачиваем свежую версию
        if _sync_status_callback:
            _sync_status_callback("Скачивание данных с облака...")
        remote_db = _download_fresh_db()

        if not remote_db:
            logger.info("Не удалось скачать свежую БД, загружаем локальную на диск")
            if _sync_status_callback:
                _sync_status_callback("Загрузка локальной БД в облако...")
            return _upload_merged_db(local_db)

        # РЕАЛЬНОЕ объединение баз (только при принудительной синхронизации)
        if _sync_status_callback:
            _sync_status_callback("Объединение данных...")
        merge_success = _merge_databases(local_db, remote_db)

        # Загружаем объединенную БД обратно на диск
        if _sync_status_callback:
            _sync_status_callback("Загрузка данных в облако...")
        upload_success = _upload_merged_db(local_db) if merge_success else False

        # Удаляем временные файлы
        _safe_remove_temp_file(remote_db)

        if merge_success:
            logger.info("Принудительная синхронизация завершена успешно")
            if _sync_status_callback:
                _sync_status_callback("Принудительная синхронизация завершена!")

        # Обновляем UI
        if _ui_refresh_callback:
            _ui_refresh_callback()

        return merge_success and upload_success

    except Exception as exc:
        logger.exception("Ошибка принудительной синхронизации: %s", exc)
        if _sync_status_callback:
            _sync_status_callback("Ошибка принудительной синхронизации")
        return False


def sync_on_shutdown() -> bool:
    """
    Синхронизация при выключении программы

    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Синхронизация при выключении ===")

    try:
        # Останавливаем автоматическую синхронизацию
        stop_auto_sync()

        # Выполняем финальную синхронизацию
        return sync_periodic()

    except Exception as exc:
        logger.exception("Ошибка синхронизации при выключении: %s", exc)
        return False


def show_yadisk_setup_dialog(parent_window=None) -> str:
    """
    Показать диалог настройки Яндекс.Диска при проблемах с токеном

    Returns: 'token_saved', 'offline' или 'cancelled'
    """
    try:
        if not parent_window:
            # Создаем временное окно
            import tkinter as tk

            parent_window = tk.Tk()
            parent_window.withdraw()

        from gui.yadisk_setup_dialog import YaDiskSetupDialog

        dialog = YaDiskSetupDialog(parent_window)
        parent_window.wait_window(dialog)

        return dialog.result or "cancelled"

    except Exception as exc:
        logger.exception("Ошибка показа диалога настройки Яндекс.Диска: %s", exc)
        return "cancelled"


def is_sync_running() -> bool:
    """Проверить, запущена ли автоматическая синхронизация"""
    return _sync_thread is not None and _sync_thread.is_alive()
