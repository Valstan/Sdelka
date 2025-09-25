# Максимально простой скрипт установки
# Запускать от имени администратора

Write-Host "Установка всех компонентов проекта Сделка v4.0" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

# Установка Flutter
Write-Host "1. Установка Flutter..." -ForegroundColor Yellow
if (Test-Path ".\install_flutter.ps1") {
    & .\install_flutter.ps1
} else {
    Write-Host "Скрипт install_flutter.ps1 не найден" -ForegroundColor Red
}

# Установка PostgreSQL  
Write-Host "2. Установка PostgreSQL..." -ForegroundColor Yellow
if (Test-Path ".\setup_postgresql.ps1") {
    & .\setup_postgresql.ps1
} else {
    Write-Host "Скрипт setup_postgresql.ps1 не найден" -ForegroundColor Red
}

Write-Host "3. Установка завершена!" -ForegroundColor Green
Write-Host "Перезапустите PowerShell и запустите: flutter run" -ForegroundColor Cyan
