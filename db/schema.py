from __future__ import annotations

import logging
import sqlite3

from utils.text import normalize_for_search

logger = logging.getLogger(__name__)


DDL_TABLES_SQL = r"""
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    full_name_norm TEXT,
    dept TEXT,
    dept_norm TEXT,
    position TEXT,
    position_norm TEXT,
    personnel_no TEXT NOT NULL UNIQUE,
    personnel_no_norm TEXT,
    status TEXT NOT NULL DEFAULT 'Работает',
    status_norm TEXT
);

CREATE TABLE IF NOT EXISTS job_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_norm TEXT,
    unit TEXT NOT NULL,
    unit_norm TEXT,
    price NUMERIC NOT NULL CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_norm TEXT,
    product_no TEXT NOT NULL UNIQUE,
    product_no_norm TEXT,
    contract_id INTEGER,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    code_norm TEXT,
    name TEXT,
    name_norm TEXT,
    contract_type TEXT,
    contract_type_norm TEXT,
    executor TEXT,
    executor_norm TEXT,
    igk TEXT,
    contract_number TEXT,
    bank_account TEXT,
    start_date TEXT,
    end_date TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no INTEGER NOT NULL UNIQUE,
    date TEXT NOT NULL,
    contract_id INTEGER,
    total_amount NUMERIC NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS work_order_products (
    work_order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    PRIMARY KEY (work_order_id, product_id),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS work_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL,
    job_type_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),
    line_amount NUMERIC NOT NULL CHECK (line_amount >= 0),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (job_type_id) REFERENCES job_types(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS work_order_workers (
    work_order_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL DEFAULT 0,
    PRIMARY KEY (work_order_id, worker_id),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
 
CREATE TABLE IF NOT EXISTS contract_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    code TEXT,
    name TEXT,
    contract_type TEXT,
    executor TEXT,
    igk TEXT,
    contract_number TEXT,
    bank_account TEXT,
    start_date TEXT,
    end_date TEXT,
    description TEXT,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE CASCADE
);
"""

DDL_INDEXES = (
    (
        "idx_workers_full_name",
        "workers",
        ("full_name",),
        "CREATE INDEX IF NOT EXISTS idx_workers_full_name ON workers(full_name)",
    ),
    (
        "idx_workers_full_name_norm",
        "workers",
        ("full_name_norm",),
        "CREATE INDEX IF NOT EXISTS idx_workers_full_name_norm ON workers(full_name_norm)",
    ),
    (
        "idx_workers_dept_norm",
        "workers",
        ("dept_norm",),
        "CREATE INDEX IF NOT EXISTS idx_workers_dept_norm ON workers(dept_norm)",
    ),
    (
        "idx_workers_position_norm",
        "workers",
        ("position_norm",),
        "CREATE INDEX IF NOT EXISTS idx_workers_position_norm ON workers(position_norm)",
    ),
    (
        "idx_job_types_name",
        "job_types",
        ("name",),
        "CREATE INDEX IF NOT EXISTS idx_job_types_name ON job_types(name)",
    ),
    (
        "idx_job_types_name_norm",
        "job_types",
        ("name_norm",),
        "CREATE INDEX IF NOT EXISTS idx_job_types_name_norm ON job_types(name_norm)",
    ),
    (
        "idx_job_types_unit_norm",
        "job_types",
        ("unit_norm",),
        "CREATE INDEX IF NOT EXISTS idx_job_types_unit_norm ON job_types(unit_norm)",
    ),
    (
        "idx_products_name_no",
        "products",
        ("name", "product_no"),
        "CREATE INDEX IF NOT EXISTS idx_products_name_no ON products(name, product_no)",
    ),
    (
        "idx_products_name_norm",
        "products",
        ("name_norm",),
        "CREATE INDEX IF NOT EXISTS idx_products_name_norm ON products(name_norm)",
    ),
    (
        "idx_products_no_norm",
        "products",
        ("product_no_norm",),
        "CREATE INDEX IF NOT EXISTS idx_products_no_norm ON products(product_no_norm)",
    ),
    (
        "idx_products_contract",
        "products",
        ("contract_id",),
        "CREATE INDEX IF NOT EXISTS idx_products_contract ON products(contract_id)",
    ),
    (
        "idx_contracts_code",
        "contracts",
        ("code",),
        "CREATE INDEX IF NOT EXISTS idx_contracts_code ON contracts(code)",
    ),
    (
        "idx_contracts_code_norm",
        "contracts",
        ("code_norm",),
        "CREATE INDEX IF NOT EXISTS idx_contracts_code_norm ON contracts(code_norm)",
    ),
    (
        "idx_contracts_name_norm",
        "contracts",
        ("name_norm",),
        "CREATE INDEX IF NOT EXISTS idx_contracts_name_norm ON contracts(name_norm)",
    ),
    (
        "idx_contracts_type_norm",
        "contracts",
        ("contract_type_norm",),
        "CREATE INDEX IF NOT EXISTS idx_contracts_type_norm ON contracts(contract_type_norm)",
    ),
    (
        "idx_contracts_executor_norm",
        "contracts",
        ("executor_norm",),
        "CREATE INDEX IF NOT EXISTS idx_contracts_executor_norm ON contracts(executor_norm)",
    ),
    (
        "idx_work_orders_date",
        "work_orders",
        ("date",),
        "CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date)",
    ),
    (
        "idx_work_orders_order_no",
        "work_orders",
        ("order_no",),
        "CREATE INDEX IF NOT EXISTS idx_work_orders_order_no ON work_orders(order_no)",
    ),
    (
        "idx_wo_products_wo",
        "work_order_products",
        ("work_order_id",),
        "CREATE INDEX IF NOT EXISTS idx_wo_products_wo ON work_order_products(work_order_id)",
    ),
    (
        "idx_wo_products_product",
        "work_order_products",
        ("product_id",),
        "CREATE INDEX IF NOT EXISTS idx_wo_products_product ON work_order_products(product_id)",
    ),
    (
        "idx_contract_history_contract",
        "contract_history",
        ("contract_id",),
        "CREATE INDEX IF NOT EXISTS idx_contract_history_contract ON contract_history(contract_id)",
    ),
)


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create or migrate schema safely.

    - Создает таблицы, если отсутствуют
    - Мигрирует legacy-версии (workers без full_name -> с full_name)
    - Добавляет нормализованные колонки *_norm и заполняет их
    - Создает индексы только если существуют нужные колонки
    """
    conn.executescript(DDL_TABLES_SQL)

    migrate_workers_if_needed(conn)
    add_norm_columns_and_backfill(conn)
    ensure_products_contract_column(conn)
    ensure_contracts_extended_columns(conn)
    ensure_contract_history_table(conn)

    # Ensure new columns for worker allocations are present and backfilled
    ensure_work_order_workers_amounts(conn)

    create_indexes_if_possible(conn)

    logger.info("Схема БД инициализирована")


# --- migrations & helpers ---


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def get_table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]  # name in 2nd column


def migrate_workers_if_needed(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "workers"):
        return
    cols = set(get_table_columns(conn, "workers"))
    if "full_name" in cols and "personnel_no" in cols:
        return  # up-to-date

    legacy_name_col = None
    for candidate in ("name", "fio"):
        if candidate in cols:
            legacy_name_col = candidate
            break

    conn.execute("ALTER TABLE workers RENAME TO workers_old")
    conn.executescript(
        """
        CREATE TABLE workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE,
            full_name_norm TEXT,
            dept TEXT,
            dept_norm TEXT,
            position TEXT,
            position_norm TEXT,
            personnel_no TEXT NOT NULL UNIQUE,
            personnel_no_norm TEXT
        );
        """
    )

    if legacy_name_col:
        conn.execute(
            f"""
            INSERT INTO workers(full_name, dept, position, personnel_no)
            SELECT TRIM(COALESCE({legacy_name_col}, '')) AS full_name,
                   dept,
                   position,
                   personnel_no
            FROM workers_old
            WHERE {legacy_name_col} IS NOT NULL AND TRIM({legacy_name_col}) <> ''
            """
        )
    conn.execute("DROP TABLE workers_old")


def add_norm_columns_and_backfill(conn: sqlite3.Connection) -> None:
    def ensure_col(table: str, col: str) -> None:
        cols = set(get_table_columns(conn, table))
        if col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")

    # Ensure columns
    for table, cols in (
        (
            "workers",
            (
                "full_name_norm",
                "dept_norm",
                "position_norm",
                "personnel_no_norm",
                "status",
                "status_norm",
            ),
        ),
        ("job_types", ("name_norm", "unit_norm")),
        ("products", ("name_norm", "product_no_norm")),
        ("contracts", ("code_norm",)),
    ):
        if table_exists(conn, table):
            for c in cols:
                ensure_col(table, c)

    # Backfill with Python casefold for Unicode
    # Workers
    if table_exists(conn, "workers"):
        rows = conn.execute(
            "SELECT id, full_name, dept, position, personnel_no, status FROM workers"
        ).fetchall()
        for r in rows:
            status_val = r["status"] if r["status"] else "Работает"
            conn.execute(
                "UPDATE workers SET full_name_norm=?, dept_norm=?, position_norm=?, personnel_no_norm=?, status=?, status_norm=? WHERE id=?",
                (
                    normalize_for_search(r["full_name"]),
                    normalize_for_search(r["dept"]),
                    normalize_for_search(r["position"]),
                    normalize_for_search(r["personnel_no"]),
                    status_val,
                    normalize_for_search(status_val),
                    r["id"],
                ),
            )
    # job_types
    if table_exists(conn, "job_types"):
        rows = conn.execute("SELECT id, name, unit FROM job_types").fetchall()
        for r in rows:
            conn.execute(
                "UPDATE job_types SET name_norm=?, unit_norm=? WHERE id=?",
                (
                    normalize_for_search(r["name"]),
                    normalize_for_search(r["unit"]),
                    r["id"],
                ),
            )
    # products
    if table_exists(conn, "products"):
        rows = conn.execute("SELECT id, name, product_no FROM products").fetchall()
        for r in rows:
            conn.execute(
                "UPDATE products SET name_norm=?, product_no_norm=? WHERE id=?",
                (
                    normalize_for_search(r["name"]),
                    normalize_for_search(r["product_no"]),
                    r["id"],
                ),
            )
    # contracts
    if table_exists(conn, "contracts"):
        rows = conn.execute("SELECT id, code FROM contracts").fetchall()
        for r in rows:
            conn.execute(
                "UPDATE contracts SET code_norm=? WHERE id=?",
                (
                    normalize_for_search(r["code"]),
                    r["id"],
                ),
            )


def ensure_products_contract_column(conn: sqlite3.Connection) -> None:
    """Ensure products.contract_id exists for strict product-to-contract binding.

    - Adds INTEGER column if missing
    - Does not backfill; existing products remain without contract until set via UI/import
    """
    try:
        if not table_exists(conn, "products"):
            return
        cols = set(get_table_columns(conn, "products"))
        if "contract_id" not in cols:
            conn.execute("ALTER TABLE products ADD COLUMN contract_id INTEGER")
    except Exception as exc:  # noqa: TRY003
        logger.warning("ensure_products_contract_column failed: %s", exc)


def ensure_contracts_extended_columns(conn: sqlite3.Connection) -> None:
    """Добавляет расширенные колонки в таблицу contracts если их нет."""
    new_columns = [
        ("name", "TEXT"),
        ("name_norm", "TEXT"),
        ("contract_type", "TEXT"),
        ("contract_type_norm", "TEXT"),
        ("executor", "TEXT"),
        ("executor_norm", "TEXT"),
        ("igk", "TEXT"),
        ("contract_number", "TEXT"),
        ("bank_account", "TEXT"),
    ]

    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}")
            logger.info(f"Добавлена колонка {col_name} в таблицу contracts")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.debug(f"Колонка {col_name} уже существует в таблице contracts")
            else:
                logger.warning(f"Ошибка при добавлении колонки {col_name}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при добавлении колонки {col_name}: {e}")


def ensure_contract_history_table(conn: sqlite3.Connection) -> None:
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contract_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                code TEXT,
                name TEXT,
                contract_type TEXT,
                executor TEXT,
                igk TEXT,
                contract_number TEXT,
                bank_account TEXT,
                start_date TEXT,
                end_date TEXT,
                description TEXT,
                changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )
    except Exception as exc:
        logger.warning("ensure_contract_history_table failed: %s", exc)


def create_indexes_if_possible(conn: sqlite3.Connection) -> None:
    for idx_name, table, required_cols, create_sql in DDL_INDEXES:
        if not table_exists(conn, table):
            continue
        cols = set(get_table_columns(conn, table))
        if not set(required_cols).issubset(cols):
            logger.warning(
                "Пропуск создания индекса %s: нет колонок %s в %s",
                idx_name,
                required_cols,
                table,
            )
            continue
        try:
            conn.execute(create_sql)
        except sqlite3.OperationalError as exc:  # noqa: TRY003
            logger.warning("Не удалось создать индекс %s: %s", idx_name, exc)


def ensure_work_order_workers_amounts(conn: sqlite3.Connection) -> None:
    """Add amount column to work_order_workers and backfill equal shares if empty.

    - Adds column if missing
    - Backfills per worker amount = total_amount / count, rounding to 2 decimals and fixing remainder
    """
    try:
        if not table_exists(conn, "work_order_workers"):
            return
        cols = set(get_table_columns(conn, "work_order_workers"))
        if "amount" not in cols:
            conn.execute(
                "ALTER TABLE work_order_workers ADD COLUMN amount NUMERIC NOT NULL DEFAULT 0"
            )
        # For each work order, if all amounts are zero, distribute equally
        orders = conn.execute("SELECT id, total_amount FROM work_orders").fetchall()
        for o in orders:
            rows = conn.execute(
                "SELECT worker_id, amount FROM work_order_workers WHERE work_order_id=? ORDER BY worker_id",
                (o["id"],),
            ).fetchall()
            if not rows:
                continue
            if all((r["amount"] is None or float(r["amount"]) == 0.0) for r in rows):
                n = len(rows)
                total = (
                    float(o["total_amount"]) if o["total_amount"] is not None else 0.0
                )
                per = round((total / n) if n else 0.0, 2)
                amounts = [per] * n
                # Adjust last to correct rounding diff
                diff = round(total - round(per * n, 2), 2)
                if n > 0 and abs(diff) >= 0.01:
                    amounts[-1] = round(amounts[-1] + diff, 2)
                for idx, r in enumerate(rows):
                    conn.execute(
                        "UPDATE work_order_workers SET amount=? WHERE work_order_id=? AND worker_id=?",
                        (amounts[idx], o["id"], r["worker_id"]),
                    )
    except Exception as exc:  # safety: don't break startup
        logger.warning("ensure_work_order_workers_amounts failed: %s", exc)
