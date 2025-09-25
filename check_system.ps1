# Скрипт проверки готовности системы для запуска Сделка v4.0
# Запускать из корневой папки проекта

Write-Host "🔍 Проверка готовности системы для Сделка v4.0" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Переход в папку Flutter проекта
$flutterProjectPath = "flutter_sdelka\sdelka_v4"
if (Test-Path $flutterProjectPath) {
    Write-Host "📁 Переход в папку Flutter проекта: $flutterProjectPath" -ForegroundColor Yellow
    Set-Location $flutterProjectPath
} else {
    Write-Host "❌ Папка Flutter проекта не найдена: $flutterProjectPath" -ForegroundColor Red
    Write-Host "🔧 Убедитесь, что вы находитесь в корневой папке проекта Сделка" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка наличия скрипта проверки
if (-not (Test-Path "check_system.ps1")) {
    Write-Host "❌ Скрипт check_system.ps1 не найден в папке Flutter проекта" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "✅ Переход в папку Flutter проекта выполнен успешно" -ForegroundColor Green
Write-Host "🔍 Запуск проверки системы..." -ForegroundColor Yellow

# Запуск основного скрипта проверки
try {
    & ".\check_system.ps1"
} catch {
    Write-Host "❌ Ошибка запуска скрипта проверки: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔧 Попробуйте запустить вручную из папки flutter_sdelka\sdelka_v4" -ForegroundColor Yellow
}
