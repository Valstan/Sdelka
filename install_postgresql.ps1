# Скрипт для установки PostgreSQL на Windows
# Автор: AI Assistant
# Дата: $(Get-Date)

Write-Host "Установка PostgreSQL на Windows..." -ForegroundColor Green

# Проверяем, запущен ли скрипт от имени администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Этот скрипт должен быть запущен от имени администратора!" -ForegroundColor Red
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# URL для скачивания PostgreSQL (последняя стабильная версия)
$postgresqlUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64.exe"
$installerPath = "$env:TEMP\postgresql-installer.exe"

Write-Host "Скачивание PostgreSQL установщика..." -ForegroundColor Yellow
try {
    # Скачиваем установщик
    Invoke-WebRequest -Uri $postgresqlUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Установщик скачан успешно!" -ForegroundColor Green
} catch {
    Write-Host "Ошибка при скачивании установщика: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Запуск установщика PostgreSQL..." -ForegroundColor Yellow
Write-Host "ВНИМАНИЕ: В процессе установки вам будет предложено:" -ForegroundColor Cyan
Write-Host "1. Выбрать компоненты для установки" -ForegroundColor Cyan
Write-Host "2. Выбрать директорию установки" -ForegroundColor Cyan
Write-Host "3. Ввести пароль для пользователя postgres" -ForegroundColor Cyan
Write-Host "4. Выбрать порт (по умолчанию 5432)" -ForegroundColor Cyan
Write-Host "5. Выбрать локаль" -ForegroundColor Cyan
Write-Host ""
Write-Host "Рекомендуемые настройки:" -ForegroundColor Yellow
Write-Host "- Пароль для postgres: sdelka123 (или любой другой безопасный пароль)" -ForegroundColor Yellow
Write-Host "- Порт: 5432" -ForegroundColor Yellow
Write-Host "- Локаль: Russian, Russia" -ForegroundColor Yellow
Write-Host ""

# Запускаем установщик
try {
    Start-Process -FilePath $installerPath -Wait
    Write-Host "Установка PostgreSQL завершена!" -ForegroundColor Green
} catch {
    Write-Host "Ошибка при запуске установщика: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Проверяем, что PostgreSQL установлен
Write-Host "Проверка установки PostgreSQL..." -ForegroundColor Yellow

# Добавляем PostgreSQL в PATH
$postgresqlPath = "C:\Program Files\PostgreSQL\16\bin"
if (Test-Path $postgresqlPath) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$postgresqlPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$postgresqlPath", "Machine")
        Write-Host "PostgreSQL добавлен в PATH" -ForegroundColor Green
    }
}

# Проверяем службу PostgreSQL
Write-Host "Проверка службы PostgreSQL..." -ForegroundColor Yellow
$service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Служба PostgreSQL найдена: $($service.Name)" -ForegroundColor Green
    if ($service.Status -eq "Running") {
        Write-Host "Служба PostgreSQL запущена!" -ForegroundColor Green
    } else {
        Write-Host "Запуск службы PostgreSQL..." -ForegroundColor Yellow
        Start-Service -Name $service.Name
        Write-Host "Служба PostgreSQL запущена!" -ForegroundColor Green
    }
} else {
    Write-Host "Служба PostgreSQL не найдена. Возможно, установка не завершилась успешно." -ForegroundColor Red
}

# Очищаем временный файл
if (Test-Path $installerPath) {
    Remove-Item $installerPath -Force
    Write-Host "Временный файл удален" -ForegroundColor Green
}

Write-Host ""
Write-Host "Установка PostgreSQL завершена!" -ForegroundColor Green
Write-Host "Для использования PostgreSQL в командной строке перезапустите PowerShell" -ForegroundColor Yellow
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Cyan
Write-Host "1. Перезапустите PowerShell" -ForegroundColor Cyan
Write-Host "2. Проверьте подключение: psql -U postgres -h localhost" -ForegroundColor Cyan
Write-Host "3. Создайте базу данных для проекта Sdelka" -ForegroundColor Cyan

Write-Host "Нажмите любую клавишу для выхода..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

