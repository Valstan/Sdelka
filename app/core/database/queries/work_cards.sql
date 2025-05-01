-- File: app/core/database/queries/work_cards.sql
-- SQL-запросы для работы с карточками работ.

-- Таблица нарядов
CREATE TABLE IF NOT EXISTS work_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number TEXT NOT NULL UNIQUE,
    card_date DATE NOT NULL DEFAULT CURRENT_DATE,
    product_id INTEGER REFERENCES products(id),
    contract_id INTEGER REFERENCES contracts(id),
    total_amount REAL DEFAULT 0 CHECK(total_amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс по дате для фильтрации по периодам
CREATE INDEX IF NOT EXISTS idx_card_date ON work_cards(card_date);

-- Добавление новой карточки
INSERT INTO work_cards (card_number, card_date, product_id, contract_id, total_amount)
VALUES (?, ?, ?, ?, ?);

-- Обновление карточки
UPDATE work_cards SET
    card_date = ?,
    product_id = ?,
    contract_id = ?,
    total_amount = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;

-- Получение всех карточек
SELECT * FROM work_cards
ORDER BY card_date DESC;

-- Получение карточки по ID
SELECT * FROM work_cards
WHERE id = ?;

-- Поиск карточек по диапазону дат
SELECT * FROM work_cards
WHERE card_date BETWEEN ? AND ?
ORDER BY card_date DESC;

-- Поиск карточек по нескольким критериям
SELECT wc.id, wc.card_number, wc.card_date, wc.total_amount,
       p.name AS product_name, c.contract_number
FROM work_cards wc
JOIN products p ON wc.product_id = p.id
JOIN contracts c ON wc.contract_id = c.id
WHERE (:worker_id IS NULL OR wc.id IN (
    SELECT card_id FROM worker_assignments WHERE worker_id = :worker_id
))
AND (:work_type_id IS NULL OR wc.id IN (
    SELECT card_id FROM work_card_items WHERE work_type_id = :work_type_id
))
AND (:product_id IS NULL OR wc.product_id = :product_id)
AND (:contract_id IS NULL OR wc.contract_id = :contract_id)
AND (:start_date IS NULL OR wc.card_date >= :start_date)
AND (:end_date IS NULL OR wc.card_date <= :end_date)
ORDER BY wc.card_date DESC;

-- Удаление карточки
DELETE FROM work_cards
WHERE id = ?;

-- Получение следующего номера карточки
SELECT COALESCE(MAX(CAST(card_number AS INTEGER)), 0) + 1
FROM work_cards
WHERE card_date >= date('now', 'start of year');