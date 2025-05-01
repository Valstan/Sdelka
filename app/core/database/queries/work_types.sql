-- File: app/core/database/queries/work_types.sql
-- SQL-запросы для работы с видами работ.

-- Таблица видов работ
CREATE TABLE IF NOT EXISTS work_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL CHECK(unit IN ('штуки', 'комплекты')),
    price REAL NOT NULL CHECK(price >= 0),
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(valid_from <= CURRENT_DATE)
);

-- Уникальный индекс по имени и дате для предотвращения дубликатов
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_work_type ON work_types(name, valid_from);

-- Добавление нового вида работы
INSERT INTO work_types (name, unit, price, valid_from)
VALUES (?, ?, ?, ?);

-- Обновление вида работы
UPDATE work_types SET
    name = ?,
    unit = ?,
    price = ?,
    valid_from = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;

-- Получение всех видов работ
SELECT * FROM work_types
ORDER BY name;

-- Получение вида работы по ID
SELECT * FROM work_types
WHERE id = ?;

-- Поиск видов работ по названию
SELECT * FROM work_types
WHERE name LIKE ?
ORDER BY name;

-- Удаление вида работы
DELETE FROM work_types
WHERE id = ?;

-- Получение актуальной цены вида работы на определенную дату
SELECT * FROM work_types
WHERE id = ? AND valid_from <= ?
ORDER BY valid_from DESC
LIMIT 1;

-- Проверка уникальности названия вида работы
SELECT EXISTS(
    SELECT 1 FROM work_types
    WHERE name = ? AND id != ?
) AS exists;