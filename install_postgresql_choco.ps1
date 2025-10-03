# Альтернативный скрипт для установки PostgreSQL через Chocolatey
# Автор: AI Assistant
# Дата: $(Get-Date)

Write-Host "Установка PostgreSQL через Chocolatey..." -ForegroundColor Green

# Проверяем, запущен ли скрипт от имени администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Этот скрипт должен быть запущен от имени администратора!" -ForegroundColor Red
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Проверяем, установлен ли Chocolatey
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey не установлен. Устанавливаем Chocolatey..." -ForegroundColor Yellow
    
    # Устанавливаем Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Обновляем PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    
    Write-Host "Chocolatey установлен!" -ForegroundColor Green
} else {
    Write-Host "Chocolatey уже установлен" -ForegroundColor Green
}

# Устанавливаем PostgreSQL через Chocolatey
Write-Host "Установка PostgreSQL через Chocolatey..." -ForegroundColor Yellow
try {
    choco install postgresql --yes
    Write-Host "PostgreSQL установлен успешно!" -ForegroundColor Green
} catch {
    Write-Host "Ошибка при установке PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Проверяем установку
Write-Host "Проверка установки PostgreSQL..." -ForegroundColor Yellow
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
}

Write-Host ""
Write-Host "Установка PostgreSQL через Chocolatey завершена!" -ForegroundColor Green
Write-Host "Для использования PostgreSQL в командной строке перезапустите PowerShell" -ForegroundColor Yellow

Write-Host "Нажмите любую клавишу для выхода..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

