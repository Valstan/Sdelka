-- File: app/core/database/queries/worker_assignments.sql
"""
SQL-запросы для работы с назначением работников к карточкам.
"""

-- Создание таблицы worker_assignments
CREATE TABLE IF NOT EXISTS worker_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(card_id) REFERENCES work_cards(id),
    FOREIGN KEY(worker_id) REFERENCES workers(id)
);

-- Добавление назначения работника
INSERT INTO worker_assignments (card_id, worker_id, amount)
VALUES (?, ?, ?);

-- Получение назначений работников для карточки
SELECT wa.*, w.last_name, w.first_name, w.middle_name
FROM worker_assignments wa
JOIN workers w ON wa.worker_id = w.id
WHERE wa.card_id = ?
ORDER BY w.last_name, w.first_name, w.middle_name;

-- Удаление назначения работника
DELETE FROM worker_assignments
WHERE id = ?;

-- Удаление всех назначений для карточки
DELETE FROM worker_assignments
WHERE card_id = ?;