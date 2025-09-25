# Скрипт автоматической настройки и запуска проекта Сделка v4.0
# Запускать из корневой папки проекта

Write-Host "Автоматическая настройка и запуск проекта Сделка v4.0" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Проверка прав администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Этот скрипт требует прав администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Права администратора подтверждены" -ForegroundColor Green

# Переход в папку Flutter проекта
$flutterProjectPath = "flutter_sdelka\sdelka_v4"
if (Test-Path $flutterProjectPath) {
    Write-Host "Переход в папку Flutter проекта: $flutterProjectPath" -ForegroundColor Yellow
    Set-Location $flutterProjectPath
} else {
    Write-Host "Папка Flutter проекта не найдена: $flutterProjectPath" -ForegroundColor Red
    Write-Host "Убедитесь, что вы находитесь в корневой папке проекта Сделка" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка наличия скриптов
if (-not (Test-Path "setup_and_run.ps1")) {
    Write-Host "Скрипт setup_and_run.ps1 не найден в папке Flutter проекта" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Переход в папку Flutter проекта выполнен успешно" -ForegroundColor Green
Write-Host "Запуск основного скрипта настройки..." -ForegroundColor Yellow

# Запуск скрипта с использованием существующего Flutter
try {
    & ".\use_existing_flutter.ps1"
} catch {
    Write-Host "Ошибка запуска скрипта: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Попробуйте запустить вручную из папки flutter_sdelka\sdelka_v4" -ForegroundColor Yellow
}
