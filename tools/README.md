# Инструменты разработки

Эта папка содержит утилиты для разработки и сборки проекта.

## Файлы

- `build_exe.py` - Скрипт для сборки исполняемого файла с помощью PyInstaller
- `build_exe_gui.py` - GUI версия скрипта сборки
- `run_project.bat` - Batch скрипт для запуска проекта (Windows)
- `run_project.ps1` - PowerShell скрипт для запуска проекта

## Использование

### Сборка исполняемого файла

```bash
python tools/build_exe.py
```

### Запуск проекта

Windows (Command Prompt):
```cmd
tools\run_project.bat
```

Windows (PowerShell):
```powershell
.\tools\run_project.ps1
```

Или напрямую:
```bash
python main.py
```
