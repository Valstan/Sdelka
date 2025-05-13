"""
Репозиторий для работы с нарядами
"""

from typing import List, Optional, Tuple, Any, Dict
from datetime import date
from app.core.models.work_card import WorkCard
from app.core.repositories.base_repository import BaseRepository
from app.core.models.work_card_item import WorkCardItem
from app.core.models.worker import Worker
from app.utils.exceptions import DatabaseError
from app.utils.validators.common_validators import common_validators


class WorkCardRepository(BaseRepository[WorkCard]):
    """
    Репозиторий для работы с нарядами в БД
    """

    def __init__(self, connection):
        """
        Инициализация репозитория

        Args:
            connection: Соединение с БД
        """
        super().__init__(WorkCard)
        self.connection = connection

    def create(self, model: WorkCard) -> Tuple[bool, Optional[WorkCard], List[str]]:
        """
        Создает новый наряд в БД

        Args:
            model: Модель наряда

        Returns:
            Tuple[bool, Optional[WorkCard], List[str]]: (успех, созданный наряд, ошибки)
        """
        try:
            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Вставка основной записи
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO work_cards (
                        card_number, card_date, product_id, 
                        contract_id, total_amount
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    model.card_number,
                    model.card_date.isoformat() if model.card_date else None,
                    model.product_id,
                    model.contract_id,
                    model.total_amount
                ))

                # Получаем ID созданного наряда
                model.id = cursor.lastrowid

                # Добавляем элементы наряда
                for item in model.items:
                    cursor.execute("""
                        INSERT INTO work_card_items (
                            work_card_id, work_type_id, quantity, amount
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        model.id,
                        item.work_type_id,
                        item.quantity,
                        item.amount
                    ))

                # Добавляем работников
                for worker_id in model.worker_ids:
                    cursor.execute("""
                        INSERT INTO work_card_workers (
                            work_card_id, worker_id
                        ) VALUES (?, ?)
                    """, (model.id, worker_id))

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка создания наряда: {str(e)}"]

    def update(self, model: WorkCard) -> Tuple[bool, Optional[WorkCard], List[str]]:
        """
        Обновляет существующий наряд в БД

        Args:
            model: Модель наряда

        Returns:
            Tuple[bool, Optional[WorkCard], List[str]]: (успех, обновленный наряд, ошибки)
        """
        try:
            # Проверяем существование наряда
            if not self.exists(model.id):
                return False, None, ["Наряд не найден"]

            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Обновление основной информации
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE work_cards
                    SET card_number = ?, card_date = ?, 
                        product_id = ?, contract_id = ?,
                        total_amount = ?
                    WHERE id = ?
                """, (
                    model.card_number,
                    model.card_date.isoformat() if model.card_date else None,
                    model.product_id,
                    model.contract_id,
                    model.total_amount,
                    model.id
                ))

                # Удаляем старые элементы
                cursor.execute("DELETE FROM work_card_items WHERE work_card_id = ?", (model.id,))

                # Добавляем обновленные элементы
                for item in model.items:
                    cursor.execute("""
                        INSERT INTO work_card_items (
                            work_card_id, work_type_id, quantity, amount
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        model.id,
                        item.work_type_id,
                        item.quantity,
                        item.amount
                    ))

                # Удаляем старых работников
                cursor.execute("DELETE FROM work_card_workers WHERE work_card_id = ?", (model.id,))

                # Добавляем обновленных работников
                for worker_id in model.worker_ids:
                    cursor.execute("""
                        INSERT INTO work_card_workers (
                            work_card_id, worker_id
                        ) VALUES (?, ?)
                    """, (model.id, worker_id))

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка обновления наряда: {str(e)}"]

    def delete(self, model_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет наряд из БД

        Args:
            model_id: ID наряда для удаления

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()

                # Удаляем элементы наряда
                cursor.execute("DELETE FROM work_card_items WHERE work_card_id = ?", (model_id,))

                # Удаляем работников наряда
                cursor.execute("DELETE FROM work_card_workers WHERE work_card_id = ?", (model_id,))

                # Удаляем сам наряд
                cursor.execute("DELETE FROM work_cards WHERE id = ?", (model_id,))

                return True, []

        except Exception as e:
            return False, [f"Ошибка удаления наряда: {str(e)}"]

    def get_by_id(self, model_id: int) -> Optional[WorkCard]:
        """
        Получает наряд по ID

        Args:
            model_id: ID наряда

        Returns:
            Optional[WorkCard]: Найденный наряд или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM work_cards WHERE id = ?
            """, (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Создаем модель наряда
            work_card = WorkCard(**dict(row))

            # Получаем элементы наряда
            cursor.execute("""
                SELECT * FROM work_card_items WHERE work_card_id = ?
            """, (model_id,))
            items = [WorkCardItem(**dict(item_row)) for item_row in cursor.fetchall()]
            work_card.items = items

            # Получаем ID работников
            cursor.execute("""
                SELECT worker_id FROM work_card_workers WHERE work_card_id = ?
            """, (model_id,))
            worker_ids = [worker_row["worker_id"] for worker_row in cursor.fetchall()]
            work_card.worker_ids = worker_ids

            return work_card

        except Exception as e:
            return None

    def get_all(self) -> List[WorkCard]:
        """
        Получает все наряды из БД

        Returns:
            List[WorkCard]: Список нарядов
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM work_cards")
            rows = cursor.fetchall()

            work_cards = []
            for row in rows:
                work_card = WorkCard(**dict(row))

                # Получаем элементы наряда
                cursor.execute("""
                    SELECT * FROM work_card_items WHERE work_card_id = ?
                """, (work_card.id,))
                items = [WorkCardItem(**dict(item_row)) for item_row in cursor.fetchall()]
                work_card.items = items

                # Получаем ID работников
                cursor.execute("""
                    SELECT worker_id FROM work_card_workers WHERE work_card_id = ?
                """, (work_card.id,))
                worker_ids = [worker_row["worker_id"] for worker_row in cursor.fetchall()]
                work_card.worker_ids = worker_ids

                work_cards.append(work_card)

            return work_cards

        except Exception as e:
            return []

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование наряда по ID

        Args:
            model_id: ID наряда

        Returns:
            bool: True, если наряд существует
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM work_cards WHERE id = ?", (model_id,))
            return cursor.fetchone() is not None
        except:
            return False

    def add_item(self, item_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Добавляет элемент в наряд

        Args:
            item_data: Данные элемента наряда

        Returns:
            Tuple[bool, Optional[Dict[str, Any]], List[str]]: (успех, добавленный элемент, ошибки)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO work_card_items (
                    work_card_id, work_type_id, quantity, amount
                ) VALUES (?, ?, ?, ?)
            """, (
                item_data["work_card_id"],
                item_data["work_type_id"],
                item_data["quantity"],
                item_data["amount"]
            ))

            # Получаем вставленную запись
            item_id = cursor.lastrowid
            cursor.execute("SELECT * FROM work_card_items WHERE id = ?", (item_id,))
            result = cursor.fetchone()

            return True, dict(result) if result else None, []

        except Exception as e:
            return False, None, [f"Ошибка добавления элемента: {str(e)}"]

    def remove_item(self, item_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет элемент из наряда

        Args:
            item_id: ID элемента наряда

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM work_card_items WHERE id = ?", (item_id,))
            return True, []

        except Exception as e:
            return False, [f"Ошибка удаления элемента: {str(e)}"]

    def get_items(self, work_card_id: int) -> List[WorkCardItem]:
        """
        Получает элементы наряда по ID наряда

        Args:
            work_card_id: ID наряда

        Returns:
            List[WorkCardItem]: Список элементов наряда
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM work_card_items WHERE work_card_id = ?", (work_card_id,))
            return [WorkCardItem(**dict(row)) for row in cursor.fetchall()]

        except Exception as e:
            return []

    def get_workers(self, work_card_id: int) -> List[Worker]:
        """
        Получает работников наряда по ID наряда

        Args:
            work_card_id: ID наряда

        Returns:
            List[Worker]: Список работников наряда
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT w.* FROM workers w
                JOIN work_card_workers wcw ON w.id = wcw.worker_id
                WHERE wcw.work_card_id = ?
            """, (work_card_id,))

            return [Worker(**dict(row)) for row in cursor.fetchall()]

        except Exception as e:
            return []

    def add_worker(self, work_card_id: int, worker_id: int) -> Tuple[bool, List[str]]:
        """
        Добавляет работника в наряд

        Args:
            work_card_id: ID наряда
            worker_id: ID работника

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO work_card_workers (
                    work_card_id, worker_id
                ) VALUES (?, ?)
            """, (work_card_id, worker_id))

            return True, []

        except Exception as e:
            return False, [f"Ошибка добавления работника: {str(e)}"]

    def remove_worker(self, work_card_id: int, worker_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет работника из наряда

        Args:
            work_card_id: ID наряда
            worker_id: ID работника

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM work_card_workers 
                WHERE work_card_id = ? AND worker_id = ?
            """, (work_card_id, worker_id))

            return True, []

        except Exception as e:
            return False, [f"Ошибка удаления работника: {str(e)}"]

    def is_worker_in_card(self, work_card_id: int, worker_id: int) -> bool:
        """
        Проверяет, есть ли работник в наряде

        Args:
            work_card_id: ID наряда
            worker_id: ID работника

        Returns:
            bool: True, если работник в наряде
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM work_card_workers 
                WHERE work_card_id = ? AND worker_id = ?
            """, (work_card_id, worker_id))

            return cursor.fetchone() is not None

        except Exception as e:
            return False

    def search(self, **kwargs) -> List[WorkCard]:
        """
        Выполняет поиск нарядов по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            List[WorkCard]: Список найденных нарядов
        """
        try:
            query = "SELECT * FROM work_cards WHERE 1=1"
            params = []

            # Фильтрация по дате
            if "start_date" in kwargs and "end_date" in kwargs:
                query += " AND card_date BETWEEN ? AND ?"
                params.extend([kwargs["start_date"], kwargs["end_date"]])

            # Фильтрация по изделию
            if "product_id" in kwargs:
                query += " AND product_id = ?"
                params.append(kwargs["product_id"])

            # Фильтрация по контракту
            if "contract_id" in kwargs:
                query += " AND contract_id = ?"
                params.append(kwargs["contract_id"])

            # Фильтрация по периоду
            if "period" in kwargs:
                period = kwargs["period"]
                if period == "today":
                    query += " AND card_date = DATE('now')"
                elif period == "week":
                    query += " AND card_date >= DATE('now', '-7 days')"
                elif period == "month":
                    query += " AND card_date >= DATE('now', '-1 month')"

            cursor = self.connection.cursor()
            cursor.execute(query, params)

            # Получаем результаты
            rows = cursor.fetchall()
            if not rows:
                return []

            work_cards = []
            for row in rows:
                work_card = WorkCard(**dict(row))

                # Получаем элементы наряда
                cursor.execute("""
                    SELECT * FROM work_card_items WHERE work_card_id = ?
                """, (work_card.id,))
                items = [WorkCardItem(**dict(item_row)) for item_row in cursor.fetchall()]
                work_card.items = items

                # Получаем ID работников
                cursor.execute("""
                    SELECT worker_id FROM work_card_workers WHERE work_card_id = ?
                """, (work_card.id,))
                worker_ids = [worker_row["worker_id"] for worker_row in cursor.fetchall()]
                work_card.worker_ids = worker_ids

                work_cards.append(work_card)

            return work_cards

        except Exception as e:
            return []