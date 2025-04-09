import os


def create_project_map(project_root):
    project_map = []
    for root, dirs, files in os.walk(project_root):
        if '.venv' in dirs:
            dirs.remove('.venv')
        if 'fonts' in dirs:
            dirs.remove('fonts')
        if 'data' in dirs:
            dirs.remove('data')
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                project_map.append(os.path.relpath(file_path, project_root))
    return project_map

def write_part(output_path, file_group, project_root, project_map):
    with open(output_path, 'w', encoding='utf-8') as f:
        # Записываем карту проекта
        f.write("Карта проекта:\n")
        for file_path in project_map:
            f.write(f"{file_path}\n")
        f.write('\n' + '-' * 80 + '\n\n')
        # Записываем содержимое файлов группы
        for file_path in file_group:
            full_path = os.path.join(project_root, file_path)
            with open(full_path, 'r', encoding='utf-8') as src_file:
                content = src_file.read()
            f.write(f"Путь: {file_path}\n")
            f.write(f"Имя файла: {os.path.basename(file_path)}\n")
            f.write("Содержимое:\n")
            f.write(content)
            f.write('\n' + '-' * 80 + '\n')

def split_files(project_map):
    # Делим файлы проекта на три группы
    total_files = len(project_map)
    group_size = total_files // 3

    group1 = project_map[:group_size]
    group2 = project_map[group_size:group_size*2]
    group3 = project_map[group_size*2:]

    return group1, group2, group3

def main():
    project_root = os.getcwd()
    project_map = create_project_map(project_root)

    # Разделяем файлы на три группы
    group1, group2, group3 = split_files(project_map)

    # Определяем пути для итоговых файлов
    output_file1 = os.path.join(project_root, "project_contents_part1.txt")
    output_file2 = os.path.join(project_root, "project_contents_part2.txt")
    output_file3 = os.path.join(project_root, "project_contents_part3.txt")

    # Записываем каждую группу в отдельный файл
    write_part(output_file1, group1, project_root, project_map)
    write_part(output_file2, group2, project_root, project_map)
    write_part(output_file3, group3, project_root, project_map)

    print(f"Информация о проекте сохранена в файлы: {output_file1}, {output_file2} и {output_file3}")

if __name__ == "__main__":
    main()