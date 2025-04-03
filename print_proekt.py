import os

def create_project_map(project_root):
    project_map = []
    for root, dirs, files in os.walk(project_root):
        if '.venv' in dirs:
            dirs.remove('.venv')  # Исключаем папку из сканирования
        if 'fonts' in dirs:
            dirs.remove('fonts')  # Исключаем папку из сканирования
        if 'data' in dirs:
            dirs.remove('data')  # Исключаем папку из сканирования
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                project_map.append(os.path.relpath(file_path, project_root))
    return project_map

project_root = os.getcwd()  # Корневая директория проекта
output_file = os.path.join(project_root, "project_contents.txt")

# Создаем карту проекта
project_map = create_project_map(project_root)

with open(output_file, 'w', encoding='utf-8') as f:
    # Записываем карту проекта
    f.write("Карта проекта:\n")
    for file_path in project_map:
        f.write(f"{file_path}\n")
    f.write('\n' + '-' * 80 + '\n\n')

    # Записываем содержимое файлов
    for file_path in project_map:
        full_path = os.path.join(project_root, file_path)
        with open(full_path, 'r', encoding='utf-8') as src_file:
            content = src_file.read()

        f.write(f"Путь: {file_path}\n")
        f.write(f"Имя файла: {os.path.basename(file_path)}\n")
        f.write("Содержимое:\n")
        f.write(content)
        f.write('\n' + '-' * 80 + '\n')

print(f"Информация о проекте сохранена в файл: {output_file}")