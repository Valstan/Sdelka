"""
Репозиторий для работы с видами работ
"""

from typing import List, Optional, Tuple, Any, Dict
from datetime import date
from app.core.models.work_type import WorkType
from app.core.repositories.base_repository import BaseRepository
from app.utils.exceptions import DatabaseError
from app.utils.validators.common_validators import common_validators


class WorkTypeRepository(BaseRepository[WorkType]):
    """
    Репозиторий для работы с видами работ в БД
    """

    def __init__(self, connection):
        """
        Инициализация репозитория

        Args:
            connection: Соединение с БД
        """
        super().__init__(WorkType)
        self.connection = connection

    def create(self, model: WorkType) -> Tuple[bool, Optional[WorkType], List[str]]:
        """
        Создает новый вид работы в БД

        Args:
            model: Модель вида работы

        Returns:
            Tuple[bool, Optional[WorkType], List[str]]: (успех, созданный вид работы, ошибки)
        """
        try:
            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Вставка записи
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO work_types (
                        name, unit, price, valid_from
                    ) VALUES (?, ?, ?, ?)
                """, (
                    model.name,
                    model.unit,
                    model.price,
                    model.valid_from.isoformat() if model.valid_from else None
                ))

                # Получаем ID созданного вида работы
                model.id = cursor.lastrowid

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка создания вида работы: {str(e)}"]

    def update(self, model: WorkType) -> Tuple[bool, Optional[WorkType], List[str]]:
        """
        Обновляет существующий вид работы в БД

        Args:
            model: Модель вида работы

        Returns:
            Tuple[bool, Optional[WorkType], List[str]]: (успех, обновленный вид работы, ошибки)
        """
        try:
            # Проверяем существование вида работы
            if not self.exists(model.id):
                return False, None, ["Вид работы не найден"]

            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Обновление записи
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE work_types
                    SET name = ?, unit = ?, price = ?, valid_from = ?
                    WHERE id = ?
                """, (
                    model.name,
                    model.unit,
                    model.price,
                    model.valid_from.isoformat() if model.valid_from else None,
                    model.id
                ))

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка обновления вида работы: {str(e)}"]

    def delete(self, model_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет вид работы из БД

        Args:
            model_id: ID вида работы

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM work_types WHERE id = ?", (model_id,))

                return True, []

        except Exception as e:
            return False, [f"Ошибка удаления вида работы: {str(e)}"]

    def get_by_id(self, model_id: int) -> Optional[WorkType]:
        """
        Получает вид работы по ID

        Args:
            model_id: ID вида работы

        Returns:
            Optional[WorkType]: Найденный вид работы или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM work_types WHERE id = ?", (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Создаем модель вида работы
            return WorkType(**dict(row))

        except Exception as e:
            return None

    def get_all(self) -> List[WorkType]:
        """
        Получает все виды работ из БД

        Returns:
            List[WorkType]: Список видов работ
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM work_types")
            rows = cursor.fetchall()

            return [WorkType(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование вида работы по ID

        Args:
            model_id: ID вида работы

        Returns:
            bool: True, если вид работы существует
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM work_types WHERE id = ?", (model_id,))
            return cursor.fetchone() is not None
        except:
            return False

    def search(self, **kwargs) -> List[WorkType]:
        """
        Выполняет поиск видов работ по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            List[WorkType]: Список найденных видов работ
        """
        try:
            query = "SELECT * FROM work_types WHERE 1=1"
            params = []

            # Поиск по названию
            if "name" in kwargs:
                query += " AND name LIKE ?"
                params.append(f"%{kwargs['name']}%")

            # Поиск по единице измерения
            if "unit" in kwargs:
                query += " AND unit = ?"
                params.append(kwargs["unit"])

            # Поиск по цене
            if "price" in kwargs:
                query += " AND price = ?"
                params.append(kwargs["price"])

            # Поиск по дате действия
            if "valid_from" in kwargs and isinstance(kwargs["valid_from"], date):
                query += " AND valid_from <= ?"
                params.append(kwargs["valid_from"].isoformat())

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [WorkType(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_by_name(self, name: str) -> Optional[WorkType]:
        """
        Получает вид работы по названию

        Args:
            name: Название вида работы

        Returns:
            Optional[WorkType]: Найденный вид работы или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM work_types WHERE name = ?", (name,))

            row = cursor.fetchone()
            if not row:
                return None

            return WorkType(**dict(row))

        except Exception as e:
            return None

    def get_active_work_types(self) -> List[WorkType]:
        """
        Получает активные виды работ (не истекшие)

        Returns:
            List[WorkType]: Список активных видов работ
        """
        try:
            today = date.today().isoformat()
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM work_types 
                WHERE valid_from <= ? OR valid_from IS NULL
                ORDER BY name
            """, (today,))

            rows = cursor.fetchall()
            return [WorkType(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_work_types_for_combobox(self) -> List[Dict[str, Any]]:
        """
        Получает список видов работ для выпадающего списка

        Returns:
            List[Dict[str, Any]]: Список видов работ с полями id и display_name
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, name, unit, price FROM work_types")
            rows = cursor.fetchall()

            work_types = []
            for row in rows:
                work_types.append({
                    "id": row["id"],
                    "display_name": f"{row['name']} ({row['unit']}, {row['price']:.2f} руб.)",
                    "name": row["name"],
                    "unit": row["unit"],
                    "price": row["price"]
                })

            return work_types

        except Exception as e:
            return []