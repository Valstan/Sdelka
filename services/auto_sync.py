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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from config.settings import CONFIG
from db.sqlite import get_connection
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


class SyncConflictResolver:
    """Класс для разрешения конфликтов при объединении баз данных"""
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    
    def resolve_conflict(self, conflict_type: str, local_data: Dict[str, Any], 
                        remote_data: Dict[str, Any]) -> str:
        """
        Разрешение конфликта с участием пользователя
        
        Returns: 'local', 'remote', 'merge' или 'skip'
        """
        if not self.parent_window:
            # Автоматическое разрешение: приоритет удаленным данным
            logger.info(f"Авторазрешение конфликта {conflict_type}: выбираем remote")
            return 'remote'
        
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
                message + "\n\nДа - использовать удаленные данные\nНет - оставить локальные\nОтмена - пропустить"
            )
            
            if result is True:
                return 'remote'
            elif result is False:
                return 'local'
            else:
                return 'skip'
                
        except Exception as exc:
            logger.exception("Ошибка при разрешении конфликта: %s", exc)
            return 'remote'  # Безопасный выбор по умолчанию


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
            
        return YaDiskClient(YaDiskConfig(oauth_token=token, remote_dir=remote_dir))
        
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
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
            return True
            
    except Exception:
        return False


def _merge_databases(local_db: Path, remote_db: Path, 
                    conflict_resolver: Optional[SyncConflictResolver] = None) -> bool:
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
        
        logger.info("Объединение завершено: refs_upserts=%d, orders_merged=%d", 
                   refs_upserts, orders_merged)
        
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


def _check_for_newer_remote_version() -> bool:
    """Проверить, появилась ли более новая версия на Яндекс.Диске"""
    client = _get_yadisk_client()
    if not client:
        return False
    
    try:
        # Получаем информацию о файле на диске
        remote_path = f"{client.cfg.remote_dir}/sdelka_base.db"
        
        # Для простоты будем считать, что если файл существует, то он потенциально новее
        # В будущем можно добавить сравнение по времени модификации
        return client._resource_exists(remote_path)
        
    except Exception as exc:
        logger.exception("Ошибка проверки новой версии: %s", exc)
        return False


def sync_on_startup() -> bool:
    """
    Синхронизация при запуске программы - всегда объединяем локальную и удаленную БД
    
    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Синхронизация при запуске ===")
    
    if _sync_status_callback:
        _sync_status_callback("Синхронизация при запуске...")
    
    try:
        local_db = Path(get_current_db_path())
        
        # Скачиваем свежую версию с Яндекс.Диска
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
                logger.info("Ни локальной, ни удаленной БД нет - работаем с пустой локальной")
                if _sync_status_callback:
                    _sync_status_callback("Работаем с новой БД")
                return False
        
        # Локальная БД существует
        if not remote_db:
            # Нет удаленной БД - загружаем локальную на диск
            logger.info("Удаленная БД не найдена, загружаем локальную на Яндекс.Диск")
            success = _upload_merged_db(local_db)
            if _sync_status_callback:
                _sync_status_callback("Локальная БД загружена на Яндекс.Диск" if success else "Ошибка загрузки на Яндекс.Диск")
            return success
        
        # Есть и локальная, и удаленная БД - объединяем их
        logger.info("Объединяем локальную и удаленную БД")
        merge_success = _merge_databases(local_db, remote_db)
        
        # Загружаем объединенную БД обратно на диск
        upload_success = _upload_merged_db(local_db) if merge_success else False
        
        # Удаляем временный файл
        remote_db.unlink(missing_ok=True)
        
        if merge_success and upload_success:
            logger.info("Синхронизация при запуске завершена успешно")
            if _sync_status_callback:
                _sync_status_callback("Данные синхронизированы")
        else:
            logger.error("Ошибка синхронизации при запуске")
            if _sync_status_callback:
                _sync_status_callback("Ошибка синхронизации")
        
        # Обновляем UI если есть коллбэк
        if _ui_refresh_callback:
            _ui_refresh_callback()
        
        return merge_success and upload_success
        
    except Exception as exc:
        logger.exception("Ошибка синхронизации при запуске: %s", exc)
        if _sync_status_callback:
            _sync_status_callback("Ошибка синхронизации")
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
        
        # Проверяем, не появилась ли еще более новая версия
        if upload_success and _check_for_newer_remote_version():
            logger.info("Обнаружена еще более новая версия, повторяем синхронизацию")
            # Рекурсивно повторяем процесс (но только один раз)
            remote_db2 = _download_fresh_db()
            if remote_db2:
                _merge_databases(local_db, remote_db2)
                _upload_merged_db(local_db)
                remote_db2.unlink(missing_ok=True)
        
        # Удаляем временные файлы
        remote_db.unlink(missing_ok=True)
        
        # Обновляем UI
        if _ui_refresh_callback:
            _ui_refresh_callback()
        
        if _sync_status_callback:
            _sync_status_callback("Синхронизация завершена" if merge_success and upload_success else "Синхронизация с ошибками")
        
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


def start_auto_sync(ui_refresh_callback: Optional[Callable[[], None]] = None,
                   sync_status_callback: Optional[Callable[[str], None]] = None):
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
        target=_sync_loop,
        daemon=True,
        name="AutoSyncThread"
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
    Принудительная синхронизация (для красной кнопки)
    
    Returns: True если синхронизация прошла успешно
    """
    logger.info("=== Принудительная синхронизация ===")
    return sync_periodic()


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


def is_sync_running() -> bool:
    """Проверить, запущена ли автоматическая синхронизация"""
    return _sync_thread is not None and _sync_thread.is_alive()
