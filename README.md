# Сделка v4.0 - Flutter + PostgreSQL

Современное приложение для управления нарядами, разработанное с использованием Flutter и PostgreSQL.

## 🚀 Особенности

- **Современный UI** - Material Design 3 с поддержкой темной темы
- **Кроссплатформенность** - Windows, macOS, Linux
- **PostgreSQL** - надежная база данных с поддержкой сетевого доступа
- **Архитектура** - Clean Architecture с Riverpod для управления состоянием
- **Производительность** - нативная скорость выполнения

## 📋 Функциональность

### ✅ Реализовано
- [x] Базовая структура приложения
- [x] Современная тема оформления
- [x] Навигация между экранами
- [x] Модели данных
- [x] Сервис для работы с PostgreSQL
- [x] Управление состоянием (Riverpod)
- [x] Экран нарядов с карточками
- [x] Диалог создания/редактирования нарядов

### 🔄 В разработке
- [ ] Полная форма создания нарядов
- [ ] Управление работниками
- [ ] Управление изделиями
- [ ] Управление видами работ
- [ ] Отчеты и аналитика
- [ ] Синхронизация данных
- [ ] Экспорт/импорт данных

## 🛠 Технологии

- **Flutter** 3.0+ - UI фреймворк
- **PostgreSQL** 13+ - база данных
- **Riverpod** - управление состоянием
- **Material Design 3** - дизайн-система
- **Dart** 3.0+ - язык программирования

## 📦 Установка

### Требования
- Flutter SDK 3.0+
- PostgreSQL 13+
- Dart SDK 3.0+

### Настройка базы данных

1. Установите PostgreSQL
2. Создайте базу данных:
```sql
CREATE DATABASE sdelka_v4;
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;
```

3. Обновите настройки подключения в `lib/services/database_service.dart`:
```dart
static const String _host = 'localhost';
static const int _port = 5432;
static const String _databaseName = 'sdelka_v4';
static const String _username = 'sdelka_user';
static const String _password = 'sdelka_password';
```

### Запуск приложения

```bash
# Установка зависимостей
flutter pub get

# Генерация кода
flutter packages pub run build_runner build

# Запуск приложения
flutter run
```

## 📁 Структура проекта

```
lib/
├── main.dart                 # Точка входа
├── models/                   # Модели данных
│   ├── work_order.dart
│   ├── worker.dart
│   └── product.dart
├── services/                 # Сервисы
│   └── database_service.dart
├── providers/                # Провайдеры состояния
│   ├── database_provider.dart
│   └── app_provider.dart
├── screens/                  # Экраны приложения
│   ├── main_screen.dart
│   ├── work_orders_screen.dart
│   ├── workers_screen.dart
│   ├── products_screen.dart
│   ├── reports_screen.dart
│   └── settings_screen.dart
├── widgets/                  # Переиспользуемые виджеты
│   ├── app_app_bar.dart
│   ├── app_drawer.dart
│   ├── work_order_card.dart
│   └── work_order_form_dialog.dart
└── utils/                    # Утилиты
    └── app_theme.dart
```

## 🔧 Разработка

### Генерация кода
```bash
# Генерация JSON сериализации
flutter packages pub run build_runner build

# Генерация с удалением конфликтов
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### Линтинг
```bash
flutter analyze
```

### Тестирование
```bash
flutter test
```

## 📊 Сравнение с версией 3.0

| Параметр | v3.0 (Python + Tkinter) | v4.0 (Flutter + PostgreSQL) |
|----------|-------------------------|------------------------------|
| **UI** | Устаревший | Современный Material Design 3 |
| **Производительность** | Медленный | Нативная скорость |
| **Кроссплатформенность** | Только Windows | Windows, macOS, Linux |
| **База данных** | SQLite (локальная) | PostgreSQL (сетевая) |
| **Архитектура** | Монолитная | Clean Architecture |
| **Состояние** | Глобальные переменные | Riverpod |
| **Темы** | Ограниченные | Полная поддержка темной темы |
| **Размер** | ~50MB | ~20MB |
| **Скорость запуска** | 3-5 сек | <1 сек |

## 🎯 Планы развития

### v4.1 (Q1 2024)
- [ ] Полная функциональность форм
- [ ] Интеграция с внешними API
- [ ] Улучшенная синхронизация

### v4.2 (Q2 2024)
- [ ] Мобильная версия
- [ ] Облачная синхронизация
- [ ] Расширенная аналитика

### v4.3 (Q3 2024)
- [ ] Веб-версия
- [ ] API для интеграций
- [ ] Машинное обучение для прогнозов

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для функции (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

Если у вас есть вопросы или предложения, создайте [Issue](https://github.com/Valstan/Sdelka/issues) или свяжитесь с разработчиком.

---

**Сделка v4.0** - Современное решение для управления нарядами 🚀