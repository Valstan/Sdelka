# Улучшенный скрипт установки Flutter SDK
# Запускать от имени администратора в PowerShell

Write-Host "Установка Flutter SDK для проекта Сделка v4.0" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan

# Проверяем существующую установку Flutter
$existingFlutterPaths = @(
    "d:\valentin\downloads\flutter\",
    "C:\flutter\",
    "C:\src\flutter\",
    "$env:USERPROFILE\flutter\"
)

$flutterFound = $false
$flutterPath = ""

foreach ($path in $existingFlutterPaths) {
    if (Test-Path "$path\bin\flutter.bat") {
        Write-Host "Найден существующий Flutter: $path" -ForegroundColor Green
        $flutterPath = $path
        $flutterFound = $true
        break
    }
}

# Если Flutter найден, используем его
if ($flutterFound) {
    Write-Host "Используем существующую установку Flutter" -ForegroundColor Green
    
    # Проверяем, добавлен ли в PATH
    $flutterBinPath = "$flutterPath\bin"
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    
    if ($currentPath -notlike "*$flutterBinPath*") {
        Write-Host "Добавляем Flutter в PATH..." -ForegroundColor Yellow
        $newPath = $currentPath + ";" + $flutterBinPath
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "Flutter добавлен в PATH" -ForegroundColor Green
        
        # Обновляем PATH для текущей сессии
        $env:PATH = $env:PATH + ";" + $flutterBinPath
    } else {
        Write-Host "Flutter уже добавлен в PATH" -ForegroundColor Green
    }
    
    # Проверяем работоспособность
    Write-Host "Проверка работоспособности Flutter..." -ForegroundColor Yellow
    try {
        $version = & "$flutterBinPath\flutter.bat" --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Flutter работает корректно" -ForegroundColor Green
            $versionLine = $version | Where-Object { $_ -match "Flutter" } | Select-Object -First 1
            Write-Host $versionLine -ForegroundColor Cyan
        } else {
            throw "Flutter не отвечает"
        }
    } catch {
        Write-Host "Проблемы с существующей установкой Flutter" -ForegroundColor Red
        $flutterFound = $false
    }
}

# Если Flutter не найден или не работает, скачиваем новый
if (-not $flutterFound) {
    Write-Host "Устанавливаем новый Flutter SDK..." -ForegroundColor Yellow
    
    # Создание папки для Flutter
    $installPath = "C:\flutter"
    if (-not (Test-Path $installPath)) {
        Write-Host "Создание папки $installPath" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $installPath -Force
    }
    
    # Загрузка Flutter SDK
    $flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.9-stable.zip"
    $zipFile = "$env:TEMP\flutter_sdk.zip"
    
    Write-Host "Загрузка Flutter SDK..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $flutterUrl -OutFile $zipFile -UseBasicParsing
        Write-Host "Flutter SDK загружен" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка загрузки Flutter SDK: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    # Распаковка Flutter SDK
    Write-Host "Распаковка Flutter SDK..." -ForegroundColor Yellow
    try {
        Expand-Archive -Path $zipFile -DestinationPath "C:\" -Force
        Write-Host "Flutter SDK распакован" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка распаковки Flutter SDK: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    # Очистка временных файлов
    Remove-Item $zipFile -Force
    
    $flutterPath = $installPath
    $flutterBinPath = "$flutterPath\bin"
    
    # Добавление Flutter в PATH
    Write-Host "Настройка переменных окружения..." -ForegroundColor Yellow
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$flutterBinPath*") {
        $newPath = $currentPath + ";" + $flutterBinPath
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "Flutter добавлен в PATH" -ForegroundColor Green
    }
    
    # Обновляем PATH для текущей сессии
    $env:PATH = $env:PATH + ";" + $flutterBinPath
}

Write-Host ""
Write-Host "Установка Flutter завершена!" -ForegroundColor Green
Write-Host "Путь к Flutter: $flutterPath" -ForegroundColor Cyan
Write-Host "Путь к bin: $flutterBinPath" -ForegroundColor Cyan

# Финальная проверка
Write-Host ""
Write-Host "Финальная проверка Flutter..." -ForegroundColor Yellow
try {
    $version = & "$flutterBinPath\flutter.bat" --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Flutter установлен и работает!" -ForegroundColor Green
    } else {
        Write-Host "Предупреждение: Flutter может потребовать перезагрузки системы" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Предупреждение: Flutter может потребовать перезагрузки системы" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Cyan
Write-Host "1. Если Flutter не работает, перезапустите PowerShell" -ForegroundColor White
Write-Host "2. Если все еще не работает, перезагрузите компьютер" -ForegroundColor White
Write-Host "3. Запустите: flutter doctor" -ForegroundColor White
