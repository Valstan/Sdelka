-- Создание базы данных и пользователя для проекта "Сделка"
-- PostgreSQL 18

-- Создание базы данных
CREATE DATABASE sdelka_v4;

-- Создание пользователя
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;

-- Подключение к базе данных
\c sdelka_v4;

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;

-- Установка прав по умолчанию
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sdelka_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sdelka_user;

