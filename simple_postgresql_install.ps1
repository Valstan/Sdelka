# Простая установка PostgreSQL
Write-Host "Установка PostgreSQL..." -ForegroundColor Green

# Скачиваем установщик PostgreSQL
$url = "https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64.exe"
$output = "$env:TEMP\postgresql-installer.exe"

Write-Host "Скачивание установщика PostgreSQL..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    Write-Host "Установщик скачан: $output" -ForegroundColor Green
} catch {
    Write-Host "Ошибка скачивания: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Запуск установщика PostgreSQL..." -ForegroundColor Yellow
Write-Host "ВНИМАНИЕ: В установщике выберите:" -ForegroundColor Cyan
Write-Host "- Пароль для postgres: sdelka123" -ForegroundColor Cyan
Write-Host "- Порт: 5432" -ForegroundColor Cyan
Write-Host "- Локаль: Russian, Russia" -ForegroundColor Cyan

# Запускаем установщик
Start-Process -FilePath $output -Wait

Write-Host "Установка завершена!" -ForegroundColor Green
Write-Host "Проверяем службу PostgreSQL..." -ForegroundColor Yellow

# Проверяем службу
$services = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
if ($services) {
    foreach ($service in $services) {
        Write-Host "Найдена служба: $($service.Name) - $($service.Status)" -ForegroundColor Green
        if ($service.Status -ne "Running") {
            Start-Service -Name $service.Name
            Write-Host "Служба $($service.Name) запущена!" -ForegroundColor Green
        }
    }
} else {
    Write-Host "Служба PostgreSQL не найдена" -ForegroundColor Red
}

# Очищаем временный файл
Remove-Item $output -Force -ErrorAction SilentlyContinue

Write-Host "Готово!" -ForegroundColor Green

