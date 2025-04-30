-- File: app/core/database/queries/products.sql
"""
SQL-запросы для работы с изделиями.
"""

-- Таблица изделий
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс по наименованию для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_product_name ON products(name);

-- Добавление нового изделия
INSERT INTO products (name, product_number)
VALUES (?, ?);

-- Обновление изделия
UPDATE products SET
    name = ?,
    product_number = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;

-- Получение всех изделий
SELECT * FROM products
ORDER BY name;

-- Получение изделия по ID
SELECT * FROM products
WHERE id = ?;

-- Поиск изделий по названию или номеру
SELECT * FROM products
WHERE name LIKE ? OR product_number LIKE ?
ORDER BY name;

-- Удаление изделия
DELETE FROM products
WHERE id = ?;

-- Проверка уникальности номера изделия
SELECT EXISTS(
    SELECT 1 FROM products
    WHERE product_number = ? AND id != ?
) AS exists;