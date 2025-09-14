from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class NetworkDatabaseManager:
    """Менеджер для автоматического подключения к сетевой базе данных"""
    
    def __init__(self, network_path: str, username: str, password: str, db_filename: str):
        self.network_path = network_path
        self.username = username
        self.password = password
        self.db_filename = db_filename
        self.local_mount_point: Optional[Path] = None
    
    def connect_to_network_db(self) -> Optional[Path]:
        """
        Подключается к сетевой папке и возвращает путь к файлу БД.
        Возвращает None если подключение не удалось.
        """
        try:
            # Создаем локальную точку монтирования
            self.local_mount_point = self._create_mount_point()
            
            # Подключаемся к сетевой папке
            if self._mount_network_share():
                db_path = self.local_mount_point / self.db_filename
                if db_path.exists():
                    logger.info(f"Найдена сетевая БД: {db_path}")
                    return db_path
                else:
                    logger.warning(f"Файл БД не найден в сетевой папке: {db_path}")
                    return None
            else:
                logger.error("Не удалось подключиться к сетевой папке")
                return None
                
        except Exception as exc:
            logger.exception(f"Ошибка при подключении к сетевой БД: {exc}")
            return None
    
    def disconnect_from_network(self) -> None:
        """Отключается от сетевой папки"""
        if self.local_mount_point and self.local_mount_point.exists():
            try:
                if sys.platform == "win32":
                    # На Windows используем net use для отключения
                    subprocess.run(
                        ["net", "use", str(self.local_mount_point), "/delete", "/y"],
                        capture_output=True,
                        check=False
                    )
                else:
                    # На Linux/Mac используем umount
                    subprocess.run(
                        ["umount", str(self.local_mount_point)],
                        capture_output=True,
                        check=False
                    )
                logger.info(f"Отключились от сетевой папки: {self.local_mount_point}")
            except Exception as exc:
                logger.warning(f"Ошибка при отключении от сетевой папки: {exc}")
    
    def _create_mount_point(self) -> Path:
        """Создает локальную точку монтирования"""
        if sys.platform == "win32":
            # На Windows используем доступную букву диска
            for drive_letter in "ZYXWVUTSRQPONMLKJIHGFEDCBA":
                mount_point = Path(f"{drive_letter}:\\")
                if not mount_point.exists():
                    return mount_point
            raise RuntimeError("Не найдена доступная буква диска для монтирования")
        else:
            # На Linux/Mac создаем временную папку
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "sdelka_network"
            temp_dir.mkdir(exist_ok=True)
            return temp_dir
    
    def _mount_network_share(self) -> bool:
        """Монтирует сетевую папку"""
        try:
            if sys.platform == "win32":
                return self._mount_windows()
            else:
                return self._mount_unix()
        except Exception as exc:
            logger.error(f"Ошибка монтирования: {exc}")
            return False
    
    def _mount_windows(self) -> bool:
        """Монтирует сетевую папку на Windows"""
        try:
            # Сначала отключаем, если уже подключены
            subprocess.run(
                ["net", "use", str(self.local_mount_point), "/delete", "/y"],
                capture_output=True,
                check=False
            )
            
            # Подключаемся с учетными данными
            cmd = [
                "net", "use", str(self.local_mount_point),
                self.network_path,
                f"/user:{self.username}",
                self.password
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.info(f"Успешно подключились к {self.network_path} -> {self.local_mount_point}")
                return True
            else:
                logger.error(f"Ошибка подключения: {result.stderr}")
                return False
                
        except Exception as exc:
            logger.error(f"Ошибка Windows монтирования: {exc}")
            return False
    
    def _mount_unix(self) -> bool:
        """Монтирует сетевую папку на Linux/Mac"""
        try:
            # Для Unix систем используем cifs
            mount_cmd = [
                "sudo", "mount", "-t", "cifs",
                self.network_path,
                str(self.local_mount_point),
                "-o", f"username={self.username},password={self.password},uid={os.getuid()},gid={os.getgid()}"
            ]
            
            result = subprocess.run(mount_cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.info(f"Успешно подключились к {self.network_path} -> {self.local_mount_point}")
                return True
            else:
                logger.error(f"Ошибка подключения: {result.stderr}")
                return False
                
        except Exception as exc:
            logger.error(f"Ошибка Unix монтирования: {exc}")
            return False


def get_network_db_path() -> Optional[Path]:
    """
    Пытается подключиться к сетевой БД и возвращает путь к ней.
    Возвращает None если подключение не удалось.
    """
    network_manager = NetworkDatabaseManager(
        network_path=r"\\SRV3\sdelka",
        username="sdelka_user", 
        password="87654321",
        db_filename="base_sdelka_rmz.db"
    )
    
    return network_manager.connect_to_network_db()


def test_network_connection() -> bool:
    """Тестирует подключение к сетевой БД"""
    db_path = get_network_db_path()
    if db_path and db_path.exists():
        try:
            from db.sqlite import get_connection
            with get_connection(db_path) as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except Exception as exc:
            logger.error(f"Ошибка тестирования БД: {exc}")
            return False
    return False
