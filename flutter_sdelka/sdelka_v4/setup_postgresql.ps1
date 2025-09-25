# Скрипт автоматической установки и настройки PostgreSQL
# Запускать от имени администратора в PowerShell

Write-Host "🐘 Установка и настройка PostgreSQL для проекта Сделка v4.0" -ForegroundColor Green

# Проверка архитектуры системы
$arch = (Get-WmiObject -Class Win32_Processor).Architecture
if ($arch -eq 0) {
    $postgresArch = "x64"
} elseif ($arch -eq 5) {
    $postgresArch = "x64"
} else {
    $postgresArch = "x86"
}

Write-Host "📋 Обнаружена архитектура: $postgresArch" -ForegroundColor Yellow

# URL для загрузки PostgreSQL
$postgresUrl = "https://get.enterprisedb.com/postgresql/postgresql-15.5-1-windows-x64.exe"
$installerPath = "$env:TEMP\postgresql_installer.exe"

# Проверка, установлен ли уже PostgreSQL
$postgresService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($postgresService) {
    Write-Host "✅ PostgreSQL уже установлен" -ForegroundColor Green
    Write-Host "🔧 Настройка базы данных для проекта..." -ForegroundColor Yellow
} else {
    Write-Host "⬇️ Загрузка PostgreSQL 15.5..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $postgresUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "✅ PostgreSQL загружен" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ошибка загрузки PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "🌐 Попробуйте скачать вручную с: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "📦 Запуск установки PostgreSQL..." -ForegroundColor Yellow
    Write-Host "⚠️ ВНИМАНИЕ: В мастере установки:" -ForegroundColor Red
    Write-Host "   - Пароль для пользователя postgres: sdelka123" -ForegroundColor Cyan
    Write-Host "   - Порт: 5432 (по умолчанию)" -ForegroundColor Cyan
    Write-Host "   - Установите все компоненты" -ForegroundColor Cyan
    
    # Запуск установщика
    Start-Process -FilePath $installerPath -Wait
    
    # Очистка
    Remove-Item $installerPath -Force
}

# Настройка переменных окружения
$pgPath = "C:\Program Files\PostgreSQL\15\bin"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$pgPath*") {
    $newPath = $currentPath + ";" + $pgPath
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
    Write-Host "✅ PostgreSQL добавлен в PATH" -ForegroundColor Green
}

# Ожидание запуска службы PostgreSQL
Write-Host "⏳ Ожидание запуска службы PostgreSQL..." -ForegroundColor Yellow
$timeout = 60
$elapsed = 0
do {
    Start-Sleep -Seconds 2
    $elapsed += 2
    $service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-Host "✅ Служба PostgreSQL запущена" -ForegroundColor Green
        break
    }
} while ($elapsed -lt $timeout)

if ($elapsed -ge $timeout) {
    Write-Host "⚠️ Служба PostgreSQL не запустилась автоматически" -ForegroundColor Yellow
    Write-Host "🔧 Попробуйте запустить вручную: services.msc" -ForegroundColor Cyan
}

# Создание базы данных и пользователя
Write-Host "🗄️ Настройка базы данных для проекта..." -ForegroundColor Yellow

# SQL скрипт для настройки
$sqlScript = @"
-- Создание базы данных
CREATE DATABASE sdelka_v4;

-- Создание пользователя
CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;

-- Переключение на новую базу данных
\c sdelka_v4

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sdelka_user;

-- Создание таблиц
CREATE TABLE IF NOT EXISTS employees (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  position VARCHAR(255) NOT NULL,
  department VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  email VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  unit VARCHAR(50) NOT NULL,
  article VARCHAR(100),
  category VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS work_types (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  unit VARCHAR(50) NOT NULL,
  standard_price DECIMAL(10,2),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS work_orders (
  id VARCHAR(36) PRIMARY KEY,
  number VARCHAR(50) NOT NULL UNIQUE,
  date DATE NOT NULL,
  department VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS work_order_items (
  id VARCHAR(36) PRIMARY KEY,
  work_order_id VARCHAR(36) NOT NULL,
  employee_id VARCHAR(36) NOT NULL,
  product_id VARCHAR(36) NOT NULL,
  work_type_id VARCHAR(36) NOT NULL,
  quantity INTEGER NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (employee_id) REFERENCES employees(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (work_type_id) REFERENCES work_types(id)
);

-- Предоставление прав на новые таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdelka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdelka_user;
"@

# Сохранение SQL скрипта во временный файл
$sqlFile = "$env:TEMP\setup_sdelka_db.sql"
$sqlScript | Out-File -FilePath $sqlFile -Encoding UTF8

# Выполнение SQL скрипта
Write-Host "🔧 Выполнение SQL скрипта..." -ForegroundColor Yellow
try {
    # Используем psql для выполнения скрипта
    $env:PGPASSWORD = "sdelka123"
    & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -f $sqlFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ База данных настроена успешно" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Возможны предупреждения при настройке БД" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка выполнения SQL скрипта: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "🔧 Выполните настройку вручную:" -ForegroundColor Cyan
    Write-Host "   psql -U postgres -f $sqlFile" -ForegroundColor White
}

# Очистка временных файлов
Remove-Item $sqlFile -Force

# Проверка подключения
Write-Host "🔍 Проверка подключения к базе данных..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = "sdelka_password"
    $result = & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -U sdelka_user -d sdelka_v4 -c "SELECT current_database(), current_user;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Подключение к базе данных успешно" -ForegroundColor Green
        Write-Host "📊 Результат: $result" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️ Не удалось подключиться к базе данных" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка проверки подключения" -ForegroundColor Yellow
}

Write-Host "🎉 Настройка PostgreSQL завершена!" -ForegroundColor Green
Write-Host "📋 Информация о подключении:" -ForegroundColor Cyan
Write-Host "   Host: localhost" -ForegroundColor White
Write-Host "   Port: 5432" -ForegroundColor White
Write-Host "   Database: sdelka_v4" -ForegroundColor White
Write-Host "   Username: sdelka_user" -ForegroundColor White
Write-Host "   Password: sdelka_password" -ForegroundColor White

Write-Host "📋 Следующие шаги:" -ForegroundColor Cyan
Write-Host "   1. Перезапустите PowerShell" -ForegroundColor White
Write-Host "   2. Запустите: flutter pub get" -ForegroundColor White
Write-Host "   3. Запустите: flutter run" -ForegroundColor White
