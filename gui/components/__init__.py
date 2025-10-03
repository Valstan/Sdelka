"""Компоненты пользовательского интерфейса."""

from .tab_manager import TabManager
from .form_factory import FormFactory
from .sync_manager import SyncManager
from .ui_state_manager import UIStateManager

__all__ = [
    'TabManager',
    'FormFactory', 
    'SyncManager',
    'UIStateManager',
]
