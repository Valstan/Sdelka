-- File: app/core/database/queries/work_card_items.sql
"""
SQL-запросы для работы с элементами карточек работ.
"""

-- Создание таблицы work_card_items
CREATE TABLE IF NOT EXISTS work_card_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    work_type_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    amount REAL NOT NULL CHECK(amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(card_id) REFERENCES work_cards(id),
    FOREIGN KEY(work_type_id) REFERENCES work_types(id)
);

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