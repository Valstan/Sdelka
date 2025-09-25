# Настройка PostgreSQL для Сделка v4.0

## 📥 Установка PostgreSQL

### 1. Скачивание
Перейдите на [официальный сайт PostgreSQL](https://www.postgresql.org/download/windows/) и скачайте последнюю версию для Windows.

### 2. Установка
1. Запустите установщик
2. Выберите все компоненты (включая pgAdmin)
3. Выберите директорию установки (по умолчанию: `C:\Program Files\PostgreSQL\15`)
4. **ВАЖНО**: Запомните пароль для пользователя `postgres` - он понадобится для настройки
5. Выберите порт (по умолчанию: 5432)
6. Завершите установку

### 3. Проверка установки
Откройте командную строку и выполните:
```bash
psql --version
```

## 🗄️ Настройка базы данных

### 1. Подключение к PostgreSQL
```bash
psql -U postgres
```
Введите пароль, который вы задали при установке.

### 2. Создание базы данных и пользователя
```sql
-- Создание базы данных
CREATE DATABASE sdelka_v4;

-- Создание пользователя
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;

-- Переключение на новую базу данных
\c sdelka_v4

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sdelka_user;

-- Выход
\q
```

### 3. Проверка подключения
```bash
psql -h localhost -U sdelka_user -d sdelka_v4
```
Введите пароль: `sdelka_password`

Если подключение успешно, выполните:
```sql
SELECT current_database(), current_user;
```

Затем выйдите:
```sql
\q
```

## 🔧 Настройка pgAdmin (опционально)

### 1. Запуск pgAdmin
Найдите и запустите pgAdmin из меню Пуск.

### 2. Подключение к серверу
1. Щелкните правой кнопкой на "Servers" → "Create" → "Server"
2. Введите имя: `Sdelka Local`
3. Перейдите на вкладку "Connection":
   - Host: `localhost`
   - Port: `5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: ваш пароль от postgres

### 3. Проверка базы данных
После подключения вы должны увидеть базу данных `sdelka_v4` в списке.

## 🚀 Автоматическое создание таблиц

При первом запуске Flutter приложения таблицы будут созданы автоматически. Если нужно создать их вручную:

### 1. Подключение к базе данных
```bash
psql -h localhost -U sdelka_user -d sdelka_v4
```

### 2. Выполнение SQL скрипта
```sql
-- Создание таблицы сотрудников
CREATE TABLE IF NOT EXISTS employees (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  position VARCHAR(255) NOT NULL,
  department VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  email VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы изделий
CREATE TABLE IF NOT EXISTS products (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  unit VARCHAR(50) NOT NULL,
  article VARCHAR(100),
  category VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы видов работ
CREATE TABLE IF NOT EXISTS work_types (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  unit VARCHAR(50) NOT NULL,
  standard_price DECIMAL(10,2),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы нарядов
CREATE TABLE IF NOT EXISTS work_orders (
  id VARCHAR(36) PRIMARY KEY,
  number VARCHAR(50) NOT NULL UNIQUE,
  date DATE NOT NULL,
  department VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы позиций нарядов
CREATE TABLE IF NOT EXISTS work_order_items (
  id VARCHAR(36) PRIMARY KEY,
  work_order_id VARCHAR(36) NOT NULL,
  employee_id VARCHAR(36) NOT NULL,
  product_id VARCHAR(36) NOT NULL,
  work_type_id VARCHAR(36) NOT NULL,
  quantity INTEGER NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (employee_id) REFERENCES employees(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (work_type_id) REFERENCES work_types(id)
);
```

## 🔍 Проверка установки

### 1. Проверка службы PostgreSQL
```bash
sc query postgresql-x64-15
```
Статус должен быть "RUNNING".

### 2. Проверка портов
```bash
netstat -an | findstr :5432
```
Должен показать, что порт 5432 прослушивается.

### 3. Тестовые данные
Можете добавить тестовые данные для проверки:

```sql
-- Подключение к базе
psql -h localhost -U sdelka_user -d sdelka_v4

-- Добавление тестового сотрудника
INSERT INTO employees (id, name, position, department) 
VALUES ('test-employee-1', 'Иванов Иван Иванович', 'Слесарь', 'Цех №1');

-- Добавление тестового изделия
INSERT INTO products (id, name, unit) 
VALUES ('test-product-1', 'Деталь А', 'шт');

-- Добавление тестового вида работ
INSERT INTO work_types (id, name, unit, standard_price) 
VALUES ('test-work-type-1', 'Сборка', 'час', 150.00);
```

## 🐛 Решение проблем

### Проблема: Ошибка подключения
**Решение**: Проверьте, что PostgreSQL запущен и порт 5432 свободен.

### Проблема: Ошибка аутентификации
**Решение**: Убедитесь, что пароль для пользователя `sdelka_user` установлен как `sdelka_password`.

### Проблема: База данных не найдена
**Решение**: Убедитесь, что база данных `sdelka_v4` создана и пользователь имеет к ней доступ.

### Проблема: Нет прав на создание таблиц
**Решение**: Выполните команды GRANT для пользователя `sdelka_user`.

## 📞 Поддержка

- [Документация PostgreSQL](https://www.postgresql.org/docs/)
- [pgAdmin документация](https://www.pgadmin.org/docs/)
- [Flutter PostgreSQL](https://pub.dev/packages/postgres)
