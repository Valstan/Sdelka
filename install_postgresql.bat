@echo off
echo Установка PostgreSQL через Chocolatey...
echo.

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Права администратора подтверждены.
) else (
    echo ОШИБКА: Этот скрипт должен быть запущен от имени администратора!
    echo Щелкните правой кнопкой мыши по файлу и выберите "Запуск от имени администратора"
    pause
    exit /b 1
)

echo.
echo Устанавливаем Chocolatey...
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

echo.
echo Обновляем переменные окружения...
call refreshenv

echo.
echo Устанавливаем PostgreSQL...
choco install postgresql --yes

echo.
echo Проверяем установку PostgreSQL...
sc query postgresql-x64-16 >nul 2>&1
if %errorLevel% == 0 (
    echo Служба PostgreSQL найдена!
    sc start postgresql-x64-16
    echo Служба PostgreSQL запущена!
) else (
    echo Служба PostgreSQL не найдена. Проверяем другие варианты...
    sc query postgresql >nul 2>&1
    if %errorLevel% == 0 (
        echo Служба PostgreSQL найдена!
        sc start postgresql
        echo Служба PostgreSQL запущена!
    ) else (
        echo Служба PostgreSQL не найдена. Возможно, установка не завершилась успешно.
    )
)

echo.
echo Установка завершена!
echo Для использования PostgreSQL перезапустите командную строку.
echo.
pause

