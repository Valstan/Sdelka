# Инструкции по настройке Git и GitHub

## 🔧 Настройка Git (если не установлен)

### 1. Установка Git:
```bash
# Скачать с https://git-scm.com/download/win
# Или через Chocolatey:
choco install git

# Или через winget:
winget install Git.Git
```

### 2. Настройка Git:
```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваш@email.com"
```

## 🚀 Команды для загрузки на GitHub:

### 1. Инициализация репозитория:
```bash
cd D:\PycharmProject\Sdelka
git init
```

### 2. Создание .gitignore:
```bash
# Создать файл .gitignore с содержимым:
echo "# Python" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "*.pyo" >> .gitignore
echo "*.pyd" >> .gitignore
echo ".Python" >> .gitignore
echo "env/" >> .gitignore
echo "venv/" >> .gitignore
echo ".venv/" >> .gitignore
echo "*.egg-info/" >> .gitignore
echo "dist/" >> .gitignore
echo "build/" >> .gitignore
echo "" >> .gitignore
echo "# Flutter" >> .gitignore
echo "flutter_sdelka/sdelka_v4/build/" >> .gitignore
echo "flutter_sdelka/sdelka_v4/.dart_tool/" >> .gitignore
echo "flutter_sdelka/sdelka_v4/.packages" >> .gitignore
echo "flutter_sdelka/sdelka_v4/.pub-cache/" >> .gitignore
echo "flutter_sdelka/sdelka_v4/.pub/" >> .gitignore
echo "flutter_sdelka/sdelka_v4/pubspec.lock" >> .gitignore
echo "" >> .gitignore
echo "# IDE" >> .gitignore
echo ".vscode/" >> .gitignore
echo ".idea/" >> .gitignore
echo "*.swp" >> .gitignore
echo "*.swo" >> .gitignore
echo "" >> .gitignore
echo "# OS" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "Thumbs.db" >> .gitignore
echo "" >> .gitignore
echo "# Logs" >> .gitignore
echo "logs/" >> .gitignore
echo "*.log" >> .gitignore
```

### 3. Добавление файлов:
```bash
git add .
```

### 4. Первый коммит:
```bash
git commit -m "Initial commit: Flutter migration completed

- Migrated to Flutter v4.0
- Added PostgreSQL support
- Added Web platform support
- Implemented CRUD operations
- Added modern UI with Material Design 3
- Created automation scripts
- Added reports and export functionality"
```

### 5. Создание репозитория на GitHub:
1. Зайти на https://github.com
2. Нажать "New repository"
3. Назвать репозиторий: `Sdelka-Flutter`
4. Выбрать "Public" или "Private"
5. НЕ добавлять README, .gitignore, лицензию (они уже есть)

### 6. Подключение к GitHub:
```bash
git remote add origin https://github.com/ВАШ_ПОЛЬЗОВАТЕЛЬ/Sdelka-Flutter.git
git branch -M main
git push -u origin main
```

## 📋 Альтернативный способ (через GitHub Desktop):

1. Скачать GitHub Desktop: https://desktop.github.com/
2. Установить и войти в аккаунт
3. "Add an Existing Repository from your Hard Drive"
4. Выбрать папку `D:\PycharmProject\Sdelka`
5. "Publish repository" на GitHub

## 🔑 SSH ключи (опционально):

### Создание SSH ключа:
```bash
ssh-keygen -t rsa -b 4096 -C "ваш@email.com"
```

### Добавление в GitHub:
1. Скопировать содержимое `~/.ssh/id_rsa.pub`
2. GitHub → Settings → SSH and GPG keys → New SSH key
3. Вставить ключ

### Использование SSH URL:
```bash
git remote add origin git@github.com:ВАШ_ПОЛЬЗОВАТЕЛЬ/Sdelka-Flutter.git
```

## 📝 Описание коммитов:

```bash
# Основной коммит
git commit -m "feat: Complete Flutter migration to v4.0

- Migrate from Python to Flutter
- Add cross-platform support (Web, Windows, Android, iOS)
- Implement modern Material Design 3 UI
- Add PostgreSQL database integration
- Create comprehensive CRUD operations
- Add search, filtering, and reporting features
- Implement data export functionality
- Create automation scripts for setup and deployment
- Add comprehensive documentation and guides"
```

## 🏷️ Теги версий:

```bash
# Создать тег версии
git tag -a v4.0.0 -m "Release version 4.0.0 - Flutter migration complete"

# Отправить теги
git push origin --tags
```

## 📊 Статистика проекта:

После загрузки на GitHub вы увидите:
- **Основной язык:** Dart (Flutter)
- **Размер:** ~50MB
- **Файлов:** ~200+
- **Коммитов:** 1 (или больше, если делали промежуточные)

## 🎯 Что получится:

1. **Полноценный репозиторий** с историей разработки
2. **Документация** в README.md
3. **Инструкции** по установке и запуску
4. **Автоматизация** через GitHub Actions (можно добавить позже)
5. **Версионирование** через теги
6. **Коллаборация** с другими разработчиками

---

**Готово к загрузке на GitHub! 🚀**

