from __future__ import annotations

import logging
from typing import Optional, Callable, List
from utils.runtime_mode import is_readonly, set_mode, AppMode

logger = logging.getLogger(__name__)


class UIStateManager:
    """Управляет состоянием UI приложения."""
    
    def __init__(self, parent):
        self.parent = parent
        self._current_mode: Optional[bool] = None
        self._mode_change_callbacks: List[Callable[[bool], None]] = []
        
    def initialize(self) -> None:
        """Инициализирует менеджер состояния."""
        try:
            self._current_mode = is_readonly()
            logger.info("UIStateManager инициализирован, режим: %s", 
                       "readonly" if self._current_mode else "full")
        except Exception as exc:
            logger.exception("Ошибка инициализации UIStateManager: %s", exc)
    
    def add_mode_change_callback(self, callback: Callable[[bool], None]) -> None:
        """Добавляет callback для изменения режима."""
        self._mode_change_callbacks.append(callback)
    
    def remove_mode_change_callback(self, callback: Callable[[bool], None]) -> None:
        """Удаляет callback для изменения режима."""
        if callback in self._mode_change_callbacks:
            self._mode_change_callbacks.remove(callback)
    
    def set_mode(self, mode: AppMode) -> None:
        """Устанавливает режим приложения."""
        try:
            set_mode(mode)
            new_readonly = is_readonly()
            
            if self._current_mode != new_readonly:
                self._current_mode = new_readonly
                self._notify_mode_change(new_readonly)
                logger.info("Режим изменен на: %s", 
                           "readonly" if new_readonly else "full")
                
        except Exception as exc:
            logger.exception("Ошибка установки режима: %s", exc)
    
    def get_current_mode(self) -> bool:
        """Возвращает текущий режим (True = readonly, False = full)."""
        return self._current_mode if self._current_mode is not None else is_readonly()
    
    def is_readonly_mode(self) -> bool:
        """Проверяет, находится ли приложение в режиме только для чтения."""
        return self.get_current_mode()
    
    def is_full_mode(self) -> bool:
        """Проверяет, находится ли приложение в полном режиме."""
        return not self.get_current_mode()
    
    def _notify_mode_change(self, readonly: bool) -> None:
        """Уведомляет все зарегистрированные callback'и об изменении режима."""
        for callback in self._mode_change_callbacks:
            try:
                callback(readonly)
            except Exception as exc:
                logger.exception("Ошибка в callback изменения режима: %s", exc)
    
    def rebuild_forms_for_mode(self) -> None:
        """Пересобирает формы под текущий режим."""
        try:
            if hasattr(self.parent, 'rebuild_forms_for_mode'):
                self.parent.rebuild_forms_for_mode()
            logger.info("Формы пересобраны для режима: %s", 
                       "readonly" if self.is_readonly_mode() else "full")
        except Exception as exc:
            logger.exception("Ошибка пересборки форм: %s", exc)
    
    def update_ui_for_mode(self) -> None:
        """Обновляет UI под текущий режим."""
        try:
            readonly = self.is_readonly_mode()
            
            # Обновляем заголовок окна
            if hasattr(self.parent, '_update_title_for_mode'):
                self.parent._update_title_for_mode(readonly)
            
            # Обновляем доступность элементов управления
            if hasattr(self.parent, '_update_controls_accessibility'):
                self.parent._update_controls_accessibility(readonly)
                
            logger.info("UI обновлен для режима: %s", 
                       "readonly" if readonly else "full")
                       
        except Exception as exc:
            logger.exception("Ошибка обновления UI: %s", exc)
    
    def cleanup(self) -> None:
        """Очищает ресурсы."""
        try:
            self._mode_change_callbacks.clear()
            logger.info("UIStateManager очищен")
        except Exception as exc:
            logger.exception("Ошибка очистки UIStateManager: %s", exc)
