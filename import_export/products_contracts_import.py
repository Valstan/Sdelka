"""
Модуль импорта изделий с привязкой к контрактам из CSV файлов
Основан на анализе оборотно-сальдовой ведомости по счету 002
"""

import csv
import re
from pathlib import Path
from typing import Dict, Tuple

from db.sqlite import get_connection
from db import queries as q


def parse_product_info(text: str) -> Tuple[str, str]:
    """
    Парсит строку с информацией об изделии
    Возвращает (наименование, номер)

    Примеры:
    "Двигатель В-46-2С1 № 2Ж11АТ1789 БУ" -> ("Двигатель В-46-2С1", "2Ж11АТ1789")
    "Двигатель В-46 № Е06АТ7397 БУ" -> ("Двигатель В-46", "Е06АТ7397")
    "Двигатель 4ч 8,5/11 № 7706313 БУ" -> ("Двигатель 4ч 8,5/11", "7706313")
    "Двигатель В-55 У № 307Д5012 БУ" -> ("Двигатель В-55 У", "307Д5012")
    """
    # Паттерн для поиска номера изделия - более гибкий
    number_pattern = r"№\s*([A-Z0-9А-Я\-\.\/]+)"

    match = re.search(number_pattern, text)
    if match:
        number = match.group(1).strip()
        # Убираем номер и "БУ" из наименования
        name = re.sub(number_pattern, "", text).strip()
        name = re.sub(r"\s*БУ\s*$", "", name).strip()
        return name, number

    # Если номер не найден, возвращаем как есть
    return text.strip(), ""


def parse_contract_info(text: str) -> Tuple[str, str]:
    """
    Парсит строку с информацией о контракте
    Возвращает (наименование контракта, код)

    Примеры:
    "Договор №2224187909991442245221303 ГРАНИТ (2024) БУ" -> ("ГРАНИТ (2024)", "2224187909991442245221303")
    "Договор № 2325187913551442245231239/23 (ОВК 2024) БУ" -> ("ОВК 2024", "2325187913551442245231239/23")
    "Договор подряда №1 от 21.02.2025 БУ" -> ("Договор подряда от 21.02.2025", "1")
    "Договор 2425187912361412245238660/09/ГОЗ-25 от 26.03.2025(ОВК 2025) БУ" -> ("ГОЗ-25 от 26.03.2025(ОВК 2025)", "2425187912361412245238660/09")
    """
    # Паттерн для поиска номера договора - более гибкий
    contract_pattern = r"№\s*([0-9\/\-]+)"

    match = re.search(contract_pattern, text)
    if match:
        contract_number = match.group(1).strip()
        # Убираем номер и "БУ" из наименования
        name = re.sub(contract_pattern, "", text).strip()
        name = re.sub(r"Договор\s*", "", name).strip()
        name = re.sub(r"^\s*[-\(\)\s]+", "", name).strip()
        name = re.sub(r"\s*БУ\s*$", "", name).strip()
        return name, contract_number

    # Если номер не найден, возвращаем как есть
    return text.strip(), ""


def clean_text(text: str) -> str:
    """Очищает текст от лишних символов"""
    if not text:
        return ""
    # Убираем "БУ" и другие служебные символы
    cleaned = text.strip().replace('"', "").replace(";", "")
    cleaned = re.sub(r"\s*БУ\s*$", "", cleaned).strip()
    return cleaned


def import_products_from_contracts_csv(
    csv_path: str, progress_callback=None
) -> Dict[str, int]:
    """
    Импортирует изделия с привязкой к контрактам из CSV файла

    Args:
        csv_path: Путь к CSV файлу
        progress_callback: Функция для отображения прогресса (step, total, note)

    Returns:
        Словарь с результатами: {"products": count, "contracts": count, "errors": count}
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Файл не найден: {csv_path}")

    # Счетчики
    stats = {"products": 0, "contracts": 0, "errors": 0}

    # Структуры для хранения данных
    products_data = {}  # {product_key: {name, number, contract_name, contract_number}}
    contracts_data = {}  # {contract_key: {name, number, executor, date}}

    # Читаем CSV файл
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as file:
        reader = csv.reader(file, delimiter=";")
        rows = list(reader)

    total_rows = len(rows)
    current_row = 0

    # Парсим данные по группам
    current_group = {"product": None, "contract": None, "executor": None, "date": None}

    for row in rows:
        current_row += 1
        if progress_callback:
            progress_callback(
                current_row, total_rows, f"Обработка строки {current_row}/{total_rows}"
            )

        # Объединяем все ячейки в одну строку для анализа
        full_text = " ".join([str(cell) for cell in row if cell])

        # Пропускаем пустые строки и служебные
        if not full_text.strip():
            continue

        # Ищем изделие (строки, содержащие "Двигатель" и номер)
        if "Двигатель" in full_text and "№" in full_text:
            product_name, product_number = parse_product_info(full_text)
            if product_name and product_number:
                # Если у нас уже есть изделие, сохраняем предыдущую группу
                if current_group["product"]:
                    _save_current_group(current_group, products_data, contracts_data)

                # Начинаем новую группу
                current_group = {
                    "product": {"name": product_name, "number": product_number},
                    "contract": None,
                    "executor": None,
                    "date": None,
                }
            continue

        # Ищем контрагента (организацию)
        if any(
            keyword in full_text
            for keyword in [
                "ООО",
                "АО",
                "ОАО",
                "ЗАО",
                "РПТП",
                "КСК",
                "УРАЛТРАНСМАШ",
                "МК ВИТЯЗЬ",
                "78 ЦЕНТРАЛЬНАЯ ИНЖЕНЕРНАЯ БАЗА",
                "МПЗ",
            ]
        ):
            current_group["executor"] = clean_text(full_text)
            continue

        # Ищем договор
        if "Договор" in full_text or "договор" in full_text:
            contract_name, contract_number = parse_contract_info(full_text)
            if contract_name:
                current_group["contract"] = {
                    "name": contract_name,
                    "number": contract_number,
                }
            continue

        # Ищем дату (формат ДД.ММ.ГГГГ или ДД.ММ)
        date_pattern = r"(\d{2}\.\d{2}\.?\d{4}?)"
        date_match = re.search(date_pattern, full_text)
        if date_match:
            current_date = date_match.group(1)
            current_group["date"] = current_date
            continue

    # Сохраняем последнюю группу
    if current_group["product"]:
        _save_current_group(current_group, products_data, contracts_data)

    # Импортируем данные в базу
    if progress_callback:
        progress_callback(0, 1, "Импорт контрактов...")

    with get_connection() as conn:
        # Сначала импортируем контракты
        for contract_key, contract_data in contracts_data.items():
            try:
                # Создаем или обновляем контракт
                contract_id = q.upsert_contract(
                    conn,
                    code=contract_data["number"] or f"CONTRACT_{contract_key}",
                    start_date=contract_data["date"],
                    end_date=None,
                    description=f"Импортирован из CSV: {contract_data['name']}",
                    name=contract_data["name"],
                    contract_type="Договор",
                    executor=contract_data["executor"],
                    igk=None,
                    contract_number=contract_data["number"],
                    bank_account=None,
                )
                stats["contracts"] += 1
            except Exception:
                stats["errors"] += 1

        if progress_callback:
            progress_callback(0, 1, "Импорт изделий...")

        # Затем импортируем изделия
        for product_key, product_data in products_data.items():
            try:
                # Находим контракт по имени
                contract_id = None
                if product_data["contract_name"]:
                    contract = q.get_contract_by_name(
                        conn, product_data["contract_name"]
                    )
                    if contract:
                        contract_id = contract["id"]

                # Если контракт не найден, создаем "Без контракта"
                if not contract_id:
                    no_contract = q.get_contract_by_code(conn, "Без контракта")
                    if not no_contract:
                        contract_id = q.insert_contract(
                            conn,
                            "Без контракта",
                            None,
                            None,
                            "Автоматически создан для изделий без контракта",
                            name="Без контракта",
                            contract_type="Системный",
                            executor="Система",
                        )
                    else:
                        contract_id = no_contract["id"]

                # Создаем или обновляем изделие
                q.upsert_product(
                    conn,
                    name=product_data["name"],
                    product_no=product_data["number"],
                    contract_id=contract_id,
                )
                stats["products"] += 1
            except Exception:
                stats["errors"] += 1

    return stats


def _save_current_group(current_group, products_data, contracts_data):
    """Сохраняет текущую группу данных"""
    if not current_group["product"]:
        return

    product_key = (
        f"{current_group['product']['name']}_{current_group['product']['number']}"
    )

    # Сохраняем изделие
    if product_key not in products_data:
        products_data[product_key] = {
            "name": current_group["product"]["name"],
            "number": current_group["product"]["number"],
            "contract_name": (
                current_group["contract"]["name"] if current_group["contract"] else None
            ),
            "contract_number": (
                current_group["contract"]["number"]
                if current_group["contract"]
                else None
            ),
        }

    # Сохраняем контракт если есть
    if current_group["contract"]:
        contract_key = (
            f"{current_group['contract']['name']}_{current_group['contract']['number']}"
        )
        if contract_key not in contracts_data:
            contracts_data[contract_key] = {
                "name": current_group["contract"]["name"],
                "number": current_group["contract"]["number"],
                "executor": current_group["executor"] or "Неизвестно",
                "date": current_group["date"] or "",
            }


def generate_products_contracts_template(output_path: str) -> str:
    """
    Создает шаблон CSV файла для импорта изделий с контрактами

    Args:
        output_path: Путь для сохранения шаблона

    Returns:
        Путь к созданному файлу
    """
    template_data = [
        [
            "Двигатель В-46-2С1 № 2Ж11АТ1789",
            "РПТП ГРАНИТ АО",
            "Договор №2224187909991442245221303 ГРАНИТ (2024)",
            "04.07.2024",
        ],
        [
            "Двигатель В-46 № Е06АТ7397",
            "ОВК ООО",
            "Договор № 2325187913551442245231239/23 (ОВК 2024)",
            "14.08.2023",
        ],
        [
            "Двигатель В-55 У № 307Д5012",
            "УРАЛТРАНСМАШ АО",
            "2224187314431432245222903 Д/С №2 ( УТМ 2024)",
            "29.05.2023",
        ],
        [
            "Двигатель 4ч 8,5/11 № 7706313",
            "ОВК ООО",
            "Договор № 2325187913551442245231239/23 (ОВК 2024)",
            "14.08.2023",
        ],
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Изделие", "Контрагент", "Договор", "Дата"])
        writer.writerows(template_data)

    return output_path


if __name__ == "__main__":
    # Тестирование модуля
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        try:
            result = import_products_from_contracts_csv(csv_file)
            print("Импорт завершен:")
            print(f"  Изделий: {result['products']}")
            print(f"  Контрактов: {result['contracts']}")
            print(f"  Ошибок: {result['errors']}")
        except Exception as e:
            print(f"Ошибка импорта: {e}")
    else:
        print("Использование: python products_contracts_import.py <путь_к_csv>")
