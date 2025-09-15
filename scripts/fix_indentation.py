#!/usr/bin/env python3
"""
Скрипт для исправления ошибок отступов в try блоках
"""
import re
import os


def fix_try_indentation(file_path):
    """Исправляет ошибки отступов в try блоках"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Паттерн для поиска try: с неправильным отступом следующей строки
    pattern = r"(\s+)try:\n(\s*)([^ \s])"

    def fix_match(match):
        indent = match.group(1)
        next_line_indent = match.group(2)
        next_char = match.group(3)

        # Если следующая строка не имеет правильного отступа
        if len(next_line_indent) <= len(indent):
            return f"{indent}try:\n{indent}    {next_char}"
        return match.group(0)

    # Применяем исправления
    fixed_content = re.sub(pattern, fix_match, content)

    # Дополнительная проверка для случаев, когда строка после try: не имеет отступа вообще
    pattern2 = r"(\s+)try:\n([^ \s])"

    def fix_match2(match):
        indent = match.group(1)
        next_char = match.group(2)
        return f"{indent}try:\n{indent}    {next_char}"

    fixed_content = re.sub(pattern2, fix_match2, fixed_content)

    if fixed_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)
        print(f"Исправлен файл: {file_path}")
        return True
    return False


if __name__ == "__main__":
    file_path = "gui/forms/work_order_form.py"
    if os.path.exists(file_path):
        fix_try_indentation(file_path)
    else:
        print(f"Файл {file_path} не найден")
