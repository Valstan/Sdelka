# Сделка v4.0 - Система управления нарядами

Современное приложение для управления нарядами с поддержкой Python (CustomTkinter) и Flutter версий.

## 🚀 Быстрый старт

### Python версия (Desktop)

```bash
# Клонирование репозитория
git clone https://github.com/your-username/sdelka.git
cd sdelka

# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python main.py
```

### Flutter версия (Cross-platform)

```bash
# Переход в директорию Flutter
cd flutter_sdelka/sdelka_v4

# Установка зависимостей
flutter pub get

# Запуск на Windows
flutter run -d windows

# Запуск на Web
flutter run -d chrome

# Запуск на мобильных устройствах
flutter run -d android
flutter run -d ios
```

## 🐳 Docker развертывание

### Простое развертывание

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Ручная сборка

```bash
# Сборка образа
docker build -t sdelka:latest .

# Запуск контейнера
docker run -d \
  --name sdelka-app \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  sdelka:latest
```

## 🧪 Тестирование

### Python тесты

```bash
# Запуск всех тестов
python -m pytest tests/ -v

# Запуск с покрытием
python -m pytest tests/ --cov=. --cov-report=html

# Запуск конкретного теста
python -m pytest tests/test_gui_components.py -v
```

### Flutter тесты

```bash
cd flutter_sdelka/sdelka_v4

# Запуск тестов
flutter test

# Запуск с покрытием
flutter test --coverage
```

## 📊 CI/CD

Проект настроен с автоматическим CI/CD пайплайном:

- **Тестирование**: Python и Flutter тесты на разных версиях
- **Линтинг**: flake8, black, isort, mypy
- **Безопасность**: bandit, safety
- **Сборка**: Docker образы
- **Развертывание**: Автоматическое развертывание на staging/production

## 🏗️ Архитектура

### Python версия
- **GUI**: CustomTkinter с современным дизайном
- **База данных**: SQLite с возможностью миграции на PostgreSQL
- **Синхронизация**: Yandex.Disk для автоматического бэкапа
- **Архитектура**: Модульная с разделением на компоненты

### Flutter версия
- **UI**: Material Design 3
- **База данных**: Гибридная архитектура (SQLite/PostgreSQL/Mock)
- **Состояние**: Riverpod для управления состоянием
- **Платформы**: Windows, Web, Android, iOS

## 📁 Структура проекта

```
sdelka/
├── gui/                    # Python GUI компоненты
│   ├── components/         # Модульные компоненты
│   ├── forms/             # Формы приложения
│   └── windows/           # Окна приложения
├── services/              # Бизнес-логика
├── db/                    # Работа с базой данных
├── utils/                 # Утилиты
├── tests/                 # Тесты
├── flutter_sdelka/        # Flutter версия
│   └── sdelka_v4/
│       ├── lib/
│       │   ├── models/    # Модели данных
│       │   ├── services/  # Сервисы
│       │   ├── screens/   # Экраны
│       │   └── widgets/   # Виджеты
│       └── test/          # Flutter тесты
├── .github/workflows/     # CI/CD пайплайны
├── docker-compose.yml     # Docker Compose
└── Dockerfile            # Docker образ
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# База данных
DATABASE_URL=sqlite:///data/sdelka.db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sdelka
POSTGRES_USER=sdelka_user
POSTGRES_PASSWORD=sdelka_password

# Синхронизация
YANDEX_DISK_TOKEN=your_token_here
SYNC_INTERVAL=3600

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/sdelka.log
```

### Настройка PostgreSQL

```bash
# Создание базы данных
createdb sdelka

# Запуск миграции
python migrate_sqlite_to_postgresql.py
```

## 📈 Мониторинг

### Метрики

- Покрытие тестами: 23% (Python), 100% (Flutter)
- Производительность: Мониторинг через psutil
- Логи: Структурированное логирование

### Логирование

```bash
# Просмотр логов
tail -f logs/sdelka.log

# Docker логи
docker-compose logs -f sdelka-app
```

## 🚀 Развертывание в продакшене

### Подготовка

1. Настройте PostgreSQL
2. Создайте SSL сертификаты
3. Настройте переменные окружения
4. Запустите миграции

### Развертывание

```bash
# Продакшен развертывание
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose ps
```

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-username/sdelka/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/sdelka/discussions)
- **Email**: support@sdelka.com

## 🎯 Roadmap

- [ ] Веб-версия Flutter
- [ ] Мобильные приложения (iOS/Android)
- [ ] Интеграция с 1C
- [ ] Микросервисная архитектура
- [ ] API для внешних систем
- [ ] Машинное обучение для прогнозирования
- [ ] Многоязычность