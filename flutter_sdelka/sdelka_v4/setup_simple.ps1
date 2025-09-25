# Простой скрипт настройки и запуска проекта Сделка v4.0
# Запускать от имени администратора в PowerShell

Write-Host "Простая настройка и запуск проекта Сделка v4.0" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Проверка прав администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Этот скрипт требует прав администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Права администратора подтверждены" -ForegroundColor Green

# Шаг 1: Установка Flutter (с проверкой существующих установок)
Write-Host ""
Write-Host "Шаг 1: Установка Flutter SDK" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if (Test-Path ".\install_flutter_improved.ps1") {
    Write-Host "Запуск улучшенной установки Flutter..." -ForegroundColor Yellow
    try {
        & .\install_flutter_improved.ps1
        Write-Host "Установка Flutter завершена" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка установки Flutter: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Продолжаем без Flutter..." -ForegroundColor Yellow
    }
} else {
    Write-Host "Скрипт улучшенной установки Flutter не найден" -ForegroundColor Red
    Write-Host "Пропускаем установку Flutter..." -ForegroundColor Yellow
}

# Шаг 2: Установка PostgreSQL
Write-Host ""
Write-Host "Шаг 2: Установка PostgreSQL" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if (Test-Path ".\setup_postgresql.ps1") {
    Write-Host "Запуск установки PostgreSQL..." -ForegroundColor Yellow
    try {
        & .\setup_postgresql.ps1
        Write-Host "Установка PostgreSQL завершена" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка установки PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Продолжаем без PostgreSQL..." -ForegroundColor Yellow
    }
} else {
    Write-Host "Скрипт установки PostgreSQL не найден" -ForegroundColor Red
    Write-Host "Пропускаем установку PostgreSQL..." -ForegroundColor Yellow
}

# Шаг 3: Проверка Flutter после установки
Write-Host ""
Write-Host "Шаг 3: Проверка Flutter" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Обновляем PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

# Проверяем Flutter
$flutterCheck = Get-Command flutter -ErrorAction SilentlyContinue
if ($flutterCheck) {
    Write-Host "Flutter найден: $($flutterCheck.Source)" -ForegroundColor Green
    
    # Установка зависимостей
    Write-Host "Установка зависимостей Flutter..." -ForegroundColor Yellow
    try {
        & flutter pub get
        Write-Host "Зависимости установлены" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка установки зависимостей: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Генерация кода
    Write-Host "Генерация кода..." -ForegroundColor Yellow
    try {
        & flutter packages pub run build_runner build --delete-conflicting-outputs
        Write-Host "Код сгенерирован" -ForegroundColor Green
    } catch {
        Write-Host "Предупреждения при генерации кода (возможно нормально)" -ForegroundColor Yellow
    }
    
    # Запуск приложения
    Write-Host ""
    Write-Host "Запуск приложения..." -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    
    try {
        & flutter run
    } catch {
        Write-Host "Ошибка запуска приложения: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Попробуйте запустить вручную: flutter run" -ForegroundColor Yellow
    }
} else {
    Write-Host "Flutter не найден в PATH" -ForegroundColor Red
    Write-Host "Возможно, нужно перезапустить PowerShell или добавить Flutter в PATH вручную" -ForegroundColor Yellow
    Write-Host "Путь к Flutter обычно: C:\flutter\bin" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Спасибо за использование проекта Сделка v4.0!" -ForegroundColor Green
