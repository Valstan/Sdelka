# 🗄️ База данных для проекта "Сделка"

## 📋 Обзор

Проект "Сделка" поддерживает несколько типов баз данных:

- **SQLite** - для разработки и простых случаев
- **PostgreSQL** - для продакшена и масштабируемых решений
- **Mock** - для тестирования и демонстрации

## 🚀 Быстрый старт

### Вариант 1: SQLite (рекомендуется для начала)

```bash
# Python версия уже использует SQLite
python main.py

# Flutter версия автоматически выберет SQLite если PostgreSQL недоступен
cd flutter_sdelka/sdelka_v4
flutter run
```

### Вариант 2: PostgreSQL через Docker

```bash
# Запуск PostgreSQL в Docker
python docker_postgresql.py

# Миграция данных из SQLite в PostgreSQL
python migrate_sqlite_to_postgresql.py
```

### Вариант 3: PostgreSQL (ручная установка)

1. Установите PostgreSQL 15+
2. Создайте базу данных:
   ```sql
   CREATE DATABASE sdelka_v4;
   CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';
   GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;
   ```
3. Запустите миграцию:
   ```bash
   python migrate_sqlite_to_postgresql.py
   ```

## 🔧 Конфигурация

### SQLite
- **Файл**: `data/base_sdelka_rmz.db`
- **Преимущества**: Простота, портативность, быстрый старт
- **Недостатки**: Ограниченная масштабируемость, один пользователь

### PostgreSQL
- **Host**: localhost:5432
- **Database**: sdelka_v4
- **User**: sdelka_user
- **Password**: sdelka_password
- **Преимущества**: Масштабируемость, надежность, многопользовательский режим
- **Недостатки**: Требует установки сервера

## 📊 Схема базы данных

### Основные таблицы:
- `employees` - сотрудники
- `products` - изделия
- `work_types` - виды работ
- `contracts` - контракты
- `work_orders` - наряды
- `work_order_items` - элементы нарядов
- `work_order_products` - изделия в нарядах
- `work_order_workers` - рабочие в нарядах
- `contract_history` - история контрактов

## 🔄 Миграция данных

### SQLite → PostgreSQL

```bash
# 1. Убедитесь, что PostgreSQL запущен
python docker_postgresql.py

# 2. Выполните миграцию
python migrate_sqlite_to_postgresql.py

# 3. Проверьте результат
# Логи сохраняются в migration.log
```

### Особенности миграции:
- Автоматическое создание таблиц
- Конвертация типов данных
- Генерация UUID для записей без ID
- Проверка целостности данных
- Логирование всех операций

## 🐳 Docker команды

```bash
# Запуск PostgreSQL
python docker_postgresql.py

# Остановка PostgreSQL
python docker_postgresql.py stop

# Просмотр логов
docker logs postgres-sdelka

# Подключение к базе
docker exec -it postgres-sdelka psql -U sdelka_user -d sdelka_v4
```

## 🔍 Отладка

### Проверка подключения к PostgreSQL:
```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="sdelka_v4",
        user="sdelka_user",
        password="sdelka_password"
    )
    print("✅ Подключение успешно")
    conn.close()
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

### Проверка SQLite:
```python
import sqlite3

try:
    conn = sqlite3.connect("data/base_sdelka_rmz.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    print(f"✅ SQLite: {count} сотрудников")
    conn.close()
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

## 📈 Производительность

### SQLite:
- ✅ Быстрый старт
- ✅ Низкое потребление ресурсов
- ❌ Ограничения при множественных подключениях
- ❌ Нет сетевого доступа

### PostgreSQL:
- ✅ Высокая производительность
- ✅ Множественные подключения
- ✅ Сетевой доступ
- ✅ Расширенные возможности
- ❌ Требует больше ресурсов

## 🛠️ Разработка

### Добавление новых таблиц:

1. **SQLite** - обновите `db/schema.py`
2. **PostgreSQL** - обновите миграционный скрипт
3. **Flutter** - обновите модели и сервисы

### Тестирование:

```bash
# Тесты с SQLite
python run_tests.py

# Тесты с PostgreSQL (требует запущенного сервера)
POSTGRES_URL=postgresql://sdelka_user:sdelka_password@localhost:5432/sdelka_v4 python run_tests.py
```

## 📝 Логи

- **Миграция**: `migration.log`
- **Приложение**: `logs/app.log`
- **Docker**: `docker logs postgres-sdelka`

## 🆘 Решение проблем

### PostgreSQL не запускается:
1. Проверьте, что порт 5432 свободен
2. Убедитесь, что Docker запущен
3. Проверьте логи: `docker logs postgres-sdelka`

### Ошибки миграции:
1. Проверьте права доступа к файлам
2. Убедитесь, что SQLite файл существует
3. Проверьте подключение к PostgreSQL

### Flutter не подключается:
1. Проверьте, что база данных запущена
2. Убедитесь в правильности параметров подключения
3. Проверьте логи приложения

## 📚 Дополнительные ресурсы

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)
- [Flutter Database](https://docs.flutter.dev/development/data-and-backend/state-mgmt/options)
