-- File: app/core/database/queries/work_card_items.sql
-- SQL-запросы для работы с элементами карточек работ.


-- Таблица элементов наряда
CREATE TABLE IF NOT EXISTS work_card_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_card_id INTEGER REFERENCES work_cards(id) ON DELETE CASCADE,
    work_type_id INTEGER REFERENCES work_types(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    amount REAL AS (quantity * (SELECT price FROM work_types wt WHERE wt.id = work_type_id)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс по типу работы для аналитики
CREATE INDEX IF NOT EXISTS idx_work_type_id ON work_card_items(work_type_id);

-- Добавление элемента карточки
INSERT INTO work_card_items (card_id, work_type_id, quantity, amount)
VALUES (?, ?, ?, ?);

-- Получение элементов карточки
SELECT wci.*, wt.name, wt.unit, wt.price
FROM work_card_items wci
JOIN work_types wt ON wci.work_type_id = wt.id
WHERE wci.card_id = ?
ORDER BY wt.name;

-- Удаление элемента карточки
DELETE FROM work_card_items
WHERE id = ?;

-- Удаление всех элементов карточки
DELETE FROM work_card_items
WHERE card_id = ?;