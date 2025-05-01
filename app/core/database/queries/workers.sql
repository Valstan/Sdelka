-- File: app/core/database/queries/workers.sql
-- SQL-запросы для работы с работниками предприятия.

-- Таблица работников
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    workshop_number INTEGER NOT NULL,
    position TEXT NOT NULL,
    employee_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс по табельному номеру для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_employee_id ON workers(employee_id);

-- Добавление нового работника
INSERT INTO workers (last_name, first_name, middle_name, workshop_number, position, employee_id)
VALUES (?, ?, ?, ?, ?, ?);

-- Обновление данных работника
UPDATE workers SET
    last_name = ?,
    first_name = ?,
    middle_name = ?,
    workshop_number = ?,
    position = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;

-- Получение всех работников
SELECT * FROM workers
ORDER BY last_name, first_name, middle_name;

-- Получение работника по ID
SELECT * FROM workers
WHERE id = ?;

-- Поиск работников по ФИО
SELECT * FROM workers
WHERE last_name LIKE ? OR first_name LIKE ? OR middle_name LIKE ?
ORDER BY last_name, first_name, middle_name;

-- Удаление работника
DELETE FROM workers
WHERE id = ?;

-- Проверка наличия работника с таким табельным номером
SELECT EXISTS(
    SELECT 1 FROM workers
    WHERE employee_id = ? AND id != ?
) AS exists;