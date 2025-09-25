# 🚀 Руководство по запуску - Сделка v4.0

## ⚡ Быстрый запуск (рекомендуется)

### Вариант 1: Автоматическая настройка
1. **Откройте PowerShell от имени администратора**
2. **Перейдите в папку проекта**:
   ```powershell
   cd "D:\PycharmProject\Sdelka\flutter_sdelka\sdelka_v4"
   ```
3. **Запустите автоматическую настройку**:
   ```powershell
   .\setup_and_run.ps1
   ```

### Вариант 2: Быстрый запуск (если уже настроено)
1. **Двойной клик на файл**: `quick_start.bat`
2. **Или запустите в командной строке**:
   ```cmd
   quick_start.bat
   ```

## 🔧 Ручная настройка

### Шаг 1: Установка Flutter SDK
```powershell
# От имени администратора
.\install_flutter.ps1
```

### Шаг 2: Настройка PostgreSQL
```powershell
# От имени администратора
.\setup_postgresql.ps1
```

### Шаг 3: Установка зависимостей
```bash
flutter pub get
```

### Шаг 4: Генерация кода
```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### Шаг 5: Запуск приложения
```bash
flutter run
```

## 📋 Требования

### Системные требования
- **Windows 10/11** (64-bit)
- **8 GB RAM** (рекомендуется)
- **2 GB свободного места**
- **Интернет-соединение** для загрузки компонентов

### Права доступа
- **Администратор** - для установки Flutter и PostgreSQL
- **Обычный пользователь** - для запуска приложения

## 🗄️ Настройки базы данных

### Автоматические настройки
- **Host**: localhost
- **Port**: 5432
- **Database**: sdelka_v4
- **Username**: sdelka_user
- **Password**: sdelka_password

### Ручная настройка PostgreSQL
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
```

## 🔍 Проверка установки

### Проверка Flutter
```bash
flutter doctor
```

### Проверка PostgreSQL
```bash
psql -h localhost -U sdelka_user -d sdelka_v4
```

### Проверка подключения к БД
```bash
# В psql
SELECT current_database(), current_user;
```

## 🐛 Решение проблем

### Проблема: Flutter не найден
**Решение**:
1. Перезапустите PowerShell
2. Проверьте PATH: `echo $env:PATH`
3. Добавьте Flutter вручную: `C:\flutter\bin`

### Проблема: PostgreSQL не запускается
**Решение**:
1. Откройте `services.msc`
2. Найдите службу PostgreSQL
3. Запустите службу вручную

### Проблема: Ошибка подключения к БД
**Решение**:
1. Проверьте, что PostgreSQL запущен
2. Проверьте настройки в `lib/services/database_service.dart`
3. Убедитесь, что пользователь `sdelka_user` создан

### Проблема: Ошибки генерации кода
**Решение**:
```bash
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
```

## 📱 Запуск на разных устройствах

### Windows Desktop
```bash
flutter run -d windows
```

### Web (в разработке)
```bash
flutter run -d chrome
```

### Android (требует Android Studio)
```bash
flutter run -d android
```

## 🎯 Управление приложением

### Горячие клавиши Flutter
- **r** - Горячая перезагрузка
- **R** - Полная перезагрузка
- **q** - Выход из приложения
- **h** - Справка по командам

### Отладка
- **F5** - Запуск в режиме отладки
- **Ctrl+C** - Остановка приложения

## 📊 Мониторинг

### Логи приложения
```bash
flutter logs
```

### Производительность
```bash
flutter run --profile
```

### Анализ размера
```bash
flutter build apk --analyze-size
```

## 🆘 Поддержка

### Документация
- [Flutter Docs](https://flutter.dev/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

### Полезные команды
```bash
# Очистка проекта
flutter clean

# Обновление зависимостей
flutter pub upgrade

# Проверка проблем
flutter doctor -v

# Анализ кода
flutter analyze
```

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
- Главный экран с 6 карточками функций
- Статус подключения к базе данных
- Возможность создания нарядов
- Управление справочниками
- Просмотр отчетов с графиками
- Экспорт данных в CSV

**Приятного использования! 🚀**
