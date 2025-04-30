import os


# Список допустимых расширений файлов для включения в карту проекта
VALID_EXTENSIONS = ('.py', '.sql')

# Список папок, которые необходимо игнорировать
IGNORE_FOLDERS = ['.venv',
                  'fonts',
                  'data',
                  '__pycache__']

# Список файлов, которые нужно исключить
IGNORE_FILES = ['temp.py',
                'debug.py',
                'great_map_project.py',
                'greate_requirements.py',
                'print_proekt.py',
                'setup.py',
                'requirements_generator.py']

def create_project_map(project_path):
    project_mapp = []
    for root, dirs, files in os.walk(project_path):
        # Удаляем игнорируемые папки из списка для обхода
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

        # Обрабатываем только нужные файлы
        for file in files:
            # Исключаем файлы из списка IGNORE_FILES и проверяем расширение
            if file.endswith(VALID_EXTENSIONS) and file not in IGNORE_FILES:
                filepath = os.path.join(root, file)
                project_mapp.append(os.path.relpath(filepath, project_path))
    return project_mapp

project_root_path = os.getcwd()  # Корневая директория проекта
output_file = os.path.join(project_root_path, "project_contents.txt")

# Создаем карту проекта
project_map = create_project_map(project_root_path)

with open(output_file, 'w', encoding='utf-8') as f:
    # Записываем карту проекта
    f.write("Карта проекта:\n")
    for file_path in project_map:
        f.write(f"{file_path}\n")
    f.write('\n' + '-' * 80 + '\n\n')

    # Записываем содержимое файлов
    for file_path in project_map:
        full_path = os.path.join(project_root_path, file_path)
        with open(full_path, 'r', encoding='utf-8') as src_file:
            content = src_file.read()

        f.write(f"Путь: {file_path}\n")
        f.write(f"Имя файла: {os.path.basename(file_path)}\n")
        f.write("Содержимое:\n")
        f.write(content)
        f.write('\n' + '-' * 80 + '\n')

print(f"Информация о проекте сохранена в файл: {output_file}")