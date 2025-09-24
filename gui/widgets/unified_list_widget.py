"""
Единый виджет для управления списками (Изделия, Виды работ, Работники)
Обеспечивает одинаковое поведение и оформление для всех типов списков
"""

from __future__ import annotations

import customtkinter as ctk
import logging
from typing import Optional, Callable, Dict, Any, List, Tuple
from dataclasses import dataclass

from utils.modern_theme import (
    create_modern_frame, create_modern_label, create_modern_button,
    create_modern_entry, create_modern_scrollable_frame, get_color
)
from utils.autocomplete_positioning import (
    place_suggestions_under_entry,
    create_suggestion_button,
    create_suggestions_frame,
)

logger = logging.getLogger(__name__)


@dataclass
class ListItem:
    """Элемент списка"""
    id: Any
    name: str
    data: Dict[str, Any] = None


@dataclass
class ListConfig:
    """Конфигурация для типа списка"""
    title: str
    placeholder: str
    suggest_function: Optional[Callable] = None
    columns: List[str] = None  # Для табличного вида
    show_amount_field: bool = False  # Показать поле суммы (для работников)
    show_quantity_field: bool = False  # Показать поле количества (для видов работ)
    show_price_field: bool = False  # Показать поле цены (для видов работ)
    show_total_field: bool = False  # Показать поле общей суммы (для видов работ)
    on_price_change: Optional[Callable] = None  # Callback для изменения цены


class UnifiedListWidget(ctk.CTkFrame):
    """Единый виджет для управления списками"""
    
    def __init__(
        self,
        parent,
        config: ListConfig,
        on_item_add: Optional[Callable[[Any, str], None]] = None,
        on_item_remove: Optional[Callable[[Any], None]] = None,
        on_item_change: Optional[Callable[[Any, str], None]] = None,
        on_amount_change: Optional[Callable[[Any, float], None]] = None,
        readonly: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.config = config
        self.on_item_add = on_item_add
        self.on_item_remove = on_item_remove
        self.on_item_change = on_item_change
        self.on_amount_change = on_amount_change
        self.readonly = readonly
        
        # Данные списка
        self.items: Dict[Any, ListItem] = {}
        self.manual_counter = -1
        self._total_vars: Dict[Any, ctk.StringVar] = {}  # Для хранения переменных общей суммы
        self._price_vars: Dict[Any, ctk.StringVar] = {}  # Для хранения переменных цены
        self._quantity_vars: Dict[Any, ctk.StringVar] = {}  # Для хранения переменных количества
        self._saved_values: Dict[Any, Dict[str, str]] = {}  # Для сохранения значений при обновлении
        
        # UI элементы
        self._setup_ui()
        
        # Фрейм подсказок
        self.suggestions_frame = create_suggestions_frame(self)
        self.suggestions_frame.place_forget()
        
        # Добавляем пустую строку для ввода
        self._add_empty_row()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        # Заголовок
        title_label = create_modern_label(
            self,
            text=self.config.title,
            style_type="label",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w", padx=5, pady=(5, 0))
        
        # Прокручиваемый список
        self.list_frame = create_modern_scrollable_frame(
            self,
            style_type="scrollable_frame"
        )
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Настройка прокрутки
        self._setup_scrolling()
    
    def _setup_scrolling(self):
        """Настройка прокрутки для списка"""
        try:
            can_items = self.list_frame._parent_canvas
            sb_items = self.list_frame._scrollbar
            can_items.configure(yscrollcommand=sb_items.set)
            sb_items.configure(command=lambda *args: (can_items.yview(*args), "break"))

            def _refresh_scrollregion(_e=None):
                try:
                    can_items.configure(scrollregion=can_items.bbox("all"))
                except Exception as exc:
                    logger.exception("Ошибка обновления scrollregion: %s", exc)

            self.list_frame.bind("<Configure>", _refresh_scrollregion, add="+")

            def _on_mousewheel(event):
                try:
                    step = 3
                    delta = 0
                    if hasattr(event, "delta") and event.delta:
                        delta = int(-1 * (event.delta / 120) * step)
                    elif getattr(event, "num", None) == 4:
                        delta = -step
                    elif getattr(event, "num", None) == 5:
                        delta = step
                    if delta:
                        can_items.yview_scroll(delta, "units")
                        return "break"
                except Exception:
                    return None

            for widget in (can_items, self.list_frame):
                widget.bind("<MouseWheel>", _on_mousewheel, add="+")
                widget.bind("<Button-4>", _on_mousewheel, add="+")
                widget.bind("<Button-5>", _on_mousewheel, add="+")
        except Exception as exc:
            logger.exception("Ошибка настройки прокрутки: %s", exc)
    
    def _add_empty_row(self):
        """Добавить пустую строку для ввода"""
        if self.readonly:
            return
            
        self.manual_counter -= 1
        empty_id = self.manual_counter
        
        # Создаем пустой элемент
        empty_item = ListItem(id=empty_id, name="")
        self.items[empty_id] = empty_item
        
        self._refresh_display()
    
    def _refresh_display(self):
        """Обновить отображение списка"""
        # Сохраняем текущие данные полей
        self._save_current_field_values()
        
        # Очищаем список
        for child in self.list_frame.winfo_children():
            try:
                child.destroy()
            except Exception as exc:
                logger.exception("Ошибка удаления дочернего элемента: %s", exc)
        
        # Создаем строки для каждого элемента
        for item_id, item in self.items.items():
            self._create_item_row(item_id, item)
            
        # Восстанавливаем данные полей
        self._restore_field_values()
    
    def _create_item_row(self, item_id: Any, item: ListItem):
        """Создать строку элемента"""
        row_frame = create_modern_frame(self.list_frame, style_type="frame")
        row_frame.pack(fill="x", pady=2)
        
        # Поле ввода названия
        name_var = ctk.StringVar(value=item.name)
        name_entry = create_modern_entry(
            row_frame,
            textvariable=name_var,
            placeholder_text=self.config.placeholder
        )
        name_entry.pack(side="left", padx=4, fill="x", expand=True)
        
        # Бинды для автодополнения
        if self.config.suggest_function and not self.readonly:
            def _show_suggestions(evt=None, ent=name_entry):
                self._handle_suggestions(ent, item_id)
            
            name_entry.bind("<KeyRelease>", _show_suggestions)
            name_entry.bind("<FocusIn>", _show_suggestions)
        
        # Поле количества (для видов работ)
        if self.config.show_quantity_field and not self.readonly:
            qty_var = ctk.StringVar(value="1")  # По умолчанию 1
            self._quantity_vars[item_id] = qty_var
            qty_entry = create_modern_entry(
                row_frame,
                textvariable=qty_var,
                width=80,
                placeholder_text="Кол-во"
            )
            qty_entry.pack(side="left", padx=4)
            
            def _on_qty_change(_e=None, var=qty_var, i=item_id):
                try:
                    qty = float(var.get() or "0")
                    if self.on_amount_change:
                        self.on_amount_change(i, qty)
                    # Пересчитываем общую сумму если есть цена
                    self._update_total_for_item(item_id)
                except ValueError:
                    pass
            
            qty_entry.bind("<KeyRelease>", _on_qty_change)
        
        # Поле цены (для видов работ)
        if self.config.show_price_field and not self.readonly:
            price_var = ctk.StringVar(value="0.00")
            self._price_vars[item_id] = price_var
            price_entry = create_modern_entry(
                row_frame,
                textvariable=price_var,
                width=80,
                placeholder_text="Цена"
            )
            price_entry.pack(side="left", padx=4)
            
            def _on_price_change(_e=None, var=price_var, i=item_id):
                try:
                    price = float(var.get() or "0")
                    # Пересчитываем общую сумму
                    self._update_total_for_item(item_id)
                except ValueError:
                    pass
            
            price_entry.bind("<KeyRelease>", _on_price_change)
        
        # Поле общей суммы (для видов работ, только для чтения)
        if self.config.show_total_field and not self.readonly:
            total_var = ctk.StringVar(value="0.00")
            total_entry = create_modern_entry(
                row_frame,
                textvariable=total_var,
                width=100,
                placeholder_text="Сумма",
                state="readonly"
            )
            total_entry.pack(side="left", padx=4)
            
            # Сохраняем ссылку на переменную для обновления
            self._total_vars[item_id] = total_var
        
        # Поле суммы (для работников)
        if self.config.show_amount_field and not self.readonly:
            amount_var = ctk.StringVar(value="0.00")
            amount_entry = create_modern_entry(
                row_frame,
                textvariable=amount_var,
                width=100,
                placeholder_text="Сумма"
            )
            amount_entry.pack(side="left", padx=4)
            
            def _on_amount_change(_e=None, var=amount_var, i=item_id):
                try:
                    amount = float(var.get() or "0")
                    if self.on_amount_change:
                        self.on_amount_change(i, amount)
                except ValueError:
                    pass
            
            amount_entry.bind("<KeyRelease>", _on_amount_change)
        
        # Кнопки управления
        if not self.readonly:
            # Кнопка добавления
            add_btn = create_modern_button(
                row_frame,
                text="+",
                style_type="button_primary",
                width=28,
                command=self._add_empty_row
            )
            add_btn.pack(side="left", padx=4)
            
            # Кнопка удаления
            del_btn = create_modern_button(
                row_frame,
                text="Удалить",
                style_type="button_danger",
                width=80,
                command=lambda: self._remove_item(item_id)
            )
            del_btn.pack(side="left", padx=4)
    
    def _handle_suggestions(self, entry: ctk.CTkEntry, item_id: Any):
        """Обработать показ подсказок"""
        if not self.config.suggest_function:
            return
            
        try:
            # Очищаем предыдущие подсказки
            for w in self.suggestions_frame.winfo_children():
                w.destroy()
            
            # Показываем подсказки
            place_suggestions_under_entry(entry, self.suggestions_frame, self)
            
            text = (entry.get() or "").strip()
            if not text:
                self.suggestions_frame.place_forget()
                return
            
            # Получаем подсказки
            suggestions = self.config.suggest_function(text, 10)
            
            for suggestion_data in suggestions:
                # Поддерживаем как старый формат (id, name), так и новый (id, name, price)
                if len(suggestion_data) == 2:
                    suggestion_id, suggestion_label = suggestion_data
                    price = 0.0
                else:
                    suggestion_id, suggestion_label, price = suggestion_data
                
                btn = create_suggestion_button(
                    self.suggestions_frame,
                    text=suggestion_label,
                    command=lambda i=suggestion_id, l=suggestion_label, p=price, ent=entry, idx=item_id: 
                        self._pick_suggestion(idx, i, l, ent, p)
                )
                btn.pack(fill="x", padx=2, pady=1)
                
        except Exception as exc:
            logger.exception("Ошибка обработки подсказок: %s", exc)
    
    def _pick_suggestion(self, row_id: Any, suggestion_id: Any, suggestion_label: str, entry: ctk.CTkEntry, price: float = 0.0):
        """Обработать выбор подсказки"""
        try:
            # Обновляем поле ввода
            entry.delete(0, "end")
            entry.insert(0, suggestion_label)
            
            # Обновляем элемент с данными включая цену
            if row_id in self.items:
                item_data = self.items[row_id].data or {}
                item_data['price'] = price
                self.items[row_id] = ListItem(id=suggestion_id, name=suggestion_label, data=item_data)
            
            # Обновляем цену в поле если оно есть
            self._update_price_field(row_id, price)
            
            # Пересчитываем общую сумму
            self._update_total_for_item(row_id)
            
            # Скрываем подсказки
            self.suggestions_frame.place_forget()
            
            # Вызываем callback
            if self.on_item_add:
                self.on_item_add(suggestion_id, suggestion_label)
                
        except Exception as exc:
            logger.exception("Ошибка выбора подсказки: %s", exc)
    
    def _remove_item(self, item_id: Any):
        """Удалить элемент"""
        if item_id in self.items:
            del self.items[item_id]
            
            # Удаляем из всех словарей если есть
            if item_id in self._total_vars:
                del self._total_vars[item_id]
            if item_id in self._price_vars:
                del self._price_vars[item_id]
            if item_id in self._quantity_vars:
                del self._quantity_vars[item_id]
            
            if self.on_item_remove:
                self.on_item_remove(item_id)
            
            self._refresh_display()
    
    def _update_total_for_item(self, item_id: Any):
        """Обновить общую сумму для элемента"""
        if item_id not in self._total_vars:
            return
            
        try:
            # Получаем значения из полей ввода
            quantity = 0.0
            price = 0.0
            
            if item_id in self._quantity_vars:
                quantity = float(self._quantity_vars[item_id].get() or "0")
            
            if item_id in self._price_vars:
                price = float(self._price_vars[item_id].get() or "0")
            
            total = quantity * price
            self._total_vars[item_id].set(f"{total:.2f}")
        except (ValueError, TypeError):
            self._total_vars[item_id].set("0.00")
    
    def _update_price_field(self, item_id: Any, price: float):
        """Обновить поле цены для элемента"""
        # Обновляем поле ввода цены
        if item_id in self._price_vars:
            self._price_vars[item_id].set(f"{price:.2f}")
        
        # Обновляем данные элемента
        if item_id in self.items:
            if self.items[item_id].data is None:
                self.items[item_id].data = {}
            self.items[item_id].data['price'] = price
        
        # Пересчитываем общую сумму
        self._update_total_for_item(item_id)
        
        # Вызываем callback для пересчета сумм работников
        if self.config.on_price_change:
            self.config.on_price_change(item_id, price)
    
    def add_item(self, item_id: Any, name: str, data: Dict[str, Any] = None):
        """Добавить элемент в список"""
        item = ListItem(id=item_id, name=name, data=data or {})
        self.items[item_id] = item
        self._refresh_display()
    
    def remove_item(self, item_id: Any):
        """Удалить элемент из списка"""
        self._remove_item(item_id)
    
    def clear_items(self):
        """Очистить список"""
        self.items.clear()
        self._total_vars.clear()
        self._price_vars.clear()
        self._quantity_vars.clear()
        self._saved_values.clear()
        if not self.readonly:
            self._add_empty_row()
        else:
            self._refresh_display()
    
    def get_items(self) -> List[ListItem]:
        """Получить список элементов"""
        return list(self.items.values())
    
    def get_items_data(self) -> List[Dict[str, Any]]:
        """Получить данные всех элементов для сохранения"""
        result = []
        for item_id, item in self.items.items():
            data = {
                'id': item_id,
                'name': item.name,
                'quantity': 0.0,
                'price': 0.0,
                'total': 0.0
            }
            
            # Получаем количество
            if item_id in self._quantity_vars:
                try:
                    data['quantity'] = float(self._quantity_vars[item_id].get() or "0")
                except ValueError:
                    data['quantity'] = 0.0
            
            # Получаем цену
            if item_id in self._price_vars:
                try:
                    data['price'] = float(self._price_vars[item_id].get() or "0")
                except ValueError:
                    data['price'] = 0.0
            
            # Рассчитываем общую сумму
            data['total'] = data['quantity'] * data['price']
            
            result.append(data)
        
        return result
    
    def _save_current_field_values(self):
        """Сохранить текущие значения полей"""
        self._saved_values = {}
        for item_id in self.items.keys():
            values = {}
            if item_id in self._quantity_vars:
                values['quantity'] = self._quantity_vars[item_id].get()
            if item_id in self._price_vars:
                values['price'] = self._price_vars[item_id].get()
            if item_id in self._total_vars:
                values['total'] = self._total_vars[item_id].get()
            self._saved_values[item_id] = values
    
    def _restore_field_values(self):
        """Восстановить значения полей"""
        if not hasattr(self, '_saved_values'):
            return
            
        for item_id, values in self._saved_values.items():
            if item_id in self._quantity_vars and 'quantity' in values:
                self._quantity_vars[item_id].set(values['quantity'])
            if item_id in self._price_vars and 'price' in values:
                self._price_vars[item_id].set(values['price'])
            if item_id in self._total_vars and 'total' in values:
                self._total_vars[item_id].set(values['total'])
    
    def get_item_ids(self) -> List[Any]:
        """Получить список ID элементов"""
        return [item.id for item in self.items.values() if item.id > 0]
    
    def set_items(self, items: List[Tuple[Any, str, Dict[str, Any]]]):
        """Установить список элементов"""
        self.items.clear()
        for item_id, name, data in items:
            item = ListItem(id=item_id, name=name, data=data or {})
            self.items[item_id] = item
        
        if not self.readonly:
            self._add_empty_row()
        else:
            self._refresh_display()


def create_products_list(parent, **kwargs) -> UnifiedListWidget:
    """Создать список изделий"""
    from services import suggestions
    from config.settings import CONFIG
    from db.sqlite import get_connection
    
    def suggest_products(text: str, limit: int) -> List[Tuple[int, str]]:
        try:
            with get_connection() as conn:
                return suggestions.suggest_products(conn, text, limit)
        except Exception:
            return []
    
    config = ListConfig(
        title="Изделия",
        placeholder="Номер/Название изделия",
        suggest_function=suggest_products
    )
    
    return UnifiedListWidget(parent, config, **kwargs)


def create_workers_list(parent, **kwargs) -> UnifiedListWidget:
    """Создать список работников"""
    from services import suggestions
    from config.settings import CONFIG
    from db.sqlite import get_connection
    
    def suggest_workers(text: str, limit: int) -> List[Tuple[int, str]]:
        try:
            with get_connection() as conn:
                return suggestions.suggest_workers(conn, text, limit)
        except Exception:
            return []
    
    config = ListConfig(
        title="Работники",
        placeholder="ФИО работника",
        suggest_function=suggest_workers,
        show_amount_field=True
    )
    
    return UnifiedListWidget(parent, config, **kwargs)


def create_job_types_list(parent, **kwargs) -> UnifiedListWidget:
    """Создать список видов работ"""
    from services import suggestions
    from config.settings import CONFIG
    from db.sqlite import get_connection
    
    def suggest_job_types(text: str, limit: int) -> List[Tuple[int, str, float]]:
        try:
            with get_connection() as conn:
                return suggestions.suggest_job_types(conn, text, limit)
        except Exception:
            return []
    
    config = ListConfig(
        title="Виды работ",
        placeholder="Название вида работ",
        suggest_function=suggest_job_types,
        show_quantity_field=True,
        show_price_field=True,
        show_total_field=True,
        on_price_change=kwargs.get('on_price_change')
    )
    
    return UnifiedListWidget(parent, config, **kwargs)
