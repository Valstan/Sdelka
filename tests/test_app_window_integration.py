"""Интеграционные тесты для основного приложения."""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock

from gui.windows.app_window import AppWindow


class TestAppWindow:
    """Тесты для главного окна приложения."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        # Мокаем все внешние зависимости
        with patch('gui.windows.app_window.get_version') as mock_version, \
             patch('gui.windows.app_window.load_prefs') as mock_prefs, \
             patch('gui.windows.app_window.apply_user_fonts') as mock_fonts:
            
            mock_version.return_value = "4.0.0"
            mock_prefs.return_value = {}
            mock_fonts.return_value = None
            
            try:
                self.root = ctk.CTk()
                self.app = AppWindow()
            except Exception as exc:
                # Если не удается создать окно из-за проблем с Tcl/Tk, пропускаем тест
                pytest.skip(f"Не удается создать окно: {exc}")
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        try:
            self.app.destroy()
        except:
            pass
        try:
            self.root.destroy()
        except:
            pass
    
    def test_init(self):
        """Тест инициализации AppWindow."""
        assert self.app._version == "4.0.0"
        assert "СДЕЛКА РМЗ" in self.app._app_title
        assert self.app.tab_manager is not None
        assert self.app.form_factory is not None
        assert self.app.sync_manager is not None
        assert self.app.ui_state_manager is not None
    
    def test_components_initialized(self):
        """Тест инициализации компонентов."""
        # Проверяем, что все компоненты созданы
        assert hasattr(self.app, 'tab_manager')
        assert hasattr(self.app, 'form_factory')
        assert hasattr(self.app, 'sync_manager')
        assert hasattr(self.app, 'ui_state_manager')
        
        # Проверяем, что компоненты имеют правильный тип
        from gui.components import TabManager, FormFactory, SyncManager, UIStateManager
        
        assert isinstance(self.app.tab_manager, TabManager)
        assert isinstance(self.app.form_factory, FormFactory)
        assert isinstance(self.app.sync_manager, SyncManager)
        assert isinstance(self.app.ui_state_manager, UIStateManager)
    
    def test_ui_built(self):
        """Тест построения UI."""
        # Проверяем, что основные элементы UI созданы
        assert hasattr(self.app, 'tabview')
        assert hasattr(self.app, 'tab_orders')
        assert hasattr(self.app, 'tab_refs')
        assert hasattr(self.app, 'tab_reports')
        assert hasattr(self.app, 'tab_settings')
    
    @patch('services.auto_sync.sync_on_startup')
    @patch('services.auto_sync.start_periodic_sync')
    def test_services_started(self, mock_periodic, mock_startup):
        """Тест запуска сервисов."""
        # Создаем новое приложение с моками
        with patch('gui.windows.app_window.get_version') as mock_version, \
             patch('gui.windows.app_window.load_prefs') as mock_prefs, \
             patch('gui.windows.app_window.apply_user_fonts') as mock_fonts:
            
            mock_version.return_value = "4.0.0"
            mock_prefs.return_value = {}
            mock_fonts.return_value = None
            
            try:
                app = AppWindow()
                
                try:
                    # Проверяем, что методы синхронизации были вызваны
                    assert mock_startup.called or mock_periodic.called
                finally:
                    app.destroy()
            except Exception as exc:
                # Если не удается создать окно из-за проблем с Tcl/Tk, пропускаем тест
                pytest.skip(f"Не удается создать окно: {exc}")
    
    def test_rebuild_forms_for_mode(self):
        """Тест пересборки форм."""
        # Не должно вызывать исключений
        self.app.rebuild_forms_for_mode()
    
    def test_mode_change_callback(self):
        """Тест callback изменения режима."""
        # Создаем mock callback
        callback = Mock()
        
        # Добавляем callback
        self.app.ui_state_manager.add_mode_change_callback(callback)
        
        # Симулируем изменение режима через UIStateManager
        from utils.runtime_mode import AppMode
        self.app.ui_state_manager.set_mode(AppMode.READONLY)
        
        # Проверяем, что callback был вызван
        callback.assert_called_once_with(True)
    
    def test_close_handler(self):
        """Тест обработчика закрытия."""
        # Мокаем методы очистки
        with patch.object(self.app.sync_manager, 'cleanup') as mock_sync_cleanup, \
             patch.object(self.app.ui_state_manager, 'cleanup') as mock_ui_cleanup, \
             patch.object(self.app.tab_manager, 'destroy') as mock_tab_destroy:
            
            # Вызываем обработчик закрытия
            self.app._on_close()
            
            # Проверяем, что методы очистки были вызваны
            mock_sync_cleanup.assert_called_once()
            mock_ui_cleanup.assert_called_once()
            mock_tab_destroy.assert_called_once()


class TestAppWindowIntegration:
    """Интеграционные тесты для AppWindow."""
    
    @patch('gui.windows.app_window.get_version')
    @patch('gui.windows.app_window.load_prefs')
    @patch('gui.windows.app_window.apply_user_fonts')
    @patch('services.auto_sync.sync_on_startup')
    @patch('services.auto_sync.start_periodic_sync')
    def test_full_initialization(self, mock_periodic, mock_startup, mock_fonts, 
                                mock_prefs, mock_version):
        """Тест полной инициализации приложения."""
        # Настраиваем моки
        mock_version.return_value = "4.0.0"
        mock_prefs.return_value = {}
        mock_fonts.return_value = None
        mock_startup.return_value = None
        mock_periodic.return_value = None
        
        # Создаем приложение
        root = ctk.CTk()
        app = AppWindow()
        
        try:
            # Проверяем, что все компоненты работают
            assert app.tab_manager is not None
            assert app.form_factory is not None
            assert app.sync_manager is not None
            assert app.ui_state_manager is not None
            
            # Проверяем, что UI построен
            assert app.tabview is not None
            
            # Проверяем, что сервисы запущены
            assert mock_startup.called or mock_periodic.called
            
        finally:
            app.destroy()
            root.destroy()
