# Сделка v4.0 - Flutter приложение

Современное приложение для управления нарядами, разработанное на Flutter с использованием PostgreSQL в качестве базы данных.

## 🚀 Особенности

- **Современный UI/UX** - Материальный дизайн 3.0
- **PostgreSQL** - Надежная база данных
- **Riverpod** - Управление состоянием
- **Адаптивный дизайн** - Работает на разных размерах экранов
- **Темная тема** - Поддержка системной темы

## 📋 Требования

### Системные требования
- Windows 10/11
- Flutter SDK 3.0+
- PostgreSQL 13+

### Установка Flutter
1. Скачайте Flutter SDK с [официального сайта](https://flutter.dev/docs/get-started/install/windows)
2. Распакуйте в `C:\flutter`
3. Добавьте `C:\flutter\bin` в переменную PATH
4. Проверьте установку: `flutter doctor`

### Установка PostgreSQL
1. Скачайте PostgreSQL с [официального сайта](https://www.postgresql.org/download/windows/)
2. Установите с паролем для пользователя `postgres`
3. Запомните пароль - он понадобится для настройки

## 🗄️ Настройка базы данных

### 1. Создание базы данных
```sql
-- Подключитесь к PostgreSQL
psql -U postgres

-- Выполните команды:
CREATE DATABASE sdelka_v4;
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
```

### 2. Проверка подключения
```bash
psql -h localhost -U sdelka_user -d sdelka_v4
```

## 🚀 Запуск приложения

### ⚡ Быстрый запуск (рекомендуется)

#### Автоматическая настройка
```powershell
# От имени администратора
.\setup_and_run.ps1
```

#### Быстрый запуск (если уже настроено)
```cmd
quick_start.bat
```

#### Проверка системы
```powershell
.\check_system.ps1
```

### 🔧 Ручная настройка

#### 1. Установка Flutter SDK
```powershell
# От имени администратора
.\install_flutter.ps1
```

#### 2. Настройка PostgreSQL
```powershell
# От имени администратора
.\setup_postgresql.ps1
```

#### 3. Клонирование репозитория
```bash
git clone https://github.com/Valstan/Sdelka.git
cd Sdelka
git checkout v4.0.0
```

#### 4. Установка зависимостей
```bash
cd flutter_sdelka/sdelka_v4
flutter pub get
```

#### 5. Генерация кода
```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

#### 6. Запуск приложения
```bash
flutter run
```

## 📁 Структура проекта

```
lib/
├── main.dart                 # Точка входа приложения
├── models/                   # Модели данных
│   ├── work_order.dart      # Модель наряда
│   ├── employee.dart        # Модель сотрудника
│   ├── product.dart         # Модель изделия
│   └── work_type.dart       # Модель вида работ
├── services/                 # Сервисы
│   └── database_service.dart # Сервис работы с БД
├── providers/                # Провайдеры состояния
│   ├── work_order_provider.dart
│   └── reference_data_provider.dart
├── screens/                  # Экраны приложения
│   ├── home_screen.dart
│   ├── work_orders_list_screen.dart
│   └── work_order_form_screen.dart
├── widgets/                  # Переиспользуемые виджеты
│   └── work_order_card.dart
└── utils/                    # Утилиты
    └── app_theme.dart        # Тема приложения
```

## 🔧 Конфигурация

### Настройки подключения к БД
Отредактируйте файл `lib/services/database_service.dart`:

```dart
static const String _host = 'localhost';
static const int _port = 5432;
static const String _databaseName = 'sdelka_v4';
static const String _username = 'sdelka_user';
static const String _password = 'sdelka_password';
```

## 📱 Функциональность

### ✅ Реализовано
- Главный экран с навигацией
- Список нарядов с фильтрацией
- Создание новых нарядов
- Просмотр деталей наряда
- Адаптивный дизайн
- Темная/светлая тема

### 🚧 В разработке
- Полная форма нарядов с выбором сотрудников, изделий и видов работ
- Экраны справочников (сотрудники, изделия, виды работ)
- Отчеты с графиками
- Экспорт данных
- Синхронизация между экземплярами

## 🐛 Отладка

### Проверка подключения к БД
Приложение автоматически проверяет подключение к базе данных. Статус отображается на главном экране.

### Логи
Логи приложения выводятся в консоль. Для более детальной отладки используйте:
```bash
flutter run --verbose
```

### Частые проблемы

1. **Ошибка подключения к PostgreSQL**
   - Убедитесь, что PostgreSQL запущен
   - Проверьте настройки подключения в `database_service.dart`
   - Проверьте, что пользователь `sdelka_user` создан

2. **Ошибки генерации кода**
   ```bash
   flutter packages pub run build_runner build --delete-conflicting-outputs
   ```

3. **Проблемы с зависимостями**
   ```bash
   flutter clean
   flutter pub get
   ```

## 🎯 Готовые скрипты

| Файл | Описание | Требования |
|------|----------|------------|
| `setup_and_run.ps1` | Полная автоматическая настройка | Администратор |
| `quick_start.bat` | Быстрый запуск | Обычный пользователь |
| `check_system.ps1` | Проверка готовности системы | Обычный пользователь |
| `install_flutter.ps1` | Установка Flutter SDK | Администратор |
| `setup_postgresql.ps1` | Настройка PostgreSQL | Администратор |

## 📖 Документация

- 📋 [LAUNCH_GUIDE.md](LAUNCH_GUIDE.md) - Подробное руководство по запуску
- 🗄️ [SETUP_POSTGRESQL.md](SETUP_POSTGRESQL.md) - Настройка PostgreSQL
- 🚀 [QUICK_START.md](QUICK_START.md) - Быстрый старт
- 📊 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Обзор проекта
- 🎯 [FINAL_REPORT.md](FINAL_REPORT.md) - Итоговый отчет

## ✅ Чек-лист запуска

- [ ] PowerShell запущен от имени администратора
- [ ] Flutter SDK установлен и настроен
- [ ] PostgreSQL установлен и запущен
- [ ] База данных `sdelka_v4` создана
- [ ] Пользователь `sdelka_user` создан
- [ ] Зависимости Flutter установлены
- [ ] Код сгенерирован успешно
- [ ] Приложение запускается без ошибок

## 🎉 Готово!

После успешного запуска вы увидите:
- 🏠 Главный экран с 6 карточками функций
- 📊 Статус подключения к базе данных
- 📝 Возможность создания нарядов
- 👥 Управление справочниками
- 📈 Просмотр отчетов с графиками
- 📤 Экспорт данных в CSV

**Приятного использования! 🚀**

## 📞 Поддержка

- Документация Flutter: https://flutter.dev/docs
- Документация PostgreSQL: https://www.postgresql.org/docs/
- Riverpod: https://riverpod.dev/

## 📄 Лицензия

Этот проект разработан для внутреннего использования.
