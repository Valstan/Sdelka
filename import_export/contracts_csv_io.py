from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from db.queries import upsert_contract
from utils.text import normalize_for_search

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> str | None:
    """Парсит дату из строки в формате DD.MM.YYYY или DD.MM."""
    if not date_str or date_str.strip() == "":
        return None
    
    date_str = date_str.strip()
    
    # Формат DD.MM.YYYY
    if len(date_str) == 10 and date_str.count('.') == 2:
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Формат DD.MM (добавляем текущий год)
    elif len(date_str) == 5 and date_str.count('.') == 1:
        try:
            current_year = datetime.now().year
            date_with_year = f"{date_str}.{current_year}"
            return datetime.strptime(date_with_year, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Если не удалось распарсить, возвращаем как есть
    logger.warning(f"Не удалось распарсить дату: {date_str}")
    return date_str


def clean_text(text: str) -> str:
    """Очищает текст от лишних символов и пробелов."""
    if not text:
        return ""
    return text.strip().replace('"', '').replace('"', '')


def import_contracts_from_csv(conn, file_path: str | Path) -> tuple[int, int]:
    """
    Импортирует контракты из CSV файла.
    
    Args:
        conn: Соединение с базой данных
        file_path: Путь к CSV файлу
        
    Returns:
        tuple[int, int]: (количество импортированных, количество обновленных)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    imported_count = 0
    updated_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            # Определяем разделитель (проверяем первую строку)
            first_line = file.readline().strip()
            file.seek(0)
            
            if ';' in first_line:
                delimiter = ';'
            elif ',' in first_line:
                delimiter = ','
            else:
                delimiter = '\t'
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            # Проверяем наличие обязательных колонок
            required_columns = ['Наименование', 'Номер контракта']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            if missing_columns:
                raise ValueError(f"В файле отсутствуют обязательные колонки: {missing_columns}")
            
            for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, так как 1 - заголовок
                try:
                    # Извлекаем данные из строки
                    name = clean_text(row.get('Наименование', ''))
                    contract_type = clean_text(row.get('Вид контракта', ''))
                    executor = clean_text(row.get('Исполнитель', ''))
                    igk = clean_text(row.get('ИГК', ''))
                    contract_number = clean_text(row.get('Номер контракта', ''))
                    bank_account = clean_text(row.get('Отдельный счет', ''))
                    start_date_str = clean_text(row.get('Дата заключения контракта', ''))
                    end_date_str = clean_text(row.get('Плановая дата исполнения контракта', ''))
                    comment = clean_text(row.get('Комментарий', ''))
                    
                    # Пропускаем пустые строки
                    if not name and not contract_number:
                        continue
                    
                    # Генерируем код контракта
                    if contract_number:
                        code = contract_number
                    elif name:
                        code = name
                    else:
                        code = f"КОНТРАКТ_{row_num}"
                    
                    # Парсим даты
                    start_date = parse_date(start_date_str)
                    end_date = parse_date(end_date_str)
                    
                    # Создаем или обновляем контракт
                    contract_id = upsert_contract(
                        conn=conn,
                        code=code,
                        name=name if name else None,
                        contract_type=contract_type if contract_type else None,
                        executor=executor if executor else None,
                        igk=igk if igk else None,
                        contract_number=contract_number if contract_number else None,
                        bank_account=bank_account if bank_account else None,
                        start_date=start_date,
                        end_date=end_date,
                        description=comment if comment else None
                    )
                    
                    if contract_id:
                        if row.get('Есть файлы') == '1':
                            logger.info(f"Контракт импортирован: {name or code}")
                        else:
                            logger.debug(f"Контракт импортирован: {name or code}")
                        
                        imported_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка при импорте строки {row_num}: {e}")
                    logger.error(f"Содержимое строки: {row}")
                    continue
    
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise
    
    logger.info(f"Импорт завершен. Импортировано: {imported_count}, обновлено: {updated_count}")
    return imported_count, updated_count


def export_contracts_to_csv(conn, file_path: str | Path) -> Path:
    """
    Экспортирует контракты в CSV файл.
    
    Args:
        conn: Соединение с базой данных
        file_path: Путь для сохранения CSV файла
        
    Returns:
        Path: Путь к созданному файлу
    """
    file_path = Path(file_path)
    
    # Получаем все контракты
    contracts = conn.execute("""
        SELECT code, name, contract_type, executor, igk, contract_number, 
               bank_account, start_date, end_date, description
        FROM contracts 
        ORDER BY code
    """).fetchall()
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Записываем заголовки
        headers = [
            'Есть файлы', 'Наименование', 'Вид контракта', 'Исполнитель', 'ИГК',
            'Номер контракта', 'Отдельный счет', 'Дата заключения контракта',
            'Плановая дата исполнения контракта', 'Комментарий'
        ]
        writer.writerow(headers)
        
        # Записываем данные
        for contract in contracts:
            row = [
                '1',  # Есть файлы (по умолчанию)
                contract['name'] or '',
                contract['contract_type'] or '',
                contract['executor'] or '',
                contract['igk'] or '',
                contract['contract_number'] or contract['code'],
                contract['bank_account'] or '',
                contract['start_date'] or '',
                contract['end_date'] or '',
                contract['description'] or ''
            ]
            writer.writerow(row)
    
    logger.info(f"Экспорт завершен. Файл сохранен: {file_path}")
    return file_path


def generate_contracts_template(file_path: str | Path) -> Path:
    """
    Создает шаблон CSV файла для импорта контрактов.
    
    Args:
        file_path: Путь для сохранения шаблона
        
    Returns:
        Path: Путь к созданному файлу
    """
    file_path = Path(file_path)
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Записываем заголовки
        headers = [
            'Есть файлы', 'Наименование', 'Вид контракта', 'Исполнитель', 'ИГК',
            'Номер контракта', 'Отдельный счет', 'Дата заключения контракта',
            'Плановая дата исполнения контракта', 'Комментарий'
        ]
        writer.writerow(headers)
        
        # Записываем примеры данных
        examples = [
            ['1', 'ОВК 239/13/ГОЗ-23', 'Гособоронзаказ (ГОЗ)', 'МАЛМЫЖСКИЙ РЕМЗАВОД АО', '2325187913551442245231239', '2325187913551442245231239/739-1/55/13983/5125/2324/13/ГОЗ-23', '40706810003000140827, Приволжский ф-л ПАО "Промсвязьбанк"', '24.07.2023', '31.12.2023', ''],
            ['1', 'УТМ 239/27/ГОЗ-24', 'Гособоронзаказ (ГОЗ)', 'МАЛМЫЖСКИЙ РЕМЗАВОД АО', '2325187913551442245231239', '2325187913551442245231239/27/ГОЗ-24', '40706810003000198992, Приволжский ф-л ПАО "Промсвязьбанк"', '14.06.2024', '31.12.2025', ''],
            ['0', 'Пример контракта', 'Коммерческий', 'ООО Пример', '123456789', 'ДОГ-001/2024', 'Счет в банке', '01.01.2024', '31.12.2024', 'Комментарий к контракту']
        ]
        
        for example in examples:
            writer.writerow(example)
    
    logger.info(f"Шаблон создан: {file_path}")
    return file_path
