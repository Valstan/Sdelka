"""
Репозиторий для работы с контрактами
"""

from typing import List, Optional, Tuple, Any, Dict
from datetime import date
from app.core.models.contract import Contract
from app.core.repositories.base_repository import BaseRepository
from app.utils.exceptions import DatabaseError
from app.utils.validators.common_validators import common_validators


class ContractRepository(BaseRepository[Contract]):
    """
    Репозиторий для работы с контрактами в БД
    """

    def __init__(self, connection):
        """
        Инициализация репозитория

        Args:
            connection: Соединение с БД
        """
        super().__init__(Contract)
        self.connection = connection

    def create(self, model: Contract) -> Tuple[bool, Optional[Contract], List[str]]:
        """
        Создает новый контракт в БД

        Args:
            model: Модель контракта

        Returns:
            Tuple[bool, Optional[Contract], List[str]]: (успех, созданный контракт, ошибки)
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
                    INSERT INTO contracts (
                        contract_number, start_date, end_date, description
                    ) VALUES (?, ?, ?, ?)
                """, (
                    model.contract_number,
                    model.start_date.isoformat() if model.start_date else None,
                    model.end_date.isoformat() if model.end_date else None,
                    model.description
                ))

                # Получаем ID созданного контракта
                model.id = cursor.lastrowid

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка создания контракта: {str(e)}"]

    def update(self, model: Contract) -> Tuple[bool, Optional[Contract], List[str]]:
        """
        Обновляет существующий контракт в БД

        Args:
            model: Модель контракта

        Returns:
            Tuple[bool, Optional[Contract], List[str]]: (успех, обновленный контракт, ошибки)
        """
        try:
            # Проверяем существование контракта
            if not self.exists(model.id):
                return False, None, ["Контракт не найден"]

            # Валидация модели
            is_valid, errors = model.validate()
            if not is_valid:
                return False, None, errors

            # Обновление записи
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE contracts
                    SET contract_number = ?, start_date = ?, 
                        end_date = ?, description = ?
                    WHERE id = ?
                """, (
                    model.contract_number,
                    model.start_date.isoformat() if model.start_date else None,
                    model.end_date.isoformat() if model.end_date else None,
                    model.description,
                    model.id
                ))

                return True, model, []

        except Exception as e:
            return False, None, [f"Ошибка обновления контракта: {str(e)}"]

    def delete(self, model_id: int) -> Tuple[bool, List[str]]:
        """
        Удаляет контракт из БД

        Args:
            model_id: ID контракта

        Returns:
            Tuple[bool, List[str]]: (успех, ошибки)
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM contracts WHERE id = ?", (model_id,))

                return True, []

        except Exception as e:
            return False, [f"Ошибка удаления контракта: {str(e)}"]

    def get_by_id(self, model_id: int) -> Optional[Contract]:
        """
        Получает контракт по ID

        Args:
            model_id: ID контракта

        Returns:
            Optional[Contract]: Найденный контракт или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = ?", (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Создаем модель контракта
            return Contract(**dict(row))

        except Exception as e:
            return None

    def get_all(self) -> List[Contract]:
        """
        Получает все контракты из БД

        Returns:
            List[Contract]: Список контрактов
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM contracts")
            rows = cursor.fetchall()

            return [Contract(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование контракта по ID

        Args:
            model_id: ID контракта

        Returns:
            bool: True, если контракт существует
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM contracts WHERE id = ?", (model_id,))
            return cursor.fetchone() is not None
        except:
            return False

    def search(self, **kwargs) -> List[Contract]:
        """
        Выполняет поиск контрактов по заданным критериям

        Args:
            **kwargs: Параметры поиска

        Returns:
            List[Contract]: Список найденных контрактов
        """
        try:
            query = "SELECT * FROM contracts WHERE 1=1"
            params = []

            # Поиск по шифру контракта
            if "contract_number" in kwargs:
                query += " AND contract_number LIKE ?"
                params.append(f"%{kwargs['contract_number']}%")

            # Поиск по периоду действия
            if "start_date" in kwargs and "end_date" in kwargs:
                start_date = kwargs["start_date"]
                end_date = kwargs["end_date"]
                query += " AND start_date <= ? AND end_date >= ?"
                params.extend([end_date.isoformat(), start_date.isoformat()])

            # Поиск по дате начала
            if "start_date" in kwargs and "end_date" not in kwargs:
                query += " AND start_date >= ?"
                params.append(kwargs["start_date"].isoformat())

            # Поиск по дате окончания
            if "end_date" in kwargs and "start_date" not in kwargs:
                query += " AND end_date <= ?"
                params.append(kwargs["end_date"].isoformat())

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Contract(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        """
        Получает контракт по шифру

        Args:
            contract_number: Шифр контракта

        Returns:
            Optional[Contract]: Найденный контракт или None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM contracts WHERE contract_number = ?", (contract_number,))

            row = cursor.fetchone()
            if not row:
                return None

            return Contract(**dict(row))

        except Exception as e:
            return None

    def get_active_contracts(self) -> List[Contract]:
        """
        Получает активные контракты

        Returns:
            List[Contract]: Список активных контрактов
        """
        try:
            today = date.today().isoformat()
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM contracts 
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY contract_number
            """, (today, today))

            rows = cursor.fetchall()
            return [Contract(**dict(row)) for row in rows]

        except Exception as e:
            return []

    def get_contracts_for_combobox(self) -> List[Dict[str, Any]]:
        """
        Получает список контрактов для выпадающего списка

        Returns:
            List[Dict[str, Any]]: Список контрактов с полями id и display_name
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, contract_number, start_date, end_date FROM contracts")
            rows = cursor.fetchall()

            contracts = []
            for row in rows:
                start_year = row["start_date"].split("-")[0] if row["start_date"] else ""
                end_year = row["end_date"].split("-")[0] if row["end_date"] else ""

                contracts.append({
                    "id": row["id"],
                    "display_name": f"{row['contract_number']} ({start_year}-{end_year})",
                    "contract_number": row["contract_number"],
                    "start_year": start_year,
                    "end_year": end_year
                })

            return contracts

        except Exception as e:
            return []