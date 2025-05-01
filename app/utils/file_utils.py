"""
File: app/utils/file_utils.py
Утилиты для работы с файлами и директориями.
"""

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DATE_FORMATS

logger = logging.getLogger(__name__)


def create_directory(path: str) -> bool:
    """
    Создает директорию по указанному пути, если она не существует.

    Args:
        path: Путь к директории

    Returns:
        True если директория создана или существует, иначе False
    """
    try:
        Path(path).mkdir(exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка создания директории {path}: {e}", exc_info=True)
        return False


def read_file(file_path: str) -> Optional[str]:
    """
    Читает содержимое файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Содержимое файла или None в случае ошибки
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}", exc_info=True)
        return None


def write_file(file_path: str, content: str) -> bool:
    """
    Записывает содержимое в файл.

    Args:
        file_path: Путь к файлу
        content: Содержимое для записи

    Returns:
        True если запись успешна, иначе False
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в файл {file_path}: {e}", exc_info=True)
        return False


def file_exists(file_path: str) -> bool:
    """
    Проверяет, существует ли файл.

    Args:
        file_path: Путь к файлу

    Returns:
        True если файл существует
    """
    return os.path.exists(file_path)


def get_file_size(file_path: str) -> int:
    """
    Возвращает размер файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Размер файла в байтах
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return -1


def copy_file(source: str, destination: str) -> bool:
    """
    Копирует файл из источника в назначение.

    Args:
        source: Путь к исходному файлу
        destination: Путь к целевому файлу

    Returns:
        True если копирование успешное, иначе False
    """
    try:
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"Ошибка копирования файла: {e}", exc_info=True)
        return False


def backup_file(file_path: str, backup_dir: str = "backups", max_backups: int = 20) -> bool:
    """
    Создает резервную копию файла.

    Args:
        file_path: Путь к файлу
        backup_dir: Директория для резервных копий
        max_backups: Максимальное количество резервных копий

    Returns:
        True если резервная копия создана
    """
    try:
        file_path = Path(file_path)
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)

        # Генерируем имя резервной копии
        timestamp = datetime.now().strftime(DATE_FORMATS["export"])
        backup_file = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        # Копируем файл
        shutil.copy2(file_path, backup_file)
        logger.info(f"Создана резервная копия: {backup_file}")

        # Очищаем старые резервы
        self._cleanup_old_backups(backup_dir, max_backups)

        return True
    except Exception as e:
        logger.error(f"Ошибка создания резервной копии: {e}", exc_info=True)
        return False


def _cleanup_old_backups(self, backup_dir: Path, max_backups: int) -> None:
    """
    Очищает старые резервные копии.

    Args:
        backup_dir: Директория резервных копий
        max_backups: Максимальное количество копий
    """
    backups = sorted(
        (f for f in backup_dir.glob(f"*_{DATE_FORMATS['export']}*")),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for old_backup in backups[max_backups:]:
        try:
            old_backup.unlink()
            logger.info(f"Удалена старая резервная копия: {old_backup}")
        except Exception as e:
            logger.error(f"Ошибка удаления резервной копии: {e}", exc_info=True)