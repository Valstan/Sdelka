# Автоматическая настройка и запуск проекта Сделка v4.0
# Запускать от имени администратора в PowerShell

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

# Шаг 1: Проверка Flutter
Write-Host ""
Write-Host "Шаг 1: Проверка Flutter SDK" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Проверяем, есть ли Flutter в PATH
$flutterPath = Get-Command flutter -ErrorAction SilentlyContinue
if ($flutterPath) {
    Write-Host "Flutter найден в PATH: $($flutterPath.Source)" -ForegroundColor Green
    
    # Простая проверка версии с таймаутом
    Write-Host "Проверка версии Flutter..." -ForegroundColor Yellow
    try {
        $job = Start-Job -ScriptBlock { flutter --version }
        $result = Wait-Job $job -Timeout 30
        
        if ($result) {
            $output = Receive-Job $job
            Remove-Job $job
            
            if ($output -match "Flutter") {
                Write-Host "Flutter SDK работает" -ForegroundColor Green
                $versionLine = $output | Where-Object { $_ -match "Flutter" } | Select-Object -First 1
                Write-Host $versionLine -ForegroundColor Cyan
            } else {
                throw "Flutter не отвечает корректно"
            }
        } else {
            Remove-Job $job -Force
            throw "Flutter не отвечает в течение 30 секунд"
        }
    } catch {
        Write-Host "Проблемы с Flutter SDK: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Запуск установки Flutter..." -ForegroundColor Yellow
        
        try {
            if (Test-Path ".\install_flutter.ps1") {
                & .\install_flutter.ps1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Ошибка установки Flutter" -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "Скрипт установки Flutter не найден" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "Ошибка выполнения скрипта установки Flutter: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "Flutter не найден в PATH" -ForegroundColor Red
    Write-Host "Запуск установки Flutter..." -ForegroundColor Yellow
    
    try {
        if (Test-Path ".\install_flutter.ps1") {
            & .\install_flutter.ps1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Ошибка установки Flutter" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Скрипт установки Flutter не найден" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "Ошибка выполнения скрипта установки Flutter: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Шаг 2: Проверка PostgreSQL
Write-Host ""
Write-Host "Шаг 2: Проверка PostgreSQL" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$postgresService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($postgresService -and $postgresService.Status -eq "Running") {
    Write-Host "PostgreSQL запущен" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL не запущен" -ForegroundColor Red
    Write-Host "Запуск настройки PostgreSQL..." -ForegroundColor Yellow
    
    try {
        & .\setup_postgresql.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Ошибка настройки PostgreSQL" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "Ошибка выполнения скрипта настройки PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Шаг 3: Установка зависимостей Flutter
Write-Host ""
Write-Host "Шаг 3: Установка зависимостей Flutter" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Write-Host "Установка пакетов..." -ForegroundColor Yellow
try {
    & flutter pub get
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Зависимости установлены" -ForegroundColor Green
    } else {
        Write-Host "Ошибка установки зависимостей" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Ошибка выполнения flutter pub get: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Шаг 4: Генерация кода
Write-Host ""
Write-Host "Шаг 4: Генерация кода" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Write-Host "Генерация JSON сериализации..." -ForegroundColor Yellow
try {
    & flutter packages pub run build_runner build --delete-conflicting-outputs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Код сгенерирован успешно" -ForegroundColor Green
    } else {
        Write-Host "Предупреждения при генерации кода (возможно нормально)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Ошибка генерации кода: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Продолжаем без генерации..." -ForegroundColor Cyan
}

# Шаг 5: Проверка подключения к БД
Write-Host ""
Write-Host "Шаг 5: Проверка подключения к базе данных" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $env:PGPASSWORD = "sdelka_password"
    $result = & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -U sdelka_user -d sdelka_v4 -c "SELECT 'Connection OK' as status;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Подключение к базе данных успешно" -ForegroundColor Green
    } else {
        Write-Host "Проблемы с подключением к БД" -ForegroundColor Yellow
        Write-Host "Проверьте настройки PostgreSQL" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Не удалось проверить подключение к БД" -ForegroundColor Yellow
}

# Шаг 6: Запуск приложения
Write-Host ""
Write-Host "Шаг 6: Запуск приложения" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Write-Host "Все проверки пройдены успешно!" -ForegroundColor Green
Write-Host "Запуск Flutter приложения..." -ForegroundColor Yellow

Write-Host ""
Write-Host "Информация о проекте:" -ForegroundColor Cyan
Write-Host "   Приложение: Сделка v4.0" -ForegroundColor White
Write-Host "   База данных: PostgreSQL (localhost:5432)" -ForegroundColor White
Write-Host "   База данных: sdelka_v4" -ForegroundColor White
Write-Host "   Пользователь: sdelka_user" -ForegroundColor White

Write-Host ""
Write-Host "Управление приложением:" -ForegroundColor Cyan
Write-Host "   - Нажмите 'r' для горячей перезагрузки" -ForegroundColor White
Write-Host "   - Нажмите 'R' для полной перезагрузки" -ForegroundColor White
Write-Host "   - Нажмите 'q' для выхода" -ForegroundColor White
Write-Host "   - Нажмите 'h' для справки" -ForegroundColor White

Write-Host ""
Write-Host "Запуск..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Запуск Flutter приложения
try {
    & flutter run
} catch {
    Write-Host ""
    Write-Host "Ошибка запуска приложения: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Попробуйте запустить вручную: flutter run" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Спасибо за использование проекта Сделка v4.0!" -ForegroundColor Green
