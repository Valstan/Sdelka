# Бухгалтерская программа учета сдельной работы (CustomTkinter + SQLite)

## Быстрый старт

1. Python 3.10+
2. Создать и активировать venv, установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Запуск приложения:

```bash
python -m app.main
```

4. Тесты и покрытие:

```bash
pytest
```

## Структура
- `app/gui` — интерфейс (CustomTkinter)
- `app/db` — база данных, резервные копии, валидаторы
- `app/reports` — отчеты (HTML/PDF/Excel)
- `app/io` — импорт/экспорт Excel
- `app/services` — бизнес-логика
- `app/utils` — конфигурация, пути, логирование
- `tests` — модульные тесты (pytest)

## Данные
База данных SQLite создается автоматически при первом запуске (`data/app.db`). При старте формируется резервная копия (хранится до 20 последних).
