# Использование существующего Flutter из d:\valentin\downloads\flutter\
# Запускать от имени администратора

Write-Host "Использование существующего Flutter" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan

$existingFlutterPath = "d:\valentin\downloads\flutter\"
$flutterBinPath = "$existingFlutterPath\bin"

# Проверяем существование Flutter
if (Test-Path "$flutterBinPath\flutter.bat") {
    Write-Host "Найден Flutter: $existingFlutterPath" -ForegroundColor Green
    
    # Добавляем в PATH для текущей сессии
    $env:PATH = $env:PATH + ";" + $flutterBinPath
    Write-Host "Flutter добавлен в PATH для текущей сессии" -ForegroundColor Green
    
    # Добавляем в системный PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$flutterBinPath*") {
        $newPath = $currentPath + ";" + $flutterBinPath
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "Flutter добавлен в системный PATH" -ForegroundColor Green
    } else {
        Write-Host "Flutter уже в системном PATH" -ForegroundColor Green
    }
    
    # Проверяем работоспособность
    Write-Host "Проверка Flutter..." -ForegroundColor Yellow
    try {
        $version = & "$flutterBinPath\flutter.bat" --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Flutter работает!" -ForegroundColor Green
            $versionLine = $version | Where-Object { $_ -match "Flutter" } | Select-Object -First 1
            Write-Host $versionLine -ForegroundColor Cyan
        } else {
            Write-Host "Flutter не отвечает" -ForegroundColor Red
        }
    } catch {
        Write-Host "Ошибка проверки Flutter: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Устанавливаем зависимости
    Write-Host "Установка зависимостей Flutter..." -ForegroundColor Yellow
    try {
        & flutter pub get
        Write-Host "Зависимости установлены" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка установки зависимостей: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Генерируем код
    Write-Host "Генерация кода..." -ForegroundColor Yellow
    try {
        & flutter packages pub run build_runner build --delete-conflicting-outputs
        Write-Host "Код сгенерирован" -ForegroundColor Green
    } catch {
        Write-Host "Предупреждения при генерации кода (возможно нормально)" -ForegroundColor Yellow
    }
    
    # Запускаем приложение
    Write-Host "Запуск приложения..." -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Cyan
    
    try {
        & flutter run
    } catch {
        Write-Host "Ошибка запуска приложения: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Попробуйте запустить вручную: flutter run" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "Flutter не найден в: $existingFlutterPath" -ForegroundColor Red
    Write-Host "Проверьте путь к Flutter" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Готово!" -ForegroundColor Green
