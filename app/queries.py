# File: app/queries.py
"""
Модуль содержит SQL-запросы для работы с базой данных.
Здесь определены запросы для создания таблиц, добавления, обновления и получения данных.
"""

from typing import Tuple

# Запросы для создания таблиц
CREATE_WORKERS_TABLE = """CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    workshop_number TEXT,
    position TEXT,
    employee_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_WORK_TYPES_TABLE = """CREATE TABLE IF NOT EXISTS work_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    unit TEXT,
    price REAL NOT NULL,
    valid_from DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_PRODUCTS_TABLE = """CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_number TEXT UNIQUE NOT NULL,
    product_type TEXT,
    additional_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_CONTRACTS_TABLE = """CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_number TEXT UNIQUE NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_WORK_CARDS_TABLE = """CREATE TABLE IF NOT EXISTS work_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number TEXT UNIQUE NOT NULL,
    card_date DATE DEFAULT CURRENT_DATE,
    product_id INTEGER,
    contract_id INTEGER,
    total_amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
);"""

CREATE_WORK_CARD_ITEMS_TABLE = """CREATE TABLE IF NOT EXISTS work_card_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_card_id INTEGER,
    work_type_id INTEGER,
    quantity REAL,
    amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(work_card_id) REFERENCES work_cards(id),
    FOREIGN KEY(work_type_id) REFERENCES work_types(id)
);"""

CREATE_WORK_CARD_WORKERS_TABLE = """CREATE TABLE IF NOT EXISTS work_card_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_card_id INTEGER,
    worker_id INTEGER,
    amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(work_card_id, worker_id),
    FOREIGN KEY(work_card_id) REFERENCES work_cards(id),
    FOREIGN KEY(worker_id) REFERENCES workers(id)
);"""

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

# Запросы для работы со списком рабочих
GET_ALL_WORKERS = "SELECT * FROM workers ORDER BY last_name"
GET_WORKER_BY_ID = "SELECT * FROM workers WHERE id = ?"
SEARCH_WORKERS = "SELECT * FROM workers WHERE last_name LIKE ? ORDER BY last_name"
ADD_WORKER = """INSERT INTO workers (
    last_name, first_name, middle_name, workshop_number, position, employee_id
) VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_WORKER = """UPDATE workers SET
    last_name = ?, first_name = ?, middle_name = ?, 
    workshop_number = ?, position = ?, employee_id = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_WORKER = "DELETE FROM workers WHERE id = ?"

# Запросы для работы с видами работ
GET_ALL_WORK_TYPES = "SELECT * FROM work_types ORDER BY name"
GET_WORK_TYPE_BY_ID = "SELECT * FROM work_types WHERE id = ?"
SEARCH_WORK_TYPES = "SELECT * FROM work_types WHERE name LIKE ? ORDER BY name"
ADD_WORK_TYPE = "INSERT INTO work_types (name, unit, price) VALUES (?, ?, ?)"
UPDATE_WORK_TYPE = """UPDATE work_types SET
    name = ?, unit = ?, price = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_WORK_TYPE = "DELETE FROM work_types WHERE id = ?"

# Запросы для работы с изделиями
GET_ALL_PRODUCTS = "SELECT * FROM products ORDER BY product_number"
GET_PRODUCT_BY_ID = "SELECT * FROM products WHERE id = ?"
SEARCH_PRODUCTS = "SELECT * FROM products WHERE product_number LIKE ? OR product_type LIKE ? ORDER BY product_number"
ADD_PRODUCT = "INSERT INTO products (product_number, product_type, additional_number) VALUES (?, ?, ?)"
UPDATE_PRODUCT = """UPDATE products SET
    product_number = ?, product_type = ?, additional_number = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_PRODUCT = "DELETE FROM products WHERE id = ?"

# Запросы для работы с контрактами
GET_ALL_CONTRACTS = "SELECT * FROM contracts ORDER BY contract_number"
GET_CONTRACT_BY_ID = "SELECT * FROM contracts WHERE id = ?"
SEARCH_CONTRACTS = "SELECT * FROM contracts WHERE contract_number LIKE ? ORDER BY contract_number"
ADD_CONTRACT = "INSERT INTO contracts (contract_number, start_date, end_date, description) VALUES (?, ?, ?, ?)"
UPDATE_CONTRACT = """UPDATE contracts SET
    contract_number = ?, start_date = ?, end_date = ?, description = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_CONTRACT = "DELETE FROM contracts WHERE id = ?"

# Запросы для работы с карточками работ
GET_WORK_CARD_BY_ID = """SELECT wc.*, p.product_number, p.product_type, c.contract_number 
                        FROM work_cards wc
                        LEFT JOIN products p ON wc.product_id = p.id
                        LEFT JOIN contracts c ON wc.contract_id = c.id
                        WHERE wc.id = ?"""
GET_ALL_WORK_CARDS = """SELECT wc.*, p.product_number, p.product_type, c.contract_number 
                       FROM work_cards wc
                       LEFT JOIN products p ON wc.product_id = p.id
                       LEFT JOIN contracts c ON wc.contract_id = c.id
                       ORDER BY wc.card_date DESC"""
ADD_WORK_CARD = """INSERT INTO work_cards (card_number, card_date, product_id, contract_id, total_amount) 
                  VALUES (?, ?, ?, ?, ?)"""
UPDATE_WORK_CARD = """UPDATE work_cards SET
    card_date = ?, product_id = ?, contract_id = ?, total_amount = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_WORK_CARD = "DELETE FROM work_cards WHERE id = ?"

# Запросы для работы с элементами карточек работ
GET_WORK_CARD_ITEMS = "SELECT * FROM work_card_items WHERE work_card_id = ?"
ADD_WORK_CARD_ITEM = """INSERT INTO work_card_items (work_card_id, work_type_id, quantity, amount) 
                      VALUES (?, ?, ?, ?)"""
UPDATE_WORK_CARD_ITEM = """UPDATE work_card_items SET
    work_type_id = ?, quantity = ?, amount = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = ?"""
DELETE_WORK_CARD_ITEM = "DELETE FROM work_card_items WHERE id = ?"

# Запросы для работы с работниками в карточках
GET_WORK_CARD_WORKERS = "SELECT * FROM work_card_workers WHERE work_card_id = ?"
ADD_WORK_CARD_WORKER = """INSERT INTO work_card_workers (work_card_id, worker_id, amount) 
                        VALUES (?, ?, ?)"""
UPDATE_WORK_CARD_WORKER = """UPDATE work_card_workers SET
    amount = ?,
    updated_at = CURRENT_TIMESTAMP
    WHERE work_card_id = ? AND worker_id = ?"""
DELETE_WORK_CARD_WORKER = "DELETE FROM work_card_workers WHERE work_card_id = ? AND worker_id = ?"

# Запросы для получения данных для отчетов
GET_REPORT_DATA = """SELECT 
    w.last_name, w.first_name, w.middle_name,
    wc.card_number, wc.card_date,
    wci.id AS work_item_id, wci.quantity, wci.amount,
    wt.name AS work_name,
    p.product_number, p.product_type,
    c.contract_number,
    p.id AS product_id,
    c.id AS contract_id,
    wcw.amount AS worker_amount
FROM work_cards wc
LEFT JOIN work_card_items wci ON wc.id = wci.work_card_id
LEFT JOIN work_types wt ON wci.work_type_id = wt.id
LEFT JOIN work_card_workers wcw ON wc.id = wcw.work_card_id
LEFT JOIN workers w ON wcw.worker_id = w.id
LEFT JOIN products p ON wc.product_id = p.id
LEFT JOIN contracts c ON wc.contract_id = c.id
WHERE wc.card_date BETWEEN ? AND ?"""