from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence

from config.settings import CONFIG
from db import queries as q
from services.validation import validate_date, validate_positive_quantity

logger = logging.getLogger(__name__)


@dataclass
class WorkOrderItemInput:
    job_type_id: int
    quantity: float


@dataclass
class WorkOrderWorkerInput:
    worker_id: int
    worker_name: str
    amount: float | None = None


@dataclass
class WorkOrderInput:
    order_no: int | None = None
    date: str
    product_id: int | None
    contract_id: int
    items: Sequence[WorkOrderItemInput]
    workers: Sequence[WorkOrderWorkerInput]  # Изменено с worker_ids на workers


def _round_rub(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_work_order(conn: sqlite3.Connection, data: WorkOrderInput) -> int:
    validate_date(data.date)
    if not data.items:
        raise ValueError("Наряд должен содержать хотя бы одну строку работ")
    # Провалидируем наличие контракта и изделия, чтобы не ловить FK ошибку
    c_row = conn.execute("SELECT id FROM contracts WHERE id = ?", (data.contract_id,)).fetchone()
    if not c_row:
        raise ValueError("Выбранный контракт не найден. Выберите контракт из списка.")
    if data.product_id is not None:
        p_row = conn.execute("SELECT id FROM products WHERE id = ?", (data.product_id,)).fetchone()
        if not p_row:
            raise ValueError("Выбранное изделие не найдено. Выберите изделие из списка или очистьте поле.")

    total = Decimal("0")
    line_values: list[tuple[int, float, float, float]] = []

    for item in data.items:
        validate_positive_quantity(item.quantity)
        jt = conn.execute("SELECT id, price FROM job_types WHERE id = ?", (item.job_type_id,)).fetchone()
        if not jt:
            raise ValueError(f"Вид работ id={item.job_type_id} не найден")
        unit_price = Decimal(str(jt["price"]))
        line_amount = _round_rub(unit_price * Decimal(str(item.quantity)))
        total += line_amount
        line_values.append((item.job_type_id, float(item.quantity), float(unit_price), float(line_amount)))

    total = _round_rub(total)

    # Определяем номер наряда: из данных или следующий по счетчику
    order_no = int(data.order_no) if (getattr(data, "order_no", None) not in (None, "")) else q.next_order_no(conn)
    # Проверим уникальность, чтобы не уткнуться в UNIQUE
    if q.order_no_in_use(conn, order_no):
        raise ValueError(f"Номер наряда {order_no} уже используется. Укажите другой номер.")
    work_order_id = q.insert_work_order(conn, order_no, data.date, data.product_id, data.contract_id, float(total))

    for (job_type_id, quantity, unit_price, line_amount) in line_values:
        q.insert_work_order_item(conn, work_order_id, job_type_id, quantity, unit_price, line_amount)

    # Проверим работников
    if not data.workers:
        raise ValueError("Добавьте работников в бригаду")
    
    # Убираем дубликаты и проверяем корректность ID
    unique_workers = []
    seen_ids = set()
    for worker in data.workers:
        if worker.worker_id not in seen_ids:
            unique_workers.append(worker)
            seen_ids.add(worker.worker_id)
    
    if len(unique_workers) != len(data.workers):
        logger.warning("Обнаружены дублирующиеся ID работников: %s -> %s", 
                      [w.worker_id for w in data.workers], [w.worker_id for w in unique_workers])
    
    # Разделяем работников на существующих (положительные ID) и ручно добавленных (отрицательные ID)
    existing_workers = [w for w in unique_workers if w.worker_id > 0]
    manual_workers = [w for w in unique_workers if w.worker_id < 0]
    
    # Проверяем корректность ID
    for worker in unique_workers:
        if not isinstance(worker.worker_id, int):
            raise ValueError(f"Некорректный ID работника: {worker.worker_id}")
    
    # Проверяем существование работников в базе (только для положительных ID)
    if existing_workers:
        existing_ids = [w.worker_id for w in existing_workers]
        placeholders = ",".join(["?"] * len(existing_ids))
        found = conn.execute(
            f"SELECT id, status FROM workers WHERE id IN ({placeholders})",
            tuple(existing_ids),
        ).fetchall()
        found_map = {int(row["id"]): (row["status"] or "Работает") for row in found}
        # Проверка наличия
        if len(found_map) != len(existing_ids):
            missing_ids = set(existing_ids) - set(found_map.keys())
            logger.error("Работники не найдены в базе: %s", missing_ids)
            raise ValueError(f"Работники с ID {missing_ids} не найдены в базе данных. Выберите работников из списка.")
        # Блокировать уволенных
        fired_ids = [wid for wid in existing_ids if found_map.get(wid, "Работает") != "Работает"]
        if fired_ids:
            raise ValueError(f"Нельзя добавить уволенных работников в наряд: {fired_ids}")
    
    # Для ручно добавленных работников (отрицательные ID) создаем/находим записи в базе
    final_worker_ids: list[int] = []
    # Сохраняем заданные суммы по исходному ID (положительному или отрицательному)
    specified_by_orig: dict[int, Decimal] = {}
    for w in unique_workers:
        if w.amount is not None:
            try:
                val = _round_rub(Decimal(str(w.amount)))
            except Exception:
                raise ValueError("Некорректная сумма распределения для работника")
            if val < 0:
                raise ValueError("Сумма для работника не может быть отрицательной")
            specified_by_orig[w.worker_id] = val

    # Добавляем существующих работников
    final_worker_ids.extend([w.worker_id for w in existing_workers])

    # Для ручно добавленных работников пытаемся найти по ФИО, иначе создаем нового
    orig_to_new: dict[int, int] = {}
    if manual_workers:
        counter = 1
        for worker in manual_workers:
            # Сначала ищем существующего по ФИО (без учета регистра)
            found = q.get_worker_by_full_name(conn, worker.worker_name)
            if found:
                wid = int(found["id"])
                orig_to_new[worker.worker_id] = wid
                final_worker_ids.append(wid)
                logger.info("Найден существующий работник по имени '%s': id=%s", worker.worker_name, wid)
                continue
            # Создаем нового с уникальным табельным номером, привязанным к наряду
            personnel_no = f"TEMP_{work_order_id}_{counter}"
            counter += 1
            temp_worker_id = int(q.insert_worker(conn, worker.worker_name, None, None, personnel_no))
            orig_to_new[worker.worker_id] = temp_worker_id
            final_worker_ids.append(temp_worker_id)
            logger.info("Создан временный работник: %s (id=%s)", worker.worker_name, temp_worker_id)

    # Исключаем возможные дубликаты id
    final_worker_ids = list(dict.fromkeys(final_worker_ids))

    # Построим итоговую карту заданных сумм по финальным ID
    specified_by_final: dict[int, Decimal] = {}
    for orig_id, amount in specified_by_orig.items():
        final_id = orig_to_new.get(orig_id, orig_id)
        specified_by_final[final_id] = amount

    # Распределим суммы: заданные берем как есть, остаток равномерно по незаданным
    sum_specified = sum(specified_by_final.values(), Decimal("0"))
    if sum_specified > total:
        raise ValueError("Сумма распределений превышает итоговую сумму наряда")
    remainder = total - sum_specified
    unspecified_ids = [wid for wid in final_worker_ids if wid not in specified_by_final]
    allocations: list[tuple[int, float]] = []
    if unspecified_ids:
        per = _round_rub(remainder / Decimal(len(unspecified_ids))) if remainder > 0 else Decimal("0")
        amounts = [per] * len(unspecified_ids)
        diff = _round_rub(remainder - per * Decimal(len(unspecified_ids)))
        if amounts and diff != Decimal("0"):
            amounts[-1] = _round_rub(amounts[-1] + diff)
        for wid, amt in zip(unspecified_ids, amounts):
            allocations.append((wid, float(amt)))
    for wid, amt in specified_by_final.items():
        allocations.append((wid, float(amt)))

    # Сохраняем работников с суммами
    q.set_work_order_workers_with_amounts(conn, work_order_id, allocations)

    logger.info("Создан наряд #%s, сумма: %s", order_no, total)
    return work_order_id


@dataclass
class LoadedWorkOrder:
    id: int
    order_no: int
    date: str
    product_id: int | None
    contract_id: int
    items: list[tuple[int, str, float, float, float]]  # job_type_id, name, qty, unit_price, line_amount
    workers: list[tuple[int, float]]  # (worker_id, amount)
    total_amount: float


def load_work_order(conn: sqlite3.Connection, work_order_id: int) -> LoadedWorkOrder:
    header = q.get_work_order_header(conn, work_order_id)
    if not header:
        raise ValueError("Наряд не найден")
    items_rows = q.get_work_order_items(conn, work_order_id)
    workers_rows = q.get_work_order_workers(conn, work_order_id)
    items = [
        (r["job_type_id"], r["job_name"], float(r["quantity"]), float(r["unit_price"]), float(r["line_amount"]))
        for r in items_rows
    ]
    worker_allocs = [(int(r["worker_id"]), float(r["amount"]) if r["amount"] is not None else 0.0) for r in workers_rows]
    return LoadedWorkOrder(
        id=int(header["id"]),
        order_no=int(header["order_no"]),
        date=str(header["date"]),
        product_id=int(header["product_id"]) if header["product_id"] is not None else None,
        contract_id=int(header["contract_id"]),
        items=items,
        workers=worker_allocs,
        total_amount=float(header["total_amount"]),
    )


def update_work_order(conn: sqlite3.Connection, work_order_id: int, data: WorkOrderInput) -> None:
    validate_date(data.date)
    if not data.items:
        raise ValueError("Наряд должен содержать хотя бы одну строку работ")

    total = Decimal("0")
    line_values: list[tuple[int, float, float, float]] = []

    for item in data.items:
        validate_positive_quantity(item.quantity)
        jt = conn.execute("SELECT id, price FROM job_types WHERE id = ?", (item.job_type_id,)).fetchone()
        if not jt:
            raise ValueError(f"Вид работ id={item.job_type_id} не найден")
        unit_price = Decimal(str(jt["price"]))
        line_amount = _round_rub(unit_price * Decimal(str(item.quantity)))
        total += line_amount
        line_values.append((item.job_type_id, float(item.quantity), float(unit_price), float(line_amount)))

    total = _round_rub(total)

    # Обновим заголовок, учитывая возможную смену номера наряда
    current = q.get_work_order_header(conn, work_order_id)
    cur_no = int(current["order_no"]) if current else None
    new_no = cur_no if getattr(data, "order_no", None) in (None, "") else int(data.order_no)
    if new_no != cur_no:
        if q.order_no_in_use(conn, new_no, exclude_id=work_order_id):
            raise ValueError(f"Номер наряда {new_no} уже используется. Укажите другой номер.")
    q.update_work_order_header(conn, work_order_id, new_no, data.date, data.product_id, data.contract_id, float(total))

    q.delete_work_order_items(conn, work_order_id)
    for (job_type_id, quantity, unit_price, line_amount) in line_values:
        q.insert_work_order_item(conn, work_order_id, job_type_id, quantity, unit_price, line_amount)

    # Обрабатываем работников аналогично create_work_order
    # Разделяем на существующих и ручно добавленных
    existing_workers = [w for w in data.workers if w.worker_id > 0]
    manual_workers = [w for w in data.workers if w.worker_id < 0]

    final_worker_ids: list[int] = []
    final_worker_ids.extend([w.worker_id for w in existing_workers])

    # Для ручно добавленных работников пытаемся найти по ФИО, иначе создаем нового
    orig_to_new: dict[int, int] = {}
    if manual_workers:
        # Привязываем счетчик к work_order_id, чтобы получить уникальные personnel_no
        counter = 1
        for worker in manual_workers:
            found = q.get_worker_by_full_name(conn, worker.worker_name)
            if found:
                wid = int(found["id"])
                orig_to_new[worker.worker_id] = wid
                final_worker_ids.append(wid)
                logger.info("Найден существующий работник по имени '%s': id=%s", worker.worker_name, wid) 
                continue
            personnel_no = f"TEMP_{work_order_id}_{counter}"
            counter += 1
            temp_worker_id = int(q.insert_worker(conn, worker.worker_name, None, None, personnel_no))
            orig_to_new[worker.worker_id] = temp_worker_id
            final_worker_ids.append(temp_worker_id)
            logger.info("Создан временный работник: %s (id=%s)", worker.worker_name, temp_worker_id)

    # Исключаем возможные дубликаты id
    final_worker_ids = list(dict.fromkeys(final_worker_ids))

    # Сопоставим заданные суммы по финальным ID
    specified_by_final: dict[int, Decimal] = {}
    for w in data.workers:
        if w.amount is None:
            continue
        try:
            val = _round_rub(Decimal(str(w.amount)))
        except Exception:
            raise ValueError("Некорректная сумма распределения для работника")
        if val < 0:
            raise ValueError("Сумма для работника не может быть отрицательной")
        final_id = orig_to_new.get(w.worker_id, w.worker_id)
        specified_by_final[final_id] = val

    sum_specified = sum(specified_by_final.values(), Decimal("0"))
    if sum_specified > total:
        raise ValueError("Сумма распределений превышает итоговую сумму наряда")
    remainder = total - sum_specified
    unspecified_ids = [wid for wid in final_worker_ids if wid not in specified_by_final]
    allocations: list[tuple[int, float]] = []
    if unspecified_ids:
        per = _round_rub(remainder / Decimal(len(unspecified_ids))) if remainder > 0 else Decimal("0")
        amounts = [per] * len(unspecified_ids)
        diff = _round_rub(remainder - per * Decimal(len(unspecified_ids)))
        if amounts and diff != Decimal("0"):
            amounts[-1] = _round_rub(amounts[-1] + diff)
        for wid, amt in zip(unspecified_ids, amounts):
            allocations.append((wid, float(amt)))
    for wid, amt in specified_by_final.items():
        allocations.append((wid, float(amt)))

    q.set_work_order_workers_with_amounts(conn, work_order_id, allocations)

    logger.info("Обновлен наряд id=%s, сумма: %s", work_order_id, total)


def delete_work_order(conn: sqlite3.Connection, work_order_id: int) -> None:
    q.delete_work_order(conn, work_order_id)
    logger.info("Удален наряд id=%s", work_order_id)