"""
File: app/core/database/migrations/migrator.py
Класс для управления миграциями базы данных.
"""

import os
import logging
import importlib.util
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from app.core.database.connections import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Модель данных для миграции."""
    version: int
    name: str
    path: Path
    applied_at: Optional[datetime] = None


class DatabaseMigrator:
    """Класс для управления миграциями базы данных."""

    MIGRATIONS_DIR = "migrations"
    MIGRATION_TABLE = "migrations"
    VERSION_PREFIX_LENGTH = 3  # Длина префикса версии в имени файла

    def __init__(self, db_manager: DatabaseManager, migrations_path: Optional[Path] = None):
        """
        Инициализация мигратора.

        Args:
            db_manager: Менеджер базы данных
            migrations_path: Путь к директории с миграциями
        """
        self.db_manager = db_manager
        self.migrations_path = migrations_path or Path(__file__).parent.parent / self.MIGRATIONS_DIR
        self._ensure_migrations_table()

    def get_available_migrations(self) -> List[Migration]:
        """Получает список доступных миграций."""
        if not self.migrations_path.exists():
            return []

        migrations = []
        for file_path in sorted(self.migrations_path.glob("*.py")):
            if file_path.name == "__init__.py":
                continue

            version_str = file_path.name[:self.VERSION_PREFIX_LENGTH]
            try:
                version = int(version_str)
            except ValueError:
                logger.warning(f"Пропущен файл миграции с недопустимым именем: {file_path.name}")
                continue

            migration = Migration(
                version=version,
                name=file_path.stem,
                path=file_path
            )
            migrations.append(migration)

        return migrations

    def get_applied_migrations(self) -> List[Migration]:
        """Получает список примененных миграций."""
        query = f"SELECT version, name, applied_at FROM {self.MIGRATION_TABLE} ORDER BY version"

        try:
            with self.db_manager.connect() as conn:
                cursor = conn.execute(query)
                results = cursor.fetchall()

                return [
                    Migration(
                        version=row["version"],
                        name=row["name"],
                        path=self.migrations_path / f"{row['name']}.py",
                        applied_at=datetime.fromisoformat(row["applied_at"])
                    )
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Ошибка получения списка примененных миграций: {e}", exc_info=True)
            return []

    def apply_migrations(self) -> bool:
        """Применяет все непримененные миграции."""
        available = self.get_available_migrations()
        applied = self.get_applied_migrations()

        # Создаем словарь примененных миграций для быстрого поиска
        applied_dict = {m.version: m for m in applied}

        success = True
        for migration in sorted(available, key=lambda m: m.version):
            if migration.version in applied_dict:
                logger.info(f"Миграция v{migration.version} уже применена")
                continue

            logger.info(f"Применяется миграция v{migration.version}: {migration.name}")
            result = self._apply_migration(migration)

            if not result:
                logger.error(f"Ошибка применения миграции v{migration.version}")
                success = False
                break

        return success

    def _apply_migration(self, migration: Migration) -> bool:
        """Применяет указанную миграцию."""
        try:
            # Загружаем модуль миграции
            spec = importlib.util.spec_from_file_location(migration.name, migration.path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Не удалось загрузить модуль миграции: {migration.path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Проверяем наличие необходимых функций
            if not hasattr(module, "upgrade") or not callable(module.upgrade):
                raise AttributeError("Миграция не содержит функцию upgrade")

            if not hasattr(module, "downgrade") or not callable(module.downgrade):
                raise AttributeError("Миграция не содержит функцию downgrade")

            # Начинаем транзакцию
            with self.db_manager.connect() as conn:
                try:
                    # Выполняем миграцию
                    module.upgrade(conn)

                    # Сохраняем информацию о примененной миграции
                    insert_query = f"""
                        INSERT INTO {self.MIGRATION_TABLE} (version, name, applied_at)
                        VALUES (?, ?, ?)
                    """
                    conn.execute(insert_query, (
                        migration.version,
                        migration.name,
                        datetime.now().isoformat()
                    ))

                    return True
                except Exception as e:
                    # Откатываем транзакцию в случае ошибки
                    conn.execute("ROLLBACK")
                    logger.error(f"Ошибка применения миграции v{migration.version}: {e}", exc_info=True)
                    return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при применении миграции v{migration.version}: {e}", exc_info=True)
            return False

    def rollback_migration(self, version: int) -> bool:
        """Откатывает указанную миграцию."""
        applied = self.get_applied_migrations()
        applied_dict = {m.version: m for m in applied}

        if version not in applied_dict:
            logger.warning(f"Миграция v{version} не найдена в списке примененных")
            return False

        migration = applied_dict[version]
        logger.info(f"Откатывается миграция v{version}: {migration.name}")

        try:
            # Загружаем модуль миграции
            spec = importlib.util.spec_from_file_location(migration.name, migration.path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Не удалось загрузить модуль миграции: {migration.path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Проверяем наличие необходимых функций
            if not hasattr(module, "downgrade") or not callable(module.downgrade):
                raise AttributeError("Миграция не содержит функцию downgrade")

            # Начинаем транзакцию
            with self.db_manager.connect() as conn:
                try:
                    # Выполняем откат
                    module.downgrade(conn)

                    # Удаляем информацию о примененной миграции
                    delete_query = f"""
                        DELETE FROM {self.MIGRATION_TABLE}
                        WHERE version = ?
                    """
                    conn.execute(delete_query, (version,))

                    return True
                except Exception as e:
                    # Откатываем транзакцию в случае ошибки
                    conn.execute("ROLLBACK")
                    logger.error(f"Ошибка отката миграции v{version}: {e}", exc_info=True)
                    return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при откате миграции v{version}: {e}", exc_info=True)
            return False

    def _ensure_migrations_table(self) -> None:
        """Создает таблицу миграций, если ее нет."""
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.MIGRATION_TABLE} (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """

        try:
            with self.db_manager.connect() as conn:
                conn.execute(create_table_sql)
                logger.debug("Таблица миграций проверена")
        except Exception as e:
            logger.error(f"Ошибка создания таблицы миграций: {e}", exc_info=True)