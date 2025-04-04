import subprocess
import os

def generate_project_requirements(project_path):
    """
    Создает файл requirements.txt, включая только используемые в проекте библиотеки.

    :param project_path: Путь к корневой директории проекта.
    """
    try:
        # Проверяем, установлен ли pipreqs
        subprocess.run(["pip", "show", "pipreqs"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("pipreqs не установлен. Устанавливаем...")
        subprocess.run(["pip", "install", "pipreqs"], check=True)

    try:
        # Генерация файла requirements.txt с использованием pipreqs
        print(f"Генерация requirements.txt для проекта в директории: {project_path}")
        subprocess.run(["pipreqs", project_path, "--force"], check=True)
        print("Файл requirements.txt успешно создан.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации файла requirements.txt: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

if __name__ == "__main__":
    # Укажите путь к вашему проекту
    project_dir = os.getcwd()  # Текущая директория по умолчанию
    generate_project_requirements(project_dir)