from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from gui.forms.workers_form import WorkersForm
from gui.forms.job_types_form import JobTypesForm
from gui.forms.products_form import ProductsForm
from gui.forms.contracts_form import ContractsForm
from gui.forms.work_order_form import WorkOrdersForm
from gui.forms.reports_view import ReportsView
from gui.forms.settings_view import SettingsView
from utils.runtime_mode import is_readonly

logger = logging.getLogger(__name__)


class FormFactory:
    """Фабрика для создания форм приложения."""
    
    def __init__(self):
        self._forms_cache: Dict[str, Any] = {}
        self._current_mode: Optional[bool] = None
        
    def create_form(self, form_type: str, parent_frame, **kwargs) -> Any:
        """Создает форму указанного типа."""
        try:
            # Проверяем, нужно ли пересоздать форму из-за изменения режима
            current_mode = is_readonly()
            if self._current_mode != current_mode:
                self._clear_cache()
                self._current_mode = current_mode
            
            # Проверяем кэш
            cache_key = f"{form_type}_{current_mode}"
            if cache_key in self._forms_cache:
                form = self._forms_cache[cache_key]
                # Перемещаем форму в новый родительский фрейм
                form.pack_forget()
                form.pack(expand=True, fill="both", padx=5, pady=5)
                return form
            
            # Создаем новую форму
            form = self._create_new_form(form_type, parent_frame, **kwargs)
            
            # Кэшируем форму
            self._forms_cache[cache_key] = form
            
            return form
            
        except ValueError as exc:
            # Пробрасываем ValueError как есть
            raise exc
        except Exception as exc:
            logger.exception("Ошибка создания формы %s: %s", form_type, exc)
            return None
    
    def _create_new_form(self, form_type: str, parent_frame, **kwargs) -> Any:
        """Создает новую форму указанного типа."""
        form_classes = {
            'workers': WorkersForm,
            'job_types': JobTypesForm,
            'products': ProductsForm,
            'contracts': ContractsForm,
            'work_orders': WorkOrdersForm,
            'reports': ReportsView,
            'settings': SettingsView,
        }
        
        if form_type not in form_classes:
            raise ValueError(f"Неизвестный тип формы: {form_type}")
        
        form_class = form_classes[form_type]
        form = form_class(parent_frame, **kwargs)
        
        return form
    
    def create_work_orders_form(self, parent_frame) -> Optional[WorkOrdersForm]:
        """Создает форму нарядов."""
        return self.create_form('work_orders', parent_frame)
    
    def create_workers_form(self, parent_frame) -> Optional[WorkersForm]:
        """Создает форму работников."""
        return self.create_form('workers', parent_frame)
    
    def create_job_types_form(self, parent_frame) -> Optional[JobTypesForm]:
        """Создает форму видов работ."""
        return self.create_form('job_types', parent_frame)
    
    def create_products_form(self, parent_frame) -> Optional[ProductsForm]:
        """Создает форму изделий."""
        return self.create_form('products', parent_frame)
    
    def create_contracts_form(self, parent_frame) -> Optional[ContractsForm]:
        """Создает форму контрактов."""
        return self.create_form('contracts', parent_frame)
    
    def create_reports_view(self, parent_frame) -> Optional[ReportsView]:
        """Создает представление отчетов."""
        return self.create_form('reports', parent_frame)
    
    def create_settings_view(self, parent_frame) -> Optional[SettingsView]:
        """Создает представление настроек."""
        return self.create_form('settings', parent_frame)
    
    def _clear_cache(self) -> None:
        """Очищает кэш форм."""
        try:
            for form in self._forms_cache.values():
                if hasattr(form, 'destroy'):
                    form.destroy()
        except Exception as exc:
            logger.exception("Ошибка очистки кэша форм: %s", exc)
        finally:
            self._forms_cache.clear()
    
    def clear_cache(self) -> None:
        """Публичный метод для очистки кэша."""
        self._clear_cache()
    
    def get_cached_form(self, form_type: str) -> Optional[Any]:
        """Возвращает кэшированную форму."""
        current_mode = is_readonly()
        cache_key = f"{form_type}_{current_mode}"
        return self._forms_cache.get(cache_key)
    
    def is_form_cached(self, form_type: str) -> bool:
        """Проверяет, закэширована ли форма."""
        current_mode = is_readonly()
        cache_key = f"{form_type}_{current_mode}"
        return cache_key in self._forms_cache
