# app/utils/exceptions.py
from typing import Any, Optional

class ValidationError(Exception):
    """Исключение, возникающее при ошибке валидации данных."""
    pass

class DatabaseError(Exception):
    """Исключение, возникающее при ошибках работы с БД."""
    pass

class NotFoundError(Exception):
    """Исключение, возникающее при отсутствии запрашиваемой сущности."""
    pass

class DuplicateError(Exception):
    """Исключение, возникающее при попытке добавить дублирующуюся сущность."""
    pass

class ReportGenerationError(Exception):
    """Исключение, возникающее при генерации отчета."""
    pass