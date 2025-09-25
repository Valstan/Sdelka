@echo off
chcp 65001 >nul
title Сделка v4.0 - Быстрый запуск

echo.
echo ========================================
echo    Сделка v4.0 - Быстрый запуск
echo ========================================
echo.

echo 🔍 Проверка Flutter SDK...
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flutter SDK не найден!
    echo 🔧 Запустите PowerShell от имени администратора и выполните:
    echo    .\setup_and_run.ps1
    echo.
    pause
    exit /b 1
)

echo ✅ Flutter SDK найден
echo.

echo 🔍 Проверка PostgreSQL...
sc query postgresql* >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PostgreSQL не найден!
    echo 🔧 Запустите PowerShell от имени администратора и выполните:
    echo    .\setup_and_run.ps1
    echo.
    pause
    exit /b 1
)

echo ✅ PostgreSQL найден
echo.

echo 📦 Установка зависимостей...
flutter pub get
if %errorlevel% neq 0 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены
echo.

echo 🔧 Генерация кода...
flutter packages pub run build_runner build --delete-conflicting-outputs
if %errorlevel% neq 0 (
    echo ⚠️ Предупреждения при генерации кода (возможно нормально)
)

echo.
echo 🚀 Запуск приложения...
echo ========================================
echo.

flutter run

echo.
echo 👋 Приложение завершено
pause
