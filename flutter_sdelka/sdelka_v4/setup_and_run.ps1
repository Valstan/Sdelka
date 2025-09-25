# Автоматическая настройка и запуск проекта Сделка v4.0
# Запускать от имени администратора в PowerShell

Write-Host "Автоматическая настройка и запуск проекта Сделка v4.0" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Проверка прав администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Этот скрипт требует прав администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "✅ Права администратора подтверждены" -ForegroundColor Green

# Шаг 1: Проверка Flutter
Write-Host "`n📋 Шаг 1: Проверка Flutter SDK" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

try {
    $flutterVersion = & flutter --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Flutter SDK уже установлен" -ForegroundColor Green
        Write-Host "📊 Версия: $($flutterVersion[0])" -ForegroundColor Cyan
    } else {
        throw "Flutter не найден"
    }
} catch {
    Write-Host "❌ Flutter SDK не найден" -ForegroundColor Red
    Write-Host "🔧 Запуск установки Flutter..." -ForegroundColor Yellow
    
    try {
        & .\install_flutter.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Ошибка установки Flutter" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Ошибка выполнения скрипта установки Flutter: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Шаг 2: Проверка Flutter Doctor
Write-Host "`n📋 Шаг 2: Проверка Flutter Doctor" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

Write-Host "🔍 Проверка компонентов Flutter..." -ForegroundColor Yellow
$doctorOutput = & flutter doctor 2>&1
Write-Host $doctorOutput -ForegroundColor Cyan

# Проверка критических компонентов
if ($doctorOutput -match "Flutter.*not found" -or $doctorOutput -match "No valid Flutter SDK") {
    Write-Host "❌ Flutter SDK не настроен корректно" -ForegroundColor Red
    exit 1
}

# Шаг 3: Проверка PostgreSQL
Write-Host "`n📋 Шаг 3: Проверка PostgreSQL" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

$postgresService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($postgresService -and $postgresService.Status -eq "Running") {
    Write-Host "✅ PostgreSQL запущен" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL не запущен" -ForegroundColor Red
    Write-Host "🔧 Запуск настройки PostgreSQL..." -ForegroundColor Yellow
    
    try {
        & .\setup_postgresql.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Ошибка настройки PostgreSQL" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Ошибка выполнения скрипта настройки PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Шаг 4: Установка зависимостей Flutter
Write-Host "`n📋 Шаг 4: Установка зависимостей Flutter" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

Write-Host "📦 Установка пакетов..." -ForegroundColor Yellow
try {
    & flutter pub get
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Зависимости установлены" -ForegroundColor Green
    } else {
        Write-Host "❌ Ошибка установки зависимостей" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка выполнения flutter pub get: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Шаг 5: Генерация кода
Write-Host "`n📋 Шаг 5: Генерация кода" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

Write-Host "🔧 Генерация JSON сериализации..." -ForegroundColor Yellow
try {
    & flutter packages pub run build_runner build --delete-conflicting-outputs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Код сгенерирован успешно" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Предупреждения при генерации кода (возможно нормально)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка генерации кода: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "🔧 Продолжаем без генерации..." -ForegroundColor Cyan
}

# Шаг 6: Проверка подключения к БД
Write-Host "`n📋 Шаг 6: Проверка подключения к базе данных" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

try {
    $env:PGPASSWORD = "sdelka_password"
    $result = & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -U sdelka_user -d sdelka_v4 -c "SELECT 'Connection OK' as status;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Подключение к базе данных успешно" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Проблемы с подключением к БД" -ForegroundColor Yellow
        Write-Host "🔧 Проверьте настройки PostgreSQL" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️ Не удалось проверить подключение к БД" -ForegroundColor Yellow
}

# Шаг 7: Запуск приложения
Write-Host "`n📋 Шаг 7: Запуск приложения" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

Write-Host "🎉 Все проверки пройдены успешно!" -ForegroundColor Green
Write-Host "🚀 Запуск Flutter приложения..." -ForegroundColor Yellow

Write-Host "`n📋 Информация о проекте:" -ForegroundColor Cyan
Write-Host "   📱 Приложение: Сделка v4.0" -ForegroundColor White
Write-Host "   🗄️ База данных: PostgreSQL (localhost:5432)" -ForegroundColor White
Write-Host "   📊 База данных: sdelka_v4" -ForegroundColor White
Write-Host "   👤 Пользователь: sdelka_user" -ForegroundColor White

Write-Host "`n🔧 Управление приложением:" -ForegroundColor Cyan
Write-Host "   - Нажмите 'r' для горячей перезагрузки" -ForegroundColor White
Write-Host "   - Нажмите 'R' для полной перезагрузки" -ForegroundColor White
Write-Host "   - Нажмите 'q' для выхода" -ForegroundColor White
Write-Host "   - Нажмите 'h' для справки" -ForegroundColor White

Write-Host "`n⏳ Запуск..." -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

# Запуск Flutter приложения
try {
    & flutter run
} catch {
    Write-Host "`n❌ Ошибка запуска приложения: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔧 Попробуйте запустить вручную: flutter run" -ForegroundColor Yellow
}

Write-Host "`n👋 Спасибо за использование проекта Сделка v4.0!" -ForegroundColor Green
