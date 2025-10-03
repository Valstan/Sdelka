from __future__ import annotations

import customtkinter as ctk
import tkinter.font as tkfont
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TabManager:
    """Управляет вкладками главного окна приложения."""
    
    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.tabview: Optional[ctk.CTkTabview] = None
        self.refs_tabs: Optional[ctk.CTkTabview] = None
        self._tab_font_normal: Optional[tkfont.Font] = None
        self._tab_font_active: Optional[tkfont.Font] = None
        
    def create_main_tabs(self) -> ctk.CTkTabview:
        """Создает основные вкладки приложения."""
        tabview = ctk.CTkTabview(self.parent)
        tabview.pack(expand=True, fill="both", pady=(5, 0))
        self.tabview = tabview
        
        # Добавляем основные вкладки
        tabview.add("Наряды")
        tabview.add("Справочники") 
        tabview.add("Отчеты")
        tabview.add("Настройки")
        
        # Настраиваем шрифты
        self._setup_tab_fonts(tabview)
        
        return tabview
    
    def create_refs_tabs(self, parent_frame) -> ctk.CTkTabview:
        """Создает вкладки для справочников."""
        refs_tabs = ctk.CTkTabview(parent_frame)
        refs_tabs.pack(expand=True, fill="both", pady=(5, 0))
        self.refs_tabs = refs_tabs
        
        # Добавляем вкладки справочников
        refs_tabs.add("Работники")
        refs_tabs.add("Виды работ")
        refs_tabs.add("Изделия")
        refs_tabs.add("Контракты")
        
        # Настраиваем шрифты
        self._setup_tab_fonts(refs_tabs)
        
        return refs_tabs
    
    def _setup_tab_fonts(self, tabview: ctk.CTkTabview) -> None:
        """Настраивает шрифты для вкладок."""
        try:
            if self._tab_font_normal is None:
                self._tab_font_normal = tkfont.Font(
                    family="Segoe UI", size=11, weight="normal"
                )
            if self._tab_font_active is None:
                self._tab_font_active = tkfont.Font(
                    family="Segoe UI", size=11, weight="bold"
                )
            
            # Применяем шрифты к вкладкам
            # CustomTkinter не поддерживает прямое изменение шрифтов вкладок
            # Поэтому просто сохраняем шрифты для возможного использования
            logger.debug("Шрифты вкладок настроены")
                    
        except Exception as exc:
            logger.exception("Ошибка настройки шрифтов вкладок: %s", exc)
    
    def get_tab_frame(self, tab_name: str) -> Optional[ctk.CTkFrame]:
        """Возвращает фрейм указанной вкладки."""
        if self.tabview and tab_name in self.tabview._tab_dict:
            return self.tabview._tab_dict[tab_name]
        return None
    
    def get_refs_tab_frame(self, tab_name: str) -> Optional[ctk.CTkFrame]:
        """Возвращает фрейм указанной вкладки справочников."""
        if self.refs_tabs and tab_name in self.refs_tabs._tab_dict:
            return self.refs_tabs._tab_dict[tab_name]
        return None
    
    def switch_to_tab(self, tab_name: str) -> None:
        """Переключается на указанную вкладку."""
        if self.tabview:
            try:
                self.tabview.set(tab_name)
            except Exception as exc:
                logger.exception("Ошибка переключения на вкладку %s: %s", tab_name, exc)
    
    def switch_to_refs_tab(self, tab_name: str) -> None:
        """Переключается на указанную вкладку справочников."""
        if self.refs_tabs:
            try:
                self.refs_tabs.set(tab_name)
            except Exception as exc:
                logger.exception("Ошибка переключения на вкладку справочников %s: %s", tab_name, exc)
    
    def destroy(self) -> None:
        """Очищает ресурсы."""
        if self.tabview:
            self.tabview.destroy()
        if self.refs_tabs:
            self.refs_tabs.destroy()
