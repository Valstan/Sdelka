"""
Миграция для изменения структуры таблицы work_orders:
- Удаление поля product_id (связь теперь через work_order_products)
- Изменение contract_id с NOT NULL на NULL (контракт может подтягиваться автоматически)
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def migrate_work_orders_structure(conn: sqlite3.Connection) -> None:
    """Мигрирует структуру таблицы work_orders для поддержки множественных изделий"""

    # Проверяем, нужна ли миграция
    cursor = conn.execute("PRAGMA table_info(work_orders)")
    columns = [row[1] for row in cursor.fetchall()]

    if "product_id" not in columns:
        logger.info("Миграция work_orders уже выполнена")
        return

    logger.info("Начинаем миграцию таблицы work_orders...")

    # Создаем временную таблицу с новой структурой
    conn.execute(
        """
        CREATE TABLE work_orders_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no INTEGER NOT NULL UNIQUE,
            date TEXT NOT NULL,
            contract_id INTEGER,
            total_amount NUMERIC NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE SET NULL
        )
    """
    )

    # Копируем данные из старой таблицы
    conn.execute(
        """
        INSERT INTO work_orders_new (id, order_no, date, contract_id, total_amount)
        SELECT id, order_no, date, contract_id, total_amount
        FROM work_orders
    """
    )

    # Удаляем старую таблицу
    conn.execute("DROP TABLE work_orders")

    # Переименовываем новую таблицу
    conn.execute("ALTER TABLE work_orders_new RENAME TO work_orders")

    # Восстанавливаем индексы
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_orders_order_no ON work_orders(order_no)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_orders_contract_id ON work_orders(contract_id)"
    )

    logger.info("Миграция таблицы work_orders завершена")


def migrate_existing_product_links(conn: sqlite3.Connection) -> None:
    """Мигрирует существующие связи product_id из work_orders в work_order_products"""

    # Проверяем, есть ли данные для миграции
    cursor = conn.execute(
        "SELECT COUNT(*) FROM work_orders WHERE product_id IS NOT NULL"
    )
    count = cursor.fetchone()[0]

    if count == 0:
        logger.info("Нет данных для миграции в work_order_products")
        return

    logger.info(f"Мигрируем {count} связей product_id в work_order_products...")

    # Добавляем связи в work_order_products
    conn.execute(
        """
        INSERT OR IGNORE INTO work_order_products (work_order_id, product_id)
        SELECT id, product_id
        FROM work_orders
        WHERE product_id IS NOT NULL
    """
    )

    logger.info("Миграция связей product_id завершена")


def run_migration(conn: sqlite3.Connection) -> None:
    """Выполняет полную миграцию структуры work_orders"""
    try:
        migrate_work_orders_structure(conn)
        migrate_existing_product_links(conn)
        conn.commit()
        logger.info("Миграция work_orders успешно завершена")
    except Exception as exc:
        conn.rollback()
        logger.error(f"Ошибка миграции work_orders: {exc}")
        raise


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Добавляем корневую директорию в путь
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from db.sqlite import get_connection

    with get_connection() as conn:
        run_migration(conn)
