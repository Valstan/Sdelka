from __future__ import annotations

import customtkinter as ctk
import logging
from typing import Optional

from gui.components.tab_manager import TabManager
from gui.components.form_factory import FormFactory
from gui.components.sync_manager import SyncManager
from gui.components.ui_state_manager import UIStateManager
from utils.user_prefs import load_prefs
from utils.ui_theming import apply_user_fonts
from utils.versioning import get_version

logger = logging.getLogger(__name__)


class AppWindow(ctk.CTk):
    """Главное окно приложения с упрощенной архитектурой."""
    
    def __init__(self) -> None:
        super().__init__()
        
        # Инициализация компонентов
        self._init_window()
        self._init_components()
        self._build_ui()
        self._start_services()
    
    def _init_window(self) -> None:
        """Инициализирует основное окно."""
        try:
            # Получаем версию
            try:
                ver = get_version()
            except Exception:
                ver = "Unknown"
            
            self._version = ver
            self._app_title = f"СДЕЛКА РМЗ {ver}"
            self.title(self._app_title)
            
            # Настраиваем размер и состояние окна
            try:
                self.state("zoomed")
            except Exception:
                self.geometry("1600x900")
            
            self.resizable(True, True)
            
            # Настраиваем обработчик закрытия
            self.protocol("WM_DELETE_WINDOW", self._on_close)
            
            # Применяем пользовательские шрифты
            try:
                prefs = load_prefs()
                apply_user_fonts(self, prefs)
            except Exception as exc:
                logger.exception("Ошибка применения пользовательских шрифтов: %s", exc)
                
        except Exception as exc:
            logger.exception("Ошибка инициализации окна: %s", exc)
    
    def _init_components(self) -> None:
        """Инициализирует компоненты приложения."""
        try:
            # Создаем менеджеры
            self.tab_manager = TabManager(self)
            self.form_factory = FormFactory()
            self.sync_manager = SyncManager(self)
            self.ui_state_manager = UIStateManager(self)
            
            # Инициализируем состояние UI
            self.ui_state_manager.initialize()
            
            # Регистрируем callback для изменения режима
            self.ui_state_manager.add_mode_change_callback(self._on_mode_changed)
            
            logger.info("Компоненты приложения инициализированы")
            
        except Exception as exc:
            logger.exception("Ошибка инициализации компонентов: %s", exc)
    
    def _build_ui(self) -> None:
        """Строит пользовательский интерфейс."""
        try:
            # Создаем основные вкладки
            self.tabview = self.tab_manager.create_main_tabs()
            
            # Получаем фреймы вкладок
            self.tab_orders = self.tab_manager.get_tab_frame("Наряды")
            self.tab_refs = self.tab_manager.get_tab_frame("Справочники")
            self.tab_reports = self.tab_manager.get_tab_frame("Отчеты")
            self.tab_settings = self.tab_manager.get_tab_frame("Настройки")
            
            # Создаем формы для текущего режима
            self._build_forms_for_current_mode()
            
            logger.info("UI построен успешно")
            
        except Exception as exc:
            logger.exception("Ошибка построения UI: %s", exc)
    
    def _build_forms_for_current_mode(self) -> None:
        """Создает формы под текущий режим."""
        try:
            # Форма нарядов
            if self.tab_orders:
                self.form_work_orders = self.form_factory.create_work_orders_form(self.tab_orders)
            
            # Вкладки справочников
            if self.tab_refs:
                self.refs_tabs = self.tab_manager.create_refs_tabs(self.tab_refs)
                
                # Формы справочников
                workers_frame = self.tab_manager.get_refs_tab_frame("Работники")
                if workers_frame:
                    self.form_workers = self.form_factory.create_workers_form(workers_frame)
                
                job_types_frame = self.tab_manager.get_refs_tab_frame("Виды работ")
                if job_types_frame:
                    self.form_job_types = self.form_factory.create_job_types_form(job_types_frame)
                
                products_frame = self.tab_manager.get_refs_tab_frame("Изделия")
                if products_frame:
                    self.form_products = self.form_factory.create_products_form(products_frame)
                
                contracts_frame = self.tab_manager.get_refs_tab_frame("Контракты")
                if contracts_frame:
                    self.form_contracts = self.form_factory.create_contracts_form(contracts_frame)
            
            # Форма отчетов
            if self.tab_reports:
                self.form_reports = self.form_factory.create_reports_view(self.tab_reports)
            
            # Форма настроек
            if self.tab_settings:
                self.form_settings = self.form_factory.create_settings_view(self.tab_settings)
            
            logger.info("Формы созданы для режима: %s", 
                       "readonly" if self.ui_state_manager.is_readonly_mode() else "full")
            
        except Exception as exc:
            logger.exception("Ошибка создания форм: %s", exc)
    
    def _start_services(self) -> None:
        """Запускает сервисы приложения."""
        try:
            # Запускаем фоновую синхронизацию
            self.sync_manager.start_background_sync()
            
            # Запускаем периодическую синхронизацию
            self.sync_manager.start_periodic_sync()
            
            logger.info("Сервисы запущены")
            
        except Exception as exc:
            logger.exception("Ошибка запуска сервисов: %s", exc)
    
    def _on_mode_changed(self, readonly: bool) -> None:
        """Обработчик изменения режима."""
        try:
            logger.info("Режим изменен на: %s", "readonly" if readonly else "full")
            
            # Очищаем кэш форм
            self.form_factory.clear_cache()
            
            # Пересобираем формы
            self._build_forms_for_current_mode()
            
            # Обновляем UI
            self.ui_state_manager.update_ui_for_mode()
            
        except Exception as exc:
            logger.exception("Ошибка обработки изменения режима: %s", exc)
    
    def rebuild_forms_for_mode(self) -> None:
        """Пересобирает формы под текущий режим."""
        try:
            self._build_forms_for_current_mode()
            logger.info("Формы пересобраны")
        except Exception as exc:
            logger.exception("Ошибка пересборки форм: %s", exc)
    
    def _update_sync_status(self, status: str) -> None:
        """Обновляет статус синхронизации."""
        try:
            # Здесь можно добавить логику обновления статуса в UI
            logger.debug("Статус синхронизации: %s", status)
        except Exception as exc:
            logger.exception("Ошибка обновления статуса синхронизации: %s", exc)
    
    def _on_close(self) -> None:
        """Обработчик закрытия приложения."""
        try:
            logger.info("Закрытие приложения...")
            
            # Очищаем ресурсы компонентов
            self.sync_manager.cleanup()
            self.ui_state_manager.cleanup()
            self.tab_manager.destroy()
            
            # Закрываем окно
            self.destroy()
            
        except Exception as exc:
            logger.exception("Ошибка при закрытии приложения: %s", exc)
            self.destroy()
