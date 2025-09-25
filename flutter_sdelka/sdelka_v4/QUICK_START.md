# 🚀 Быстрый старт - Сделка v4.0

## 📋 Что нужно установить

### 1. Flutter SDK
```bash
# Скачайте с https://flutter.dev/docs/get-started/install/windows
# Распакуйте в C:\flutter
# Добавьте C:\flutter\bin в PATH
```

### 2. PostgreSQL
```bash
# Скачайте с https://www.postgresql.org/download/windows/
# Установите с паролем для postgres
```

## ⚡ Быстрая настройка

### 1. Клонируйте проект
```bash
git clone https://github.com/Valstan/Sdelka.git
cd Sdelka/flutter_sdelka/sdelka_v4
```

### 2. Настройте PostgreSQL
```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Выполните команды:
CREATE DATABASE sdelka_v4;
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
\q
```

### 3. Запустите приложение
```bash
flutter pub get
flutter packages pub run build_runner build
flutter run
```

## 🎯 Что вы увидите

1. **Главный экран** - с карточками функций
2. **Список нарядов** - пустой список (можно создать новый)
3. **Создание наряда** - форма с основными полями
4. **Статус БД** - внизу главного экрана

## 🔧 Если что-то не работает

### Ошибка подключения к БД
```bash
# Проверьте, что PostgreSQL запущен
sc query postgresql-x64-15

# Проверьте подключение
psql -h localhost -U sdelka_user -d sdelka_v4
```

### Ошибки Flutter
```bash
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### Ошибки генерации кода
```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

## 📱 Функции

### ✅ Работает
- Главный экран с навигацией
- Список нарядов
- Создание нарядов
- Просмотр деталей наряда
- Темная/светлая тема

### 🚧 В разработке
- Полная форма нарядов
- Справочники
- Отчеты
- Экспорт

## 🆘 Поддержка

Если что-то не работает:
1. Проверьте `flutter doctor`
2. Проверьте подключение к PostgreSQL
3. Убедитесь, что все зависимости установлены

**Удачи! 🎉**
