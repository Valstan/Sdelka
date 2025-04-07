import subprocess
import os
import sys
from chardet import detect

def run_pipreqs_safely(project_path):
    """Безопасный запуск pipreqs с обработкой новых требований к аргументам"""
    try:
        # Определяем кодировку
        encoding = "utf-8"
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "rb") as f:
                        raw = f.read(50000)
                        if result := detect(raw):
                            encoding = result["encoding"]
                            break
            if encoding != "utf-8":
                break

        # Формируем команду согласно новым требованиям
        cmd = [
            sys.executable,
            "-m",
            "pipreqs.pipreqs",
            "--savepath", "requirements.txt",
            "--force",
            f"--encoding={encoding}",
            "--mode=compat",
            "--ignore-errors",
            project_path
        ]

        # Запускаем с обработкой вывода
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        print("Успешно создан requirements.txt")
        print("Вывод:\n", result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Ошибка (код {e.returncode}):")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        print("Рекомендации:")
        print("1. Обновите pipreqs: pip install -U pipreqs")
        print("2. Проверьте пути к файлам")
        print("3. Запустите вручную:")
        print("   ", " ".join(cmd))

if __name__ == "__main__":
    current_dir = os.getcwd()
    run_pipreqs_safely(current_dir)