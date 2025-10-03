"""Скрипт для запуска тестов."""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Запускает все тесты проекта."""
    project_root = Path(__file__).parent
    
    print("Запуск тестов проекта Сделка...")
    print(f"Корневая директория: {project_root}")
    
    # Команда для запуска pytest
    cmd = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "-v",  # подробный вывод
        "--tb=short",  # короткий traceback
        "--color=yes",  # цветной вывод
    ]
    
    try:
        print("Выполнение команды:", " ".join(cmd))
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("Все тесты прошли успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Тесты завершились с ошибкой (код: {e.returncode})")
        return False
        
    except FileNotFoundError:
        print("pytest не найден. Установите его: pip install pytest")
        return False


def run_specific_test(test_file: str):
    """Запускает конкретный тест."""
    project_root = Path(__file__).parent
    test_path = project_root / "tests" / test_file
    
    if not test_path.exists():
        print(f"❌ Файл теста не найден: {test_path}")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    
    try:
        print(f"Запуск теста: {test_file}")
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("Тест прошел успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Тест завершился с ошибкой (код: {e.returncode})")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Запуск конкретного теста
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # Запуск всех тестов
        success = run_tests()
    
    sys.exit(0 if success else 1)
