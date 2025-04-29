# File: app/core/database/migrations.py
"""
Модуль реализует систему миграций базы данных для последовательного
управления изменениями структуры базы данных.
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class Migration:
    """
    Представляет одну миграцию базы данных.

    Attributes:
        version: Версия миграции
        description: Описание миграции
        up_sql: SQL-запрос для применения миграции
        down_sql: SQL-запрос для отката миграции
    """

    def __init__(self, version: int, description: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql


class MigrationManager:
    """
    Управляет применением миграций к базе данных.

    Attributes:
        db_path: Путь к файлу базы данных
        migration_dir: Путь к каталогу с файлами миграций
    """

    def __init__(self, db_path: str, migration_dir: Optional[str] = None):
        self.db_path = Path(db_path).resolve()
        self.migration_dir = Path(migration_dir or self.db_path.parent / "migrations").resolve()
        self._ensure_migration_table()

    def _ensure_migration_table(self) -> None:
        """
        Создает таблицу миграций, если ее не существует.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        with self._connect() as conn:
            conn.execute(create_table_sql)

    def _connect(self) -> sqlite3.Connection:
        """
        Создает соединение с базой данных.

        Returns:
            Соединение с базой данных
        """
        return sqlite3.connect(self.db_path)

    def get_applied_versions(self) -> List[int]:
        """
        Получает список примененных версий миграций.

        Returns:
            Список номеров версий
        """
        with self._connect() as conn:
            cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]

    def get_available_migrations(self) -> List[Migration]:
        """
        Получает список доступных миграций из каталога.

        Returns:
            Список объектов Migration
        """
        migrations = []

        if not self.migration_dir.exists():
            return migrations

        for file in sorted(self.migration_dir.glob("*.sql")):
            try:
                version_str, desc_part = file.stem.split("_", 1)
                version = int(version_str)
                description = desc_part.replace("_", " ")

                content = file.read_text(encoding="utf-8")
                parts = content.split("-- DOWN:")
                up_sql = parts[0].strip()
                down_sql = parts[1].strip() if len(parts) > 1 else ""

                migrations.append(Migration(version, description, up_sql, down_sql))

            except Exception as e:
                logger.warning(f"Не удалось прочитать миграцию {file}: {e}")

        return sorted(migrations, key=lambda m: m.version)

    def apply_migrations(self) -> List[Tuple[int, str]]:
        """
        Применяет непримененные миграции.

        Returns:
            Список примененных миграций (номер версии, описание)
        """
        applied_versions = self.get_applied_versions()
        available_migrations = self.get_available_migrations()

        migrations_to_apply = [
            m for m in available_migrations
            if m.version not in applied_versions and m.version > 0
        ]

        applied = []

        with self._connect() as conn:
            for migration in migrations_to_apply:
                try:
                    logger.info(f"Применяется миграция v{migration.version}: {migration.description}")

                    with conn:  # Транзакция
                        conn.executescript(migration.up_sql)
                        conn.execute(
                            "INSERT INTO schema_migrations (version) VALUES (?)",
                            (migration.version,)
                        )

                    applied.append((migration.version, migration.description))
                    logger.info(f"Миграция v{migration.version} успешно применена")

                except Exception as e:
                    logger.error(f"Ошибка применения миграции v{migration.version}: {e}", exc_info=True)
                    raise

        return applied

    def rollback_migration(self, version: int) -> bool:
        """
        Откатывает миграцию до указанной версии.

        Args:
            version: Версия, к которой нужно откатиться

        Returns:
            Успех операции
        """
        applied_versions = self.get_applied_versions()

        if version >= max(applied_versions, default=0):
            logger.warning("Невозможно откатиться к версии, которая больше текущей")
            return False

        migrations_to_rollback = [
            m for m in self.get_available_migrations()
            if m.version in applied_versions and m.version > version
        ]

        with self._connect() as conn:
            for migration in reversed(migrations_to_rollback):
                try:
                    logger.info(f"Откат миграции v{migration.version}: {migration.description}")

                    with conn:  # Транзакция
                        if migration.down_sql:
                            conn.executescript(migration.down_sql)

                        conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))

                    logger.info(f"Миграция v{migration.version} успешно откачена")

                except Exception as e:
                    logger.error(f"Ошибка отката миграции v{migration.version}: {e}", exc_info=True)
                    return False

        return True


if __name__ == "__main__":
    # Пример использования
    import logging.config

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    })

    # Создаем директорию для миграций с примером
    migration_dir = Path("migrations")
    migration_dir.mkdir(exist_ok=True)

    example_sql = """
        -- UP:
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- DOWN:
        DROP TABLE IF EXISTS users;
        """

    (migration_dir / "001_create_users_table.sql").write_text(example_sql, encoding="utf-8")

    # Применяем миграции
    migrator = MigrationManager("test.db", str(migration_dir))
    applied = migrator.apply_migrations()
    print(f"Применено миграций: {len(applied)}")
    print("Список:", applied)