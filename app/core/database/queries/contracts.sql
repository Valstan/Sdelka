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