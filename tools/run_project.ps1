# Скрипт для запуска проекта Sdelka
Write-Host "Активация виртуального окружения..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

Write-Host "Запуск проекта Sdelka..." -ForegroundColor Green
python main.py

Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
