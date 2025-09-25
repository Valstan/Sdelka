# Скрипт проверки готовности системы для запуска Сделка v4.0
# Можно запускать от обычного пользователя

Write-Host "🔍 Проверка готовности системы для Сделка v4.0" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

$allGood = $true

# Проверка 1: Flutter SDK
Write-Host "`n📋 Проверка 1: Flutter SDK" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

try {
    $flutterVersion = & flutter --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Flutter SDK установлен" -ForegroundColor Green
        $versionLine = $flutterVersion | Where-Object { $_ -match "Flutter" }
        Write-Host "📊 $versionLine" -ForegroundColor Cyan
        
        # Проверка Flutter Doctor
        Write-Host "🔍 Проверка Flutter Doctor..." -ForegroundColor Yellow
        $doctorOutput = & flutter doctor 2>&1
        
        if ($doctorOutput -match "No issues found" -or $doctorOutput -match "Doctor summary") {
            Write-Host "✅ Flutter настроен корректно" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Есть предупреждения Flutter Doctor:" -ForegroundColor Yellow
            $doctorOutput | ForEach-Object { Write-Host "   $_" -ForegroundColor White }
        }
    } else {
        throw "Flutter не найден"
    }
} catch {
    Write-Host "❌ Flutter SDK не установлен или не настроен" -ForegroundColor Red
    Write-Host "🔧 Запустите: .\install_flutter.ps1 (от администратора)" -ForegroundColor Cyan
    $allGood = $false
}

# Проверка 2: PostgreSQL
Write-Host "`n📋 Проверка 2: PostgreSQL" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

$postgresService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($postgresService) {
    if ($postgresService.Status -eq "Running") {
        Write-Host "✅ PostgreSQL запущен" -ForegroundColor Green
        Write-Host "📊 Служба: $($postgresService.Name)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️ PostgreSQL установлен, но не запущен" -ForegroundColor Yellow
        Write-Host "🔧 Запустите службу PostgreSQL в services.msc" -ForegroundColor Cyan
        $allGood = $false
    }
} else {
    Write-Host "❌ PostgreSQL не установлен" -ForegroundColor Red
    Write-Host "🔧 Запустите: .\setup_postgresql.ps1 (от администратора)" -ForegroundColor Cyan
    $allGood = $false
}

# Проверка 3: Подключение к базе данных
Write-Host "`n📋 Проверка 3: Подключение к базе данных" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

try {
    $env:PGPASSWORD = "sdelka_password"
    $result = & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -U sdelka_user -d sdelka_v4 -c "SELECT 'Connection OK' as status;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Подключение к базе данных успешно" -ForegroundColor Green
        Write-Host "📊 База данных: sdelka_v4" -ForegroundColor Cyan
        Write-Host "👤 Пользователь: sdelka_user" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Не удалось подключиться к базе данных" -ForegroundColor Red
        Write-Host "🔧 Проверьте настройки PostgreSQL" -ForegroundColor Cyan
        $allGood = $false
    }
} catch {
    Write-Host "❌ PostgreSQL не настроен или недоступен" -ForegroundColor Red
    Write-Host "🔧 Запустите: .\setup_postgresql.ps1 (от администратора)" -ForegroundColor Cyan
    $allGood = $false
}

# Проверка 4: Зависимости Flutter
Write-Host "`n📋 Проверка 4: Зависимости Flutter" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

if (Test-Path "pubspec.yaml") {
    Write-Host "✅ Файл pubspec.yaml найден" -ForegroundColor Green
    
    if (Test-Path ".dart_tool\package_config.json") {
        Write-Host "✅ Зависимости Flutter установлены" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Зависимости не установлены" -ForegroundColor Yellow
        Write-Host "🔧 Запустите: flutter pub get" -ForegroundColor Cyan
        $allGood = $false
    }
} else {
    Write-Host "❌ Файл pubspec.yaml не найден" -ForegroundColor Red
    Write-Host "🔧 Убедитесь, что вы находитесь в папке проекта Flutter" -ForegroundColor Cyan
    $allGood = $false
}

# Проверка 5: Генерация кода
Write-Host "`n📋 Проверка 5: Генерация кода" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

$generatedFiles = @(
    "lib\models\work_order.g.dart",
    "lib\models\employee.g.dart", 
    "lib\models\product.g.dart",
    "lib\models\work_type.g.dart"
)

$generatedCount = 0
foreach ($file in $generatedFiles) {
    if (Test-Path $file) {
        $generatedCount++
    }
}

if ($generatedCount -eq $generatedFiles.Count) {
    Write-Host "✅ Все файлы кода сгенерированы ($generatedCount/$($generatedFiles.Count))" -ForegroundColor Green
} else {
    Write-Host "⚠️ Не все файлы кода сгенерированы ($generatedCount/$($generatedFiles.Count))" -ForegroundColor Yellow
    Write-Host "🔧 Запустите: flutter packages pub run build_runner build --delete-conflicting-outputs" -ForegroundColor Cyan
    $allGood = $false
}

# Проверка 6: Файлы проекта
Write-Host "`n📋 Проверка 6: Файлы проекта" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Gray

$requiredFiles = @(
    "lib\main.dart",
    "lib\services\database_service.dart",
    "lib\providers\work_order_provider.dart",
    "lib\screens\home_screen.dart"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host "✅ Все основные файлы проекта найдены" -ForegroundColor Green
} else {
    Write-Host "❌ Отсутствуют файлы проекта:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor White }
    $allGood = $false
}

# Итоговый результат
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "📊 РЕЗУЛЬТАТ ПРОВЕРКИ" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

if ($allGood) {
    Write-Host "🎉 СИСТЕМА ГОТОВА К ЗАПУСКУ!" -ForegroundColor Green
    Write-Host "`n🚀 Следующие шаги:" -ForegroundColor Cyan
    Write-Host "   1. Запустите: .\quick_start.bat" -ForegroundColor White
    Write-Host "   2. Или выполните: flutter run" -ForegroundColor White
    Write-Host "   3. Откройте приложение в браузере или эмуляторе" -ForegroundColor White
} else {
    Write-Host "⚠️ ТРЕБУЕТСЯ НАСТРОЙКА" -ForegroundColor Yellow
    Write-Host "`n🔧 Выполните следующие действия:" -ForegroundColor Cyan
    
    if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
        Write-Host "   1. Запустите PowerShell от администратора" -ForegroundColor White
        Write-Host "   2. Выполните: .\install_flutter.ps1" -ForegroundColor White
    }
    
    if (-not (Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue)) {
        Write-Host "   3. Выполните: .\setup_postgresql.ps1" -ForegroundColor White
    }
    
    Write-Host "   4. Перезапустите PowerShell" -ForegroundColor White
    Write-Host "   5. Выполните: .\check_system.ps1" -ForegroundColor White
}

Write-Host "`n📋 Дополнительная информация:" -ForegroundColor Cyan
Write-Host "   📖 Подробное руководство: LAUNCH_GUIDE.md" -ForegroundColor White
Write-Host "   🔧 Автоматическая настройка: setup_and_run.ps1" -ForegroundColor White
Write-Host "   ⚡ Быстрый запуск: quick_start.bat" -ForegroundColor White

Write-Host "`n👋 Проверка завершена!" -ForegroundColor Green
