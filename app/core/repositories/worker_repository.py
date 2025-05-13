"""
Репозиторий для работы с работниками
"""

from typing import List, Optional, Tuple, Any, Dict
from datetime import date
from app.core.models.worker import Worker
from app.core.repositories.base_repository import BaseRepository
from app.core.models.base import BaseModel
from app.utils.exceptions import DatabaseError
from app.utils.validators.common_validators import common_validators


class WorkerRepository(BaseRepository[Worker]):
    """
    Репозиторий для работы с работниками в БД
    """

    def __init__(self, connection):
        """
        Инициализация репозитория

        Args:
            connection: Соединение с БД
        """
        super().__init__(Worker)
        self.connection = connection

    def create(self, model: Worker) -> Tuple[bool, Optional[Worker], List[str]]:
        """
        Создает нового работника в БД

        Args:
            model: Модель работника

        Returns:
            Tuple[bool, Optional[Worker], List[str]]: (успех, созданный работник, ошибки)
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
                    INSERT INTO workers (
                        last_name, first_name, middle_name, 
                        employee_id, workshop_number
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    model.last_name,
                    model.first_name,
                    model.middle_name,
                    model.employee_id,
                    model.workshop_number
                ))

                # Получаем ID созданного работника
                model.id = cursor.lastrowid

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка создания работника: {str(e)}"]

    def update(self, model: Worker) -> Tuple[bool, Optional[Worker], List[str]]:
        """
        Обновляет существующего работника в БД

        Args:
            model: Модель работника

        Returns:
            Tuple[bool, Optional[Worker], List[str]]: (успех, обновленный работник, ошибки)
        """
        try:
            # Проверяем существование работника
            if not self.exists(model.id):
                return False, None, ["Работник не найден"]

            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Обновление записи
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE workers
                    SET last_name = ?, first_name = ?, 
                        middle_name = ?, employee_id = ?, 
                        workshop_number = ?
                    WHERE id = ?
                """, (
                    model.last_name,
                    model.first_name,
                    model.middle_name,
                    model.employee_id,
                    model.workshop_number,
                    model.id
                ))

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка обновления работника: {str(e)}"]

    def delete(self, model_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет работника из БД

        Args:
            model_id: ID работника

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM workers WHERE id = ?", (model_id,))

                return True, []

        except Exception as e:
            return False, [f"Ошибка удаления работника: {str(e)}"]

    def get_by_id(self, model_id: int) -> Optional[Worker]:
        """
        Получает работника по ID

        Args:
            model_id: ID работника

        Returns:
            Optional[Worker]: Найденный работник или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM workers WHERE id = ?", (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Создаем модель работника
            return Worker(**dict(row))

        except Exception as e:
            return None

    def get_all(self) -> List[Worker]:
        """
        Получает всех работников из БД

        Returns:
            List[Worker]: Список работников
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM workers")
            rows = cursor.fetchall()

            return [Worker(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование работника по ID

        Args:
            model_id: ID работника

        Returns:
            bool: True, если работник существует
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM workers WHERE id = ?", (model_id,))
            return cursor.fetchone() is not None
        except:
            return False

    def search(self, **kwargs) -> List[Worker]:
        """
        Выполняет поиск работников по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            List[Worker]: Список найденных работников
        """
        try:
            query = "SELECT * FROM workers WHERE 1=1"
            params = []

            # Поиск по ФИО
            if "full_name" in kwargs:
                full_name = kwargs["full_name"].strip().split()
                if len(full_name) >= 2:
                    query += " AND last_name = ? AND first_name = ?"
                    params.extend([full_name[0], full_name[1]])
                    if len(full_name) > 2:
                        query += " AND middle_name = ?"
                        params.append(full_name[2])

            # Поиск по фамилии
            if "last_name" in kwargs:
                query += " AND last_name LIKE ?"
                params.append(f"%{kwargs['last_name']}%")

            # Поиск по имени
            if "first_name" in kwargs:
                query += " AND first_name LIKE ?"
                params.append(f"%{kwargs['first_name']}%")

            # Поиск по отчеству
            if "middle_name" in kwargs:
                query += " AND middle_name LIKE ?"
                params.append(f"%{kwargs['middle_name']}%")

            # Поиск по табельному номеру
            if "employee_id" in kwargs:
                query += " AND employee_id = ?"
                params.append(kwargs["employee_id"])

            # Поиск по номеру цеха
            if "workshop_number" in kwargs:
                query += " AND workshop_number = ?"
                params.append(kwargs["workshop_number"])

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Worker(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_by_employee_id(self, employee_id: int) -> Optional[Worker]:
        """
        Получает работника по табельному номеру

        Args:
            employee_id: Табельный номер работника

        Returns:
            Optional[Worker]: Найденный работник или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM workers WHERE employee_id = ?", (employee_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return Worker(**dict(row))

        except Exception as e:
            return None

    def get_by_workshop(self, workshop_number: int) -> List[Worker]:
        """
        Получает работников по номеру цеха

        Args:
            workshop_number: Номер цеха

        Returns:
            List[Worker]: Список работников цеха
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM workers WHERE workshop_number = ?", (workshop_number,))
            rows = cursor.fetchall()

            return [Worker(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_workers_for_combobox(self) -> List[Dict[str, Any]]:
        """
        Получает список работников для выпадающего списка

        Returns:
            List[Dict[str, Any]]: Список работников с полями id и full_name
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, last_name, first_name, middle_name FROM workers")
            rows = cursor.fetchall()

            workers = []
            for row in rows:
                workers.append({
                    "id": row["id"],
                    "full_name": f"{row['last_name']} {row['first_name']} {row['middle_name']}".strip()
                })

            return workers

        except Exception as e:
            return []