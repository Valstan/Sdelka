# Скрипт автоматической установки Flutter SDK
# Запускать от имени администратора в PowerShell

Write-Host "🚀 Установка Flutter SDK для проекта Сделка v4.0" -ForegroundColor Green

# Проверка архитектуры системы
$arch = (Get-WmiObject -Class Win32_Processor).Architecture
if ($arch -eq 0) {
    $flutterArch = "x64"
} elseif ($arch -eq 5) {
    $flutterArch = "x64"
} else {
    $flutterArch = "x86"
}

Write-Host "📋 Обнаружена архитектура: $flutterArch" -ForegroundColor Yellow

# Создание папки для Flutter
$flutterPath = "C:\flutter"
if (-not (Test-Path $flutterPath)) {
    Write-Host "📁 Создание папки $flutterPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $flutterPath -Force
}

# Загрузка Flutter SDK
$flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.9-stable.zip"
$zipFile = "$env:TEMP\flutter_sdk.zip"

Write-Host "⬇️ Загрузка Flutter SDK..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $flutterUrl -OutFile $zipFile -UseBasicParsing
    Write-Host "✅ Flutter SDK загружен" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка загрузки Flutter SDK: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Распаковка Flutter SDK
Write-Host "📦 Распаковка Flutter SDK..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipFile -DestinationPath "C:\" -Force
    Write-Host "✅ Flutter SDK распакован" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка распаковки Flutter SDK: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Добавление Flutter в PATH
Write-Host "🔧 Настройка переменных окружения..." -ForegroundColor Yellow
$flutterBinPath = "$flutterPath\bin"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$flutterBinPath*") {
    $newPath = $currentPath + ";" + $flutterBinPath
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
    Write-Host "✅ Flutter добавлен в PATH" -ForegroundColor Green
}

# Очистка временных файлов
Remove-Item $zipFile -Force

Write-Host "🎉 Flutter SDK установлен успешно!" -ForegroundColor Green
Write-Host "📍 Путь установки: $flutterPath" -ForegroundColor Cyan
Write-Host "🔄 Перезапустите PowerShell или перезагрузите компьютер для применения изменений PATH" -ForegroundColor Yellow

# Проверка установки
Write-Host "🔍 Проверка установки Flutter..." -ForegroundColor Yellow
& "$flutterBinPath\flutter.bat" --version

Write-Host "✅ Установка завершена!" -ForegroundColor Green
Write-Host "📋 Следующие шаги:" -ForegroundColor Cyan
Write-Host "   1. Перезапустите PowerShell" -ForegroundColor White
Write-Host "   2. Запустите: flutter doctor" -ForegroundColor White
Write-Host "   3. Установите недостающие компоненты" -ForegroundColor White
Write-Host "   4. Запустите: setup_postgresql.ps1" -ForegroundColor White
