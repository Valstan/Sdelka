@echo off
chcp 65001 >nul
title Сделка v4.0 - Быстрый запуск

echo.
echo ========================================
echo    Сделка v4.0 - Быстрый запуск
echo ========================================
echo.

echo 📁 Переход в папку Flutter проекта...
cd /d "%~dp0flutter_sdelka\sdelka_v4"
if not exist "quick_start.bat" (
    echo ❌ Папка Flutter проекта не найдена!
    echo 🔧 Убедитесь, что вы находитесь в корневой папке проекта Сделка
    echo.
    pause
    exit /b 1
)

echo ✅ Переход в папку Flutter проекта выполнен
echo 🚀 Запуск быстрого запуска...
echo.

call quick_start.bat

echo.
echo 👋 Быстрый запуск завершен
pause
