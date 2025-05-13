# app/core/services/base_service.py
import logging
from abc import ABC
from typing import Any, Dict, List, Optional, Type, TypeVar

from app.core.models.base import BaseModel
from app.core.repositories.base_repository import BaseRepository
from app.core.database.database_manager import DatabaseManager
from app.utils.exceptions import (
    ValidationError,
    DatabaseError,
    NotFoundError
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=BaseRepository)

class BaseService(ABC):
    """
    Базовый класс сервиса для работы с сущностями.
    
    Attributes:
        db_manager: Менеджер базы данных
        repository: Репозиторий для работы с сущностью
    """
    
    def __init__(self, db_manager: DatabaseManager, repository: R):
        """
        Инициализирует сервис.
        
        Args:
            db_manager: Менеджер базы данных
            repository: Репозиторий для работы с сущностью
        """
        self.db_manager = db_manager
        self.repository = repository
        
    def create(self, model: T) -> T:
        """
        Создает новую сущность.
        
        Args:
            model: Модель данных
            
        Returns:
            T: Созданная сущность
        """
        try:
            # Валидация данных
            is_valid, errors = model.validate()
            if not is_valid:
                raise ValidationError(f"Ошибка валидации при создании {model.__class__.__name__}: {errors}")
            
            # Создание в БД
            success, model_id = self.repository.create(model)
            if not success or model_id is None:
                raise DatabaseError(f"Ошибка создания {model.__class__.__name__} в БД")
                
            # Получаем созданную сущность
            created_model = self.repository.get_by_id(model_id)
            if not created_model:
                raise DatabaseError(f"Не удалось получить созданную сущность {model.__class__.__name__}")
                
            return created_model
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка создания {model.__class__.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка создания {model.__class__.__name__}") from e
    
    def get_by_id(self, model_id: int) -> Optional[T]:
        """
        Получает сущность по ID.
        
        Args:
            model_id: ID сущности
            
        Returns:
            Optional[T]: Сущность или None
        """
        try:
            return self.repository.get_by_id(model_id)
        except Exception as e:
            logger.error(f"Ошибка получения {self.model_class.__name__} по ID: {e}", exc_info=True)
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Получает все сущности.
        
        Args:
            limit: Количество записей для получения
            offset: Смещение
            
        Returns:
            List[T]: Список сущностей
        """
        try:
            return self.repository.get_all(limit, offset)
        except Exception as e:
            logger.error(f"Ошибка получения всех {self.model_class.__name__}: {e}", exc_info=True)
            return []
    
    def update(self, model: T) -> T:
        """
        Обновляет сущность.
        
        Args:
            model: Модель данных
            
        Returns:
            T: Обновленная сущность
        """
        try:
            # Проверка наличия ID
            if model.id is None:
                raise ValidationError(f"Невозможно обновить {model.__class__.__name__} без ID")
            
            # Валидация данных
            is_valid, errors = model.validate()
            if not is_valid:
                raise ValidationError(f"Ошибка валидации при обновлении {model.__class__.__name__}: {errors}")
            
            # Проверка существования
            if not self.repository.exists(model.id):
                raise NotFoundError(f"{model.__class__.__name__} с ID {model.id} не найден")
                
            # Обновление в БД
            success, error = self.repository.update(model)
            if not success:
                raise DatabaseError(f"Ошибка обновления {model.__class__.__name__}: {error}")
                
            # Получаем обновленную сущность
            updated_model = self.repository.get_by_id(model.id)
            if not updated_model:
                raise DatabaseError(f"Не удалось получить обновленную сущность {model.__class__.__name__}")
                
            return updated_model
            
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления {model.__class__.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка обновления {model.__class__.__name__}") from e
    
    def delete(self, model_id: int) -> None:
        """
        Удаляет сущность.
        
        Args:
            model_id: ID сущности
        """
        try:
            # Проверка существования
            if not self.repository.exists(model_id):
                raise NotFoundError(f"{self.model_class.__name__} с ID {model_id} не найден")
                
            # Удаление из БД
            success, error = self.repository.delete(model_id)
            if not success:
                raise DatabaseError(f"Ошибка удаления {self.model_class.__name__}: {error}")
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка удаления {self.model_class.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка удаления {self.model_class.__name__}") from e
    
    def search(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Выполняет поиск сущностей по критериям.
        
        Args:
            criteria: Словарь с условиями поиска
            
        Returns:
            List[T]: Список подходящих сущностей
        """
        try:
            return self.repository.search(criteria)
        except Exception as e:
            logger.error(f"Ошибка поиска {self.model_class.__name__}: {e}", exc_info=True)
            return []
    
    def exists(self, model_id: int) -> bool:
        """
        Проверяет существование сущности.
        
        Args:
            model_id: ID сущности
            
        Returns:
            bool: True, если сущность существует
        """
        try:
            return self.repository.exists(model_id)
        except Exception as e:
            logger.error(f"Ошибка проверки существования {self.model_class.__name__}: {e}", exc_info=True)
            return False
    
    def count(self) -> int:
        """
        Возвращает количество сущностей.
        
        Returns:
            int: Количество сущностей
        """
        try:
            return self.repository.count()
        except Exception as e:
            logger.error(f"Ошибка получения количества {self.model_class.__name__}: {e}", exc_info=True)
            return 0
    
    def bulk_create(self, models: List[T]) -> List[T]:
        """
        Создает несколько сущностей.
        
        Args:
            models: Список моделей
            
        Returns:
            List[T]: Созданные сущности
        """
        try:
            # Валидация данных
            for model in models:
                is_valid, errors = model.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации при массовом создании {model.__class__.__name__}: {errors}")
            
            # Массовое создание в БД
            success, error = self.repository.bulk_create(models)
            if not success:
                raise DatabaseError(f"Ошибка массового создания {models[0].__class__.__name__}: {error}")
                
            # Получаем созданные сущности
            created_ids = [model.id for model in models if model.id]
            if not created_ids:
                return []
                
            return [model for model in self.repository.get_all() if model.id in created_ids]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка массового создания {models[0].__class__.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка массового создания {models[0].__class__.__name__}") from e
    
    def bulk_update(self, models: List[T]) -> List[T]:
        """
        Обновляет несколько сущностей.
        
        Args:
            models: Список моделей
            
        Returns:
            List[T]: Обновленные сущности
        """
        try:
            # Проверка наличия ID
            for model in models:
                if model.id is None:
                    raise ValidationError(f"Невозможно обновить {model.__class__.__name__} без ID")
            
            # Валидация данных
            for model in models:
                is_valid, errors = model.validate()
                if not is_valid:
                    raise ValidationError(f"Ошибка валидации при массовом обновлении {model.__class__.__name__}: {errors}")
            
            # Проверка существования
            for model in models:
                if not self.repository.exists(model.id):
                    raise NotFoundError(f"{model.__class__.__name__} с ID {model.id} не найден")
                    
            # Массовое обновление в БД
            success, error = self.repository.bulk_update(models)
            if not success:
                raise DatabaseError(f"Ошибка массового обновления {models[0].__class__.__name__}: {error}")
                
            # Получаем обновленные сущности
            updated_ids = [model.id for model in models if model.id]
            if not updated_ids:
                return []
                
            return [model for model in self.repository.get_all() if model.id in updated_ids]
            
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка массового обновления {models[0].__class__.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка массового обновления {models[0].__class__.__name__}") from e
    
    @property
    def model_class(self) -> Type[T]:
        """
        Возвращает класс модели.
        
        Returns:
            Type[T]: Класс модели
        """
        return self.repository.model_class