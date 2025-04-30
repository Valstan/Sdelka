-- File: app/core/database/queries/contracts.sql
"""
SQL-запросы для работы с контрактами.
"""

-- Создание таблицы contracts
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_number TEXT UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(start_date <= end_date)
);

-- Новая таблица work_cards (наряды)
CREATE TABLE IF NOT EXISTS work_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number TEXT UNIQUE NOT NULL,
    card_date DATE NOT NULL DEFAULT CURRENT_DATE,
    product_id INTEGER,
    contract_id INTEGER,
    total_amount REAL DEFAULT 0,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
);

-- Таблица работников наряда
CREATE TABLE IF NOT EXISTS work_card_workers (
    work_card_id INTEGER,
    worker_id INTEGER,
    amount REAL DEFAULT 0,
    PRIMARY KEY(work_card_id, worker_id),
    FOREIGN KEY(work_card_id) REFERENCES work_cards(id),
    FOREIGN KEY(worker_id) REFERENCES workers(id)
);

-- Добавление нового контракта
INSERT INTO contracts (contract_number, start_date, end_date, description)
VALUES (?, ?, ?, ?);

-- Обновление контракта
UPDATE contracts SET
    contract_number = ?,
    start_date = ?,
    end_date = ?,
    description = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;

-- Получение всех контрактов
SELECT * FROM contracts
ORDER BY contract_number;

-- Получение контракта по ID
SELECT * FROM contracts
WHERE id = ?;

-- Поиск контрактов по номеру или описанию
SELECT * FROM contracts
WHERE contract_number LIKE ? OR description LIKE ?
ORDER BY contract_number;

-- Удаление контракта
DELETE FROM contracts
WHERE id = ?;

-- Проверка уникальности номера контракта
SELECT EXISTS(
    SELECT 1 FROM contracts
    WHERE contract_number = ? AND id != ?
) AS exists;