# Установка и настройка PostgreSQL для Сделка v4.0

## 🐘 Установка PostgreSQL

### Windows

1. **Скачайте PostgreSQL** с официального сайта: https://www.postgresql.org/download/windows/
2. **Запустите установщик** и следуйте инструкциям
3. **Запомните пароль** для пользователя `postgres`
4. **Проверьте установку** через pgAdmin или командную строку

### macOS

```bash
# Через Homebrew
brew install postgresql
brew services start postgresql

# Или скачайте с официального сайта
```

### Linux (Ubuntu/Debian)

```bash
# Установка
sudo apt update
sudo apt install postgresql postgresql-contrib

# Запуск сервиса
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## 🗄 Создание базы данных

### Способ 1: Через psql (командная строка)

```bash
# Подключение к PostgreSQL
psql -U postgres

# Создание базы данных
CREATE DATABASE sdelka_v4;

# Создание пользователя
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';

# Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;

# Подключение к базе данных
\c sdelka_v4

# Предоставление прав на схему
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;

# Выход
\q
```

### Способ 2: Через pgAdmin

1. **Откройте pgAdmin**
2. **Подключитесь к серверу** (localhost)
3. **Создайте базу данных**:
   - Правый клик на "Databases" → "Create" → "Database..."
   - Name: `sdelka_v4`
   - Owner: `postgres`
4. **Создайте пользователя**:
   - Правый клик на "Login/Group Roles" → "Create" → "Login/Group Role..."
   - General: Name: `sdelka_user`
   - Definition: Password: `sdelka_password`
   - Privileges: Can login? ✅, Create roles? ✅
5. **Предоставьте права**:
   - Правый клик на `sdelka_v4` → "Properties"
   - Security: Add `sdelka_user` с правами "All"

## 🔧 Настройка подключения

### Проверка подключения

```bash
# Тест подключения
psql -h localhost -U sdelka_user -d sdelka_v4

# Если подключение успешно, вы увидите:
# sdelka_v4=>
```

### Настройка в приложении

Откройте файл `lib/services/database_service.dart` и проверьте настройки:

```dart
// Конфигурация базы данных
static const String _host = 'localhost';        // IP адрес сервера
static const int _port = 5432;                  // Порт PostgreSQL
static const String _databaseName = 'sdelka_v4'; // Имя базы данных
static const String _username = 'sdelka_user';   // Имя пользователя
static const String _password = 'sdelka_password'; // Пароль
```

## 🚀 Автоматическая настройка

Создайте скрипт для автоматической настройки:

### Windows (setup_db.bat)

```batch
@echo off
echo Настройка базы данных для Сделка v4.0...

psql -U postgres -c "CREATE DATABASE sdelka_v4;"
psql -U postgres -c "CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;"

echo База данных настроена успешно!
pause
```

### Linux/macOS (setup_db.sh)

```bash
#!/bin/bash
echo "Настройка базы данных для Сделка v4.0..."

psql -U postgres -c "CREATE DATABASE sdelka_v4;"
psql -U postgres -c "CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;"

echo "База данных настроена успешно!"
```

## 🔍 Устранение проблем

### Ошибка подключения

```
FATAL: password authentication failed for user "sdelka_user"
```

**Решение:**
1. Проверьте пароль пользователя
2. Убедитесь, что пользователь существует
3. Проверьте права доступа

### Ошибка базы данных

```
FATAL: database "sdelka_v4" does not exist
```

**Решение:**
1. Создайте базу данных: `CREATE DATABASE sdelka_v4;`
2. Проверьте права пользователя на базу данных

### Ошибка прав доступа

```
ERROR: permission denied for table workers
```

**Решение:**
```sql
-- Предоставьте права на все таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
```

## 📊 Мониторинг

### Проверка статуса PostgreSQL

```bash
# Windows
net start postgresql-x64-13

# Linux/macOS
sudo systemctl status postgresql
brew services list | grep postgresql
```

### Проверка подключений

```sql
-- Подключитесь к PostgreSQL
psql -U postgres

-- Просмотр активных подключений
SELECT * FROM pg_stat_activity WHERE datname = 'sdelka_v4';

-- Просмотр размеров таблиц
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public';
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Измените пароли по умолчанию**
2. **Ограничьте доступ** по IP адресам
3. **Используйте SSL** для удаленных подключений
4. **Регулярно обновляйте** PostgreSQL
5. **Настройте бэкапы** базы данных

### Настройка SSL (опционально)

```bash
# В postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

## 📈 Производительность

### Оптимизация PostgreSQL

```sql
-- В postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Индексы для производительности

```sql
-- Создание индексов после создания таблиц
CREATE INDEX idx_work_orders_date ON work_orders(date);
CREATE INDEX idx_work_orders_contract ON work_orders(contract_id);
CREATE INDEX idx_workers_name ON workers(name);
CREATE INDEX idx_products_no ON products(product_no);
```

## 📝 Логи

### Включение логирования

```bash
# В postgresql.conf
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'
log_min_duration_statement = 1000
```

---

**Готово!** Теперь PostgreSQL настроен и готов к работе с Сделка v4.0 🎉
