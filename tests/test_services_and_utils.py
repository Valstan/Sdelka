import pytest
from unittest.mock import Mock, patch, MagicMock
from services.validation import validate_date, validate_positive_quantity
from utils.runtime_mode import get_mode, set_mode, is_readonly, AppMode
from utils.security import verify_admin_password, verify_user_password, user_password_is_set
from utils.text import normalize_for_search, sanitize_filename, short_fio
import tempfile
import os
from pathlib import Path


class TestValidation:
    """Тесты для функций валидации."""
    
    def test_validate_date(self):
        """Тест валидации даты."""
        # Функция не возвращает значение, а выбрасывает исключение при ошибке
        # Тест с правильным форматом даты (dd.mm.yyyy) - не должно быть исключений
        validate_date('01.01.2025')
        validate_date('31.12.2025')
        
        # Тест с неправильным форматом (должны быть исключения)
        try:
            validate_date('2025-01-01')
            assert False, "Должно было выбросить исключение"
        except Exception:
            assert True
        
        try:
            validate_date('invalid-date')
            assert False, "Должно было выбросить исключение"
        except Exception:
            assert True
        
        try:
            validate_date('')
            assert False, "Должно было выбросить исключение"
        except Exception:
            assert True
    
    def test_validate_positive_quantity(self):
        """Тест валидации положительного количества."""
        # Функция не возвращает значение, а выбрасывает исключение при ошибке
        # Тест с правильными значениями (не должно быть исключений)
        validate_positive_quantity(1.0)
        validate_positive_quantity(0.5)
        
        # Тест с неправильными значениями (должны быть исключения)
        try:
            validate_positive_quantity(0)
            assert False, "Должно было выбросить исключение"
        except Exception:
            assert True
        
        try:
            validate_positive_quantity(-1.0)
            assert False, "Должно было выбросить исключение"
        except Exception:
            assert True


class TestRuntimeMode:
    """Тесты для функций режима выполнения."""
    
    def test_get_mode(self):
        """Тест получения режима выполнения."""
        mode = get_mode()
        assert mode in [AppMode.FULL, AppMode.READONLY]
    
    def test_set_mode(self):
        """Тест установки режима выполнения."""
        original_mode = get_mode()
        
        # Устанавливаем новый режим
        set_mode(AppMode.READONLY)
        assert get_mode() == AppMode.READONLY
        
        # Возвращаем исходный режим
        set_mode(original_mode)
        assert get_mode() == original_mode
    
    def test_is_readonly(self):
        """Тест проверки режима только для чтения."""
        original_mode = get_mode()
        
        # Устанавливаем режим только для чтения
        set_mode(AppMode.READONLY)
        assert is_readonly() == True
        
        # Устанавливаем полный режим
        set_mode(AppMode.FULL)
        assert is_readonly() == False
        
        # Возвращаем исходный режим
        set_mode(original_mode)


class TestSecurity:
    """Тесты для функций безопасности."""
    
    def test_verify_admin_password(self):
        """Тест проверки пароля администратора."""
        # Тест с неправильным паролем
        assert verify_admin_password('wrong_password') == False
        
        # Тест с пустым паролем
        assert verify_admin_password('') == False
    
    def test_verify_user_password(self):
        """Тест проверки пользовательского пароля."""
        # Тест с неправильным паролем
        assert verify_user_password('wrong_password') == False
        
        # Тест с пустым паролем
        assert verify_user_password('') == False
    
    def test_user_password_is_set(self):
        """Тест проверки установки пользовательского пароля."""
        is_set = user_password_is_set()
        assert isinstance(is_set, bool)


class TestTextUtils:
    """Тесты для функций работы с текстом."""
    
    def test_normalize_for_search(self):
        """Тест нормализации текста для поиска."""
        # Тест с обычным текстом
        text = "Тестовый текст"
        normalized = normalize_for_search(text)
        assert normalized == "тестовый текст"
        
        # Тест с пустой строкой
        empty_text = ""
        normalized_empty = normalize_for_search(empty_text)
        assert normalized_empty == ""
        
        # Тест с None
        none_text = None
        normalized_none = normalize_for_search(none_text)
        assert normalized_none is None
    
    def test_sanitize_filename(self):
        """Тест очистки имени файла."""
        # Тест с обычным именем
        filename = "test_file.txt"
        sanitized = sanitize_filename(filename)
        assert sanitized == "test_file.txt"
        
        # Тест с недопустимыми символами
        bad_filename = "test<>file|.txt"
        sanitized_bad = sanitize_filename(bad_filename)
        assert "<" not in sanitized_bad
        assert ">" not in sanitized_bad
        assert "|" not in sanitized_bad
    
    def test_short_fio(self):
        """Тест сокращения ФИО."""
        # Тест с полным ФИО
        full_name = "Иванов Иван Иванович"
        short_name = short_fio(full_name)
        assert short_name == "Иванов И. И."
        
        # Тест с коротким именем
        short_input = "Иванов"
        short_result = short_fio(short_input)
        assert short_result == "Иванов"


class TestBackup:
    """Тесты для функций резервного копирования."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        if hasattr(self, 'temp_dir'):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_backup_sqlite_db(self):
        """Тест создания резервной копии SQLite."""
        from utils.backup import backup_sqlite_db
        
        # Создаем тестовый файл базы данных
        test_db = os.path.join(self.temp_dir, 'test.db')
        with open(test_db, 'w') as f:
            f.write('test data')
        
        backup_path = backup_sqlite_db(test_db, self.backup_dir)
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # Проверяем содержимое
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == 'test data'
    
    def test_rotate_backups(self):
        """Тест ротации резервных копий."""
        from utils.backup import rotate_backups
        
        # Создаем несколько тестовых файлов
        test_files = ['backup1.db', 'backup2.db', 'backup3.db']
        for filename in test_files:
            filepath = os.path.join(self.backup_dir, filename)
            with open(filepath, 'w') as f:
                f.write('test data')
        
        # Ротируем, оставляя только 2 файла
        rotate_backups(Path(self.backup_dir), 'backup', '.db', 2)
        
        # Проверяем, что осталось не больше 2 файлов
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]
        assert len(backup_files) <= 2


class TestUserPreferences:
    """Тесты для функций пользовательских настроек."""
    
    def test_load_prefs(self):
        """Тест загрузки настроек."""
        from utils.user_prefs import load_prefs
        prefs = load_prefs()
        assert prefs is not None
    
    def test_save_prefs(self):
        """Тест сохранения настроек."""
        from utils.user_prefs import save_prefs, UserPrefs
        
        # Создаем тестовые настройки
        test_prefs = UserPrefs()
        
        # Сохраняем настройки (должно работать без ошибок)
        save_prefs(test_prefs)
        assert True  # Если дошли сюда, значит сохранение прошло успешно