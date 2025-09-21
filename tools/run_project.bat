@echo off
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo Запуск проекта Sdelka...
python main.py

pause
