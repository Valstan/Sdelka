"""
Модуль содержит SQL-запросы для работы с базой данных.
Здесь определены запросы для создания таблиц, добавления, обновления и получения данных.
"""
from typing import Tuple

# Запросы для создания таблиц
CREATE_WORKERS_TABLE = """
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    position TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_WORK_TYPES_TABLE = """
CREATE TABLE IF NOT EXISTS work_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_number TEXT NOT NULL,
    product_type TEXT NOT NULL,
    additional_number TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CONTRACTS_TABLE = """
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_number TEXT NOT NULL UNIQUE,
    description TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_WORK_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS work_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number INTEGER NOT NULL,
    card_date DATE NOT NULL,
    product_id INTEGER,
    contract_id INTEGER,
    total_amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (contract_id) REFERENCES contracts (id)
);
"""

CREATE_WORK_CARD_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS work_card_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_card_id INTEGER NOT NULL,
    work_type_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_card_id) REFERENCES work_cards (id),
    FOREIGN KEY (work_type_id) REFERENCES work_types (id)
);
"""

CREATE_WORK_CARD_WORKERS_TABLE = """
CREATE TABLE IF NOT EXISTS work_card_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_card_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_card_id) REFERENCES work_cards (id),
    FOREIGN KEY (worker_id) REFERENCES workers (id)
);
"""

# Список всех запросов по созданию таблиц
CREATE_TABLES_QUERIES = [
    CREATE_WORKERS_TABLE,
    CREATE_WORK_TYPES_TABLE,
    CREATE_PRODUCTS_TABLE,
    CREATE_CONTRACTS_TABLE,
    CREATE_WORK_CARDS_TABLE,
    CREATE_WORK_CARD_ITEMS_TABLE,
    CREATE_WORK_CARD_WORKERS_TABLE
]

# Запросы для работы с работниками
GET_ALL_WORKERS = "SELECT * FROM workers ORDER BY last_name"
GET_WORKER_BY_ID = "SELECT * FROM workers WHERE id = ?"
SEARCH_WORKERS = "SELECT * FROM workers WHERE last_name LIKE ? || '%' ORDER BY last_name LIMIT 10"

# Запросы для работы с видами работ
GET_ALL_WORK_TYPES = "SELECT * FROM work_types ORDER BY name"
GET_WORK_TYPE_BY_ID = "SELECT * FROM work_types WHERE id = ?"
SEARCH_WORK_TYPES = "SELECT * FROM work_types WHERE name LIKE ? || '%' ORDER BY name LIMIT 10"

# Запросы для работы с изделиями
GET_ALL_PRODUCTS = "SELECT * FROM products ORDER BY product_number"
GET_PRODUCT_BY_ID = "SELECT * FROM products WHERE id = ?"
SEARCH_PRODUCTS = """
SELECT * FROM products 
WHERE product_number LIKE ? || '%' OR product_type LIKE ? || '%' 
ORDER BY product_number LIMIT 10
"""

# Запросы для работы с контрактами
GET_ALL_CONTRACTS = "SELECT * FROM contracts ORDER BY contract_number"
GET_CONTRACT_BY_ID = "SELECT * FROM contracts WHERE id = ?"
SEARCH_CONTRACTS = "SELECT * FROM contracts WHERE contract_number LIKE ? || '%' ORDER BY contract_number LIMIT 10"

# Запросы для работы с карточками работ
GET_ALL_WORK_CARDS = """
SELECT wc.*, p.product_number, p.product_type, c.contract_number
FROM work_cards wc
LEFT JOIN products p ON wc.product_id = p.id
LEFT JOIN contracts c ON wc.contract_id = c.id
ORDER BY wc.card_number DESC
"""
GET_WORK_CARD_BY_ID = """
SELECT wc.*, p.product_number, p.product_type, c.contract_number
FROM work_cards wc
LEFT JOIN products p ON wc.product_id = p.id
LEFT JOIN contracts c ON wc.contract_id = c.id
WHERE wc.id = ?
"""
ADD_WORK_CARD = """
INSERT INTO work_cards (card_number, card_date, product_id, contract_id, total_amount)
VALUES (?, ?, ?, ?, ?)
"""
UPDATE_WORK_CARD = """
UPDATE work_cards 
SET card_date = ?, product_id = ?, contract_id = ?, total_amount = ?
WHERE id = ?
"""
DELETE_WORK_CARD = "DELETE FROM work_cards WHERE id = ?"

# Запросы для работы с элементами карточек работ
GET_WORK_CARD_ITEMS = "SELECT * FROM work_card_items WHERE work_card_id = ?"
ADD_WORK_CARD_ITEM = """
INSERT INTO work_card_items (work_card_id, work_type_id, quantity, amount)
VALUES (?, ?, ?, ?)
"""
UPDATE_WORK_CARD_ITEM = """
UPDATE work_card_items 
SET work_type_id = ?, quantity = ?, amount = ?
WHERE id = ?
"""
DELETE_WORK_CARD_ITEM = "DELETE FROM work_card_items WHERE id = ?"

# Запросы для работы с работниками в карточках
GET_WORK_CARD_WORKERS = "SELECT * FROM work_card_workers WHERE work_card_id = ?"
ADD_WORK_CARD_WORKER = """
INSERT INTO work_card_workers (work_card_id, worker_id, amount)
VALUES (?, ?, ?)
"""
UPDATE_WORK_CARD_WORKER = """
UPDATE work_card_workers 
SET worker_id = ?, amount = ?
WHERE id = ?
"""
DELETE_WORK_CARD_WORKER = "DELETE FROM work_card_workers WHERE id = ?"

# Запросы для формирования отчетов
REPORT_BY_WORKER_BASE = """
SELECT 
    w.last_name, w.first_name, w.middle_name,
    wc.card_date,
    wti.id AS work_item_id,
    wt.name AS work_name,
    wti.quantity,
    wt.price,
    wti.amount,
    p.product_number, p.product_type, p.additional_number AS product_additional,
    c.contract_number
FROM work_card_workers wcw
JOIN workers w ON wcw.worker_id = w.id
JOIN work_cards wc ON wcw.work_card_id = wc.id
JOIN work_card_items wti ON wti.work_card_id = wc.id
JOIN work_types wt ON wti.work_type_id = wt.id
LEFT JOIN products p ON wc.product_id = p.id
LEFT JOIN contracts c ON wc.contract_id = c.id
WHERE wc.card_date BETWEEN ? AND ?
"""

def get_report_query(params: dict) -> Tuple[str, list]:
    """
    Генерирует SQL-запрос для отчета с учетом фильтров.

    Args:
        params: Словарь с параметрами фильтрации

    Returns:
        Кортеж (SQL-запрос, список параметров)
    """
    query = REPORT_BY_WORKER_BASE
    conditions = []
    parameters = []
    params_count = 0

    # Добавляем условия для фильтров
    if params.get('worker_id') and params['worker_id'] != 0:
        conditions.append("w.id = ?")
        parameters.append(params['worker_id'])
        params_count += 1

    if params.get('work_type_id') and params['work_type_id'] != 0:
        conditions.append("wt.id = ?")
        parameters.append(params['work_type_id'])
        params_count += 1

    if params.get('product_id') and params['product_id'] != 0:
        conditions.append("p.id = ?")
        parameters.append(params['product_id'])
        params_count += 1

    if params.get('contract_id') and params['contract_id'] != 0:
        conditions.append("c.id = ?")
        parameters.append(params['contract_id'])
        params_count += 1

    # Добавляем условия к основному запросу
    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY w.last_name, wc.card_date"

    # Возвращаем сформированный запрос и параметры
    return query, parameters