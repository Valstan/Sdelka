"""Тесты для компонентов GUI."""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch

from gui.components.tab_manager import TabManager
from gui.components.form_factory import FormFactory
from gui.components.sync_manager import SyncManager
from gui.components.ui_state_manager import UIStateManager


class TestTabManager:
    """Тесты для TabManager."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.root = ctk.CTk()
        self.tab_manager = TabManager(self.root)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.root.destroy()
    
    def test_init(self):
        """Тест инициализации TabManager."""
        assert self.tab_manager.parent == self.root
        assert self.tab_manager.tabview is None
        assert self.tab_manager.refs_tabs is None
    
    def test_create_main_tabs(self):
        """Тест создания основных вкладок."""
        tabview = self.tab_manager.create_main_tabs()
        
        assert tabview is not None
        assert self.tab_manager.tabview == tabview
        
        # Проверяем, что вкладки созданы
        tab_names = list(tabview._tab_dict.keys())
        expected_tabs = ["Наряды", "Справочники", "Отчеты", "Настройки"]
        
        for tab_name in expected_tabs:
            assert tab_name in tab_names
    
    def test_get_tab_frame(self):
        """Тест получения фрейма вкладки."""
        self.tab_manager.create_main_tabs()
        
        frame = self.tab_manager.get_tab_frame("Наряды")
        assert frame is not None
        
        frame = self.tab_manager.get_tab_frame("Несуществующая")
        assert frame is None
    
    def test_switch_to_tab(self):
        """Тест переключения на вкладку."""
        self.tab_manager.create_main_tabs()
        
        # Не должно вызывать исключений
        self.tab_manager.switch_to_tab("Наряды")
        self.tab_manager.switch_to_tab("Отчеты")


class TestFormFactory:
    """Тесты для FormFactory."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.form_factory = FormFactory()
    
    def test_init(self):
        """Тест инициализации FormFactory."""
        assert self.form_factory._forms_cache == {}
        assert self.form_factory._current_mode is None
    
    def test_create_form_invalid_type(self):
        """Тест создания формы с неверным типом."""
        root = ctk.CTk()
        
        with pytest.raises(ValueError, match="Неизвестный тип формы"):
            self.form_factory.create_form("invalid_type", root)
        
        root.destroy()
    
    @patch('gui.components.form_factory.is_readonly')
    def test_create_form_caching(self, mock_is_readonly):
        """Тест кэширования форм."""
        mock_is_readonly.return_value = False
        
        root = ctk.CTk()
        
        # Создаем форму первый раз
        form1 = self.form_factory.create_form('workers', root)
        assert form1 is not None
        
        # Создаем форму второй раз - должна быть закэширована
        form2 = self.form_factory.create_form('workers', root)
        assert form1 == form2
        
        root.destroy()
    
    def test_clear_cache(self):
        """Тест очистки кэша."""
        self.form_factory._forms_cache = {"test": Mock()}
        
        self.form_factory.clear_cache()
        
        assert self.form_factory._forms_cache == {}


class TestSyncManager:
    """Тесты для SyncManager."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.root = ctk.CTk()
        self.sync_manager = SyncManager(self.root)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.root.destroy()
    
    def test_init(self):
        """Тест инициализации SyncManager."""
        assert self.sync_manager.parent == self.root
        assert self.sync_manager._sync_progress_manager is not None
        assert self.sync_manager._sync_running is False
    
    @patch('services.auto_sync.sync_on_startup')
    def test_start_background_sync(self, mock_sync):
        """Тест запуска фоновой синхронизации."""
        mock_sync.return_value = None
        
        # Не должно вызывать исключений
        self.sync_manager.start_background_sync()
        
        # Даем время на запуск потока
        import time
        time.sleep(0.1)
        
        # Проверяем, что поток запущен
        assert self.sync_manager._sync_thread is not None
        assert self.sync_manager._sync_thread.is_alive()
    
    def test_cancel_sync(self):
        """Тест отмены синхронизации."""
        self.sync_manager.cancel_sync()
        
        assert self.sync_manager._sync_running is False
    
    def test_cleanup(self):
        """Тест очистки ресурсов."""
        # Не должно вызывать исключений
        self.sync_manager.cleanup()


class TestUIStateManager:
    """Тесты для UIStateManager."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.root = ctk.CTk()
        self.ui_state_manager = UIStateManager(self.root)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.root.destroy()
    
    def test_init(self):
        """Тест инициализации UIStateManager."""
        assert self.ui_state_manager.parent == self.root
        assert self.ui_state_manager._current_mode is None
        assert self.ui_state_manager._mode_change_callbacks == []
    
    @patch('gui.components.ui_state_manager.is_readonly')
    def test_initialize(self, mock_is_readonly):
        """Тест инициализации."""
        mock_is_readonly.return_value = False
        
        self.ui_state_manager.initialize()
        
        assert self.ui_state_manager._current_mode is False
    
    def test_add_remove_callback(self):
        """Тест добавления и удаления callback."""
        callback = Mock()
        
        self.ui_state_manager.add_mode_change_callback(callback)
        assert callback in self.ui_state_manager._mode_change_callbacks
        
        self.ui_state_manager.remove_mode_change_callback(callback)
        assert callback not in self.ui_state_manager._mode_change_callbacks
    
    @patch('gui.components.ui_state_manager.is_readonly')
    def test_get_current_mode(self, mock_is_readonly):
        """Тест получения текущего режима."""
        mock_is_readonly.return_value = True
        
        mode = self.ui_state_manager.get_current_mode()
        assert mode is True
    
    def test_cleanup(self):
        """Тест очистки ресурсов."""
        callback = Mock()
        self.ui_state_manager.add_mode_change_callback(callback)
        
        self.ui_state_manager.cleanup()
        
        assert self.ui_state_manager._mode_change_callbacks == []
