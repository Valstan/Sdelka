# File: app/utils/requirements_generator.py
"""
Модуль для безопасной генерации файла requirements.txt.
"""

import logging
import os
import subprocess
import sys

from chardet import detect

logger = logging.getLogger(__name__)


def detect_encoding(file_path: str) -> str:
    """
    Определяет кодировку файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Обнаруженная кодировка
    """
    with open(file_path, "rb") as f:
        raw_data = f.read(50000)
    return detect(raw_data)["encoding"] or "utf-8"


def get_common_encoding(project_path: str) -> str:
    """
    Определяет наиболее распространенную кодировку в проекте.

    Args:
        project_path: Путь к корню проекта

    Returns:
        Наиболее распространенная кодировка
    """
    encodings = {}

    for root, _, files in os.walk(project_path):
        if '.venv' in root:
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                encoding = detect_encoding(file_path)
                encodings[encoding] = encodings.get(encoding, 0) + 1

    return max(encodings, key=encodings.get) if encodings else "utf-8"


def run_pipreqs_safely(project_path: str) -> None:
    """
    Безопасно запускает pipreqs с обработкой кодировки и других параметров.

    Args:
        project_path: Путь к корню проекта
    """
    try:
        common_encoding = get_common_encoding(project_path)
        logger.info(f"Используемая кодировка: {common_encoding}")

        cmd = [
            sys.executable,
            "-m",
            "pipreqs.pipreqs",
            "--savepath", "requirements.txt",
            "--force",
            f"--encoding={common_encoding}",
            "--mode=compat",
            "--ignore-errors",
            project_path
        ]

        logger.info("Запуск команды: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        logger.info("Успешно создан requirements.txt")
        logger.debug("STDOUT: %s", result.stdout)

    except subprocess.CalledProcessError as e:
        logger.error("Ошибка при выполнении pipreqs")
        logger.error("STDOUT: %s", e.stdout)
        logger.error("STDERR: %s", e.stderr)

        print("\nРекомендации:")
        print("1. Обновите pipreqs: pip install -U pipreqs")
        print("2. Проверьте пути к файлам")
        print("3. Запустите вручную:")
        print(f"   {' '.join(cmd)}")


if __name__ == "__main__":
    current_dir = os.getcwd()
    run_pipreqs_safely(current_dir)