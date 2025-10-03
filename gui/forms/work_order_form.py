from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

from config.settings import CONFIG
from db.sqlite import get_connection
from services import suggestions
from services.work_orders import (
    WorkOrderInput,
    WorkOrderItemInput,
    WorkOrderWorkerInput,
    create_work_order,
)
from services.validation import validate_date
from db import queries as q
from gui.widgets.date_picker import open_for_anchor
from utils.usage_history import record_use, get_recent
from utils.autocomplete_positioning import (
    place_suggestions_under_entry,
    create_suggestion_button,
    create_suggestions_frame,
)
from utils.modern_theme import (
    create_modern_button, create_modern_frame, create_modern_label,
    create_modern_entry, create_modern_tabview, create_modern_scrollable_frame,
    configure_widget_style, get_color
)
from gui.widgets.unified_list_widget import (
    create_products_list, create_workers_list, create_job_types_list
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class ItemRow:
    job_type_id: int
    job_type_name: str
    quantity: float
    unit_price: float
    line_amount: float


class WorkOrdersForm(ctk.CTkFrame):
    def __init__(self, master, readonly: bool = False) -> None:
        super().__init__(master)
        self._readonly = readonly
        self.selected_contract_id: Optional[int] = None
        self.selected_product_ids: list[int] = []  # Список изделий
        self.selected_products: dict[int, str] = {}  # Словарь изделий (id -> название)
        self.selected_workers: dict[int, str] = {}
        self.worker_amounts: dict[int, float] = {}
        self._worker_amount_vars: dict[int, ctk.StringVar] = {}
        self._manual_amount_ids: set[int] = set()
        self._manual_mode: bool = False
        self._edit_locked: bool = False
        self.item_rows: list[ItemRow] = []
        self.editing_order_id: Optional[int] = None
        self._manual_worker_counter = -1  # Инициализируем счетчик для ручных работников
        self._manual_product_counter = -1  # Инициализируем счетчик для ручных изделий

        # Ширины столбцов для списка работ (в пикселях)
        self._col_pad_px: int = 8
        self._col_qty_w: int = 80
        self._col_price_w: int = 90
        self._col_amount_w: int = 110
        self._col_delete_w: int = 90
        self._item_row_widgets: list[ctk.CTkLabel] = (
            []
        )  # ссылки на label названий работ для обрезки
        self._item_widgets: list[dict] = (
            []
        )  # все виджеты строк (грид в общем контейнере)

        # Пагинация списка нарядов
        self._orders_page_size: int = 100
        self._orders_offset: int = 0
        self._orders_loading: bool = False
        self._orders_can_load_more: bool = True
        self._orders_vsb: ttk.Scrollbar | None = None

        # Инициализация коллекций для доп. полей
        self._extra_product_entries: list[ctk.CTkEntry] = []

        self._build_ui()
        # Стартовые пустые строки
        # Старый метод _add_blank_item_row удален - используется новый виджет видов работ
        # Старый метод _refresh_workers_display удален
        # Старый метод _refresh_products_display удален
        self._update_totals()
        self._load_recent_orders()

    def _build_ui(self) -> None:
        # Контейнер без разделителя: правая панель фиксированной ширины, левая — остальное
        container = ctk.CTkFrame(self)
        container.pack(expand=True, fill="both")

        # Right side (orders list) — пакуем справа, ширина управляется программно
        right = ctk.CTkFrame(container, width=320)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._right = right

        # Left side (form) — занимает всё оставшееся
        left = ctk.CTkFrame(container)
        left.pack(side="left", expand=True, fill="both")
        # Резиновая сетка: списки тянут высоту
        try:
            left.grid_rowconfigure(0, weight=0)  # header
            left.grid_rowconfigure(1, weight=1)  # top panel (products + workers)
            left.grid_rowconfigure(2, weight=1)  # job types list (expand)
            left.grid_rowconfigure(3, weight=0)  # totals + actions (bottom, sticky south)
            left.grid_columnconfigure(0, weight=1)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Первичная установка ширины правой панели и пересчет при ресайзе
        def _set_initial_width() -> None:
            self._enforce_right_width_limit(adjust_to_content=True)

        self.after(200, _set_initial_width)

        def _on_resize(_evt=None):
            self._enforce_right_width_limit(adjust_to_content=False)

        self.bind("<Configure>", _on_resize, add="+")

        # Header form (Номер, Дата)
        header = ctk.CTkFrame(left)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        for i in range(6):
            header.grid_columnconfigure(i, weight=0)

        # Order No (авто подставляется, можно менять)
        ctk.CTkLabel(header, text="№ наряда").grid(row=0, column=0, sticky="w", padx=5)
        # Оставляем пустым — при сохранении подставится автоматически, если не задан
        self.order_no_var = ctk.StringVar(value="")
        self.order_no_entry = ctk.CTkEntry(
            header, textvariable=self.order_no_var, width=100
        )
        self.order_no_entry.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 6))
        # Подставим следующий свободный номер сразу
        try:
            with get_connection() as conn:
                self.order_no_var.set(str(q.next_order_no(conn)))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Date
        self.date_var = ctk.StringVar(
            value=dt.date.today().strftime(CONFIG.date_format)
        )
        ctk.CTkLabel(header, text="Дата").grid(row=0, column=1, sticky="w", padx=5)
        self.date_entry = ctk.CTkEntry(header, textvariable=self.date_var, width=120)
        self.date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 6))
        self.date_entry.bind("<FocusIn>", lambda e: self._open_date_picker())

        # Новый layout: Изделия и Работники рядом по горизонтали, Виды работ под ними
        
        # Верхняя панель: Изделия и Работники
        top_panel = create_modern_frame(left, style_type="frame")
        top_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        top_panel.grid_columnconfigure(0, weight=1)  # Изделия
        top_panel.grid_columnconfigure(1, weight=1)  # Работники
        top_panel.grid_rowconfigure(0, weight=1)
        
        # Изделия (левая колонка)
        self.products_widget = create_products_list(
            top_panel,
            readonly=self._readonly,
            on_item_add=self._on_product_add,
            on_item_remove=self._on_product_remove
        )
        self.products_widget.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Работники (правая колонка)
        self.workers_widget = create_workers_list(
            top_panel,
            readonly=self._readonly,
            on_item_add=self._on_worker_add,
            on_item_remove=self._on_worker_remove,
            on_amount_change=self._on_worker_amount_change
        )
        self.workers_widget.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Contract (заполняется автоматически по изделию, недоступно для редактирования)
        ctk.CTkLabel(header, text="Контракт").grid(row=0, column=4, sticky="w", padx=5)
        self.contract_entry = ctk.CTkEntry(header, placeholder_text="Авто")
        self.contract_entry.grid(row=1, column=4, sticky="ew", padx=5, pady=(0, 6))
        try:
            self.contract_entry.configure(state="disabled")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Suggestion frames (один общий для контрактов, один общий для изделий)
        self.suggest_contract_frame = create_suggestions_frame(self)
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame = create_suggestions_frame(self)
        self.suggest_product_frame.place_forget()

        # Убраны дополнительные изделия (одно изделие)

        # Рамка подсказок для видов работ (общая)
        self.suggest_job_frame = create_suggestions_frame(self)
        self.suggest_job_frame.place_forget()

        # Виды работ (под верхней панелью)
        self.job_types_widget = create_job_types_list(
            left,
            readonly=self._readonly,
            on_item_add=self._on_job_type_add,
            on_item_remove=self._on_job_type_remove,
            on_amount_change=self._on_job_type_quantity_change
        )
        self.job_types_widget.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 6))
        
        # Старый список видов работ удален - теперь используется новый виджет выше

        # Старый список работников удален - теперь используется новый виджет рядом с изделиями

        # Totals and Save
        totals_frame = ctk.CTkFrame(left)
        totals_frame.grid(row=3, column=0, sticky="sew", padx=10, pady=(6, 8))
        for i in range(4):
            totals_frame.grid_columnconfigure(i, weight=1 if i == 0 else 0)

        self.total_var = ctk.StringVar(value="0.00")
        self.per_worker_var = ctk.StringVar(value="0.00")

        # Итоги — верхняя строка
        totals_row = ctk.CTkFrame(totals_frame)
        totals_row.grid(row=0, column=0, columnspan=4, sticky="ew")
        ctk.CTkLabel(totals_row, text="Итог, руб:").pack(side="left", padx=5)
        ctk.CTkLabel(totals_row, textvariable=self.total_var).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkLabel(totals_row, text="На одного, руб:").pack(side="left", padx=5)
        ctk.CTkLabel(totals_row, textvariable=self.per_worker_var).pack(side="left")

        # Кнопки — ниже итогов
        actions = ctk.CTkFrame(totals_frame)
        actions.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=(6, 0))
        self.save_btn = ctk.CTkButton(actions, text="Сохранить", command=self._save)
        self.save_btn.pack(side="left", padx=4)
        self.delete_btn = ctk.CTkButton(
            actions,
            text="Удалить",
            command=self._delete,
            fg_color="#b91c1c",
            hover_color="#7f1d1d",
        )
        self.delete_btn.pack(side="left", padx=4)
        self.cancel_btn = ctk.CTkButton(
            actions, text="Отмена", command=self._cancel_edit, fg_color="#6b7280"
        )
        self.cancel_btn.pack(side="left", padx=4)
        self.edit_btn = ctk.CTkButton(
            actions, text="Изменить", command=self._enable_editing
        )
        self.edit_btn.pack(side="left", padx=4)
        # Убран переключатель ручного ввода сумм — логика авто/ручного ниже

        if self._readonly:
            # Заблокировать ввод и действия редактирования
            for w in (self.date_entry, self.contract_entry, self.product_entry):
                try:
                    w.configure(state="disabled")
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
            # Кнопка "Изменить" всегда доступна в режиме просмотра
            for b in (self.save_btn, self.delete_btn):
                b.configure(state="disabled")
            try:
                self.edit_btn.configure(state="normal")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            # Кнопка Отмена всегда активна
            try:
                self.cancel_btn.configure(state="normal")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

        # Right-side: existing orders list
        ctk.CTkLabel(right, text="Список нарядов").pack(
            padx=10, pady=(10, 0), anchor="w"
        )
        filter_frame = ctk.CTkFrame(right)
        filter_frame.pack(fill="x", padx=10, pady=5)
        self.filter_from = ctk.StringVar()
        self.filter_to = ctk.StringVar()
        ctk.CTkLabel(filter_frame, text="с").pack(side="left", padx=2)
        self.filter_from_entry = ctk.CTkEntry(
            filter_frame, textvariable=self.filter_from, width=100
        )
        self.filter_from_entry.pack(side="left")
        self.filter_from_entry.bind(
            "<FocusIn>",
            lambda e: self._open_date_picker_for(
                self.filter_from, self.filter_from_entry
            ),
        )

        ctk.CTkLabel(filter_frame, text="по").pack(side="left", padx=2)
        self.filter_to_entry = ctk.CTkEntry(
            filter_frame, textvariable=self.filter_to, width=100
        )
        self.filter_to_entry.pack(side="left")
        self.filter_to_entry.bind(
            "<FocusIn>",
            lambda e: self._open_date_picker_for(self.filter_to, self.filter_to_entry),
        )
        ctk.CTkButton(
            filter_frame, text="Фильтр", width=80, command=self._apply_filter
        ).pack(side="left", padx=6)

        list_frame = ctk.CTkFrame(right)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.orders_tree = ttk.Treeview(
            list_frame,
            columns=("no", "date", "contract", "product", "total"),
            show="headings",
        )
        self.orders_tree.heading("no", text="№")
        self.orders_tree.heading("date", text="Дата")
        self.orders_tree.heading("contract", text="Контракт")
        self.orders_tree.heading("product", text="Изделие")
        self.orders_tree.heading("total", text="Сумма")
        # Фиксированные столбцы не тянутся, "Изделие" тянется на остаток
        self.orders_tree.column("no", width=60, anchor="center", stretch=False)
        self.orders_tree.column("date", width=100, anchor="center", stretch=False)
        self.orders_tree.column("contract", width=140, stretch=False)
        self.orders_tree.column("product", width=200, stretch=True)
        self.orders_tree.column("total", width=110, anchor="e", stretch=False)
        vsb = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.orders_tree.yview
        )
        hsb = ttk.Scrollbar(
            list_frame, orient="horizontal", command=self.orders_tree.xview
        )
        self._orders_vsb = vsb
        self.orders_tree.configure(
            yscrollcommand=self._on_orders_scroll, xscrollcommand=hsb.set
        )
        self.orders_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)
        # Заголовки кликабельны для сортировки
        for col, title in (
            ("no", "№"),
            ("date", "Дата"),
            ("contract", "Контракт"),
            ("product", "Изделие"),
            ("total", "Сумма"),
        ):
            self.orders_tree.heading(
                col, text=title, command=lambda c=col: self._sort_orders_by(c)
            )

    # --- enforce right panel width and autosize columns ---
    def _autosize_orders_columns(self) -> None:
        try:
            font = tkfont.nametofont("TkDefaultFont")
        except Exception:
            font = tkfont.Font()
        pad = 24
        min_widths = {"no": 50, "date": 90, "contract": 80, "product": 120, "total": 90}
        # 1) посчитать целевые ширины для фиксированных столбцов по содержимому
        fixed_cols = ("no", "date", "contract", "total")
        widths: dict[str, int] = {}
        for col in fixed_cols:
            header = self.orders_tree.heading(col).get("text", "")
            max_w = font.measure(str(header))
            for iid in self.orders_tree.get_children(""):
                text = str(self.orders_tree.set(iid, col))
                w = font.measure(text)
                if w > max_w:
                    max_w = w
            widths[col] = max(max_w + pad, min_widths.get(col, 60))
        # 2) применить фиксированные
        for col in fixed_cols:
            self.orders_tree.column(col, width=widths[col])
        # 3) вычислить ширину для гибкого столбца "product" как остаток
        try:
            tree_w = int(self.orders_tree.winfo_width() or 0)
            if tree_w <= 1:
                # отложить, если дерево еще не измерено
                self.after(50, self._autosize_orders_columns)
                return
        except Exception:
            tree_w = sum(widths.values()) + 200
        other = sum(widths.values())
        # учесть вертикальный скроллбар и небольшой запас
        scrollbar_w = 18
        leftover = tree_w - other - scrollbar_w
        product_w = max(min_widths.get("product", 120), leftover)
        self.orders_tree.column("product", width=product_w)

    def _get_orders_content_width(self) -> int:
        total = 0
        try:
            for col in self.orders_tree["columns"]:
                total += int(self.orders_tree.column(col, "width") or 0)
            # учесть вертикальный скроллбар и внутренние отступы
            total += 20 + 16
        except Exception:
            total = 360
        return total

    def _enforce_right_width_limit(self, adjust_to_content: bool) -> None:
        try:
            total = self.winfo_width()
            if not total or total <= 1:
                self.after(
                    120, lambda: self._enforce_right_width_limit(adjust_to_content)
                )
                return
            max_right = int(total * 0.40)
            desired = max_right
            if adjust_to_content:
                desired = min(max_right, self._get_orders_content_width())
            # Минимальная ширина справа, чтобы элементы управления не ломались
            min_right = 260
            desired = max(min_right, desired)
            # Применить ширину к правой панели
            try:
                self._right.configure(width=desired)
                self._right.pack_propagate(False)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    # --- Truncate job name column with ellipsis and keep numeric columns visible ---
    # Старый метод _update_items_columns_widths удален - используется новый виджет видов работ
            # update header width for name - removed old code

            # font for measuring
            try:
                fnt = tkfont.nametofont("TkDefaultFont")
            except Exception:
                fnt = tkfont.Font()

            target = max(60, name_w - 12)
            for item in list(self._item_row_widgets):
                try:
                    # item may be (label, container)
                    lbl = item[0] if isinstance(item, tuple) else item
                    # Получаем текст безопасным способом
                    try:
                        if hasattr(lbl, "get"):
                            current_text = lbl.get()
                        elif hasattr(lbl, "cget") and "text" in lbl.configure():
                            current_text = str(lbl.cget("text") or "")
                        else:
                            current_text = ""
                    except Exception:
                        current_text = ""

                    full = getattr(lbl, "_full_text", None) or current_text
                    setattr(lbl, "_full_text", full)
                    # already fits
                    if fnt.measure(full) <= target:
                        try:
                            if hasattr(lbl, "get"):
                                if lbl.get() != full:
                                    lbl.delete(0, "end")
                                    lbl.insert(0, full)
                            elif (
                                hasattr(lbl, "configure") and "text" in lbl.configure()
                            ):
                                try:
                                    if str(lbl.cget("text")) != full:
                                        lbl.configure(text=full)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        continue
                    # binary search shrink with ellipsis
                    ell = "…"
                    lo, hi = 0, len(full)
                    res = ell
                    while lo <= hi:
                        mid = (lo + hi) // 2
                        cand = full[:mid] + ell
                        if fnt.measure(cand) <= target:
                            res = cand
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    lbl.configure(text=res)
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _enforce_right_width_limit(self, adjust_to_content: bool) -> None:
        # Метод упрощен - правая панель больше не используется для списка нарядов
        pass

    # --- suggest helpers ---
    def _hide_all_suggests(self) -> None:
        for frame in (
            self.suggest_contract_frame,
            self.suggest_product_frame,
            self.suggest_job_frame,
            self.suggest_worker_frame,
        ):
            frame.place_forget()

    def _find_job_entry_row(self, widget) -> tuple[ctk.CTkEntry | None, int | None]:
        """Find job-entry and its row index by walking up from clicked widget.

        Returns (entry, row_index) or (None, None).
        """
        try:
            # Build mapping entry->row_idx
            entries: list[ctk.CTkEntry] = []
            for idx, wmap in enumerate(self._item_widgets):
                ent = wmap.get("name")
                if ent is not None:
                    entries.append(ent)
            # Walk up masters from clicked widget and test membership
            w = widget
            while w is not None:
                for idx, ent in enumerate(entries):
                    if w == ent:
                        return ent, idx
                w = getattr(w, "master", None)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        return None, None

    def _place_suggest_under(self, entry: ctk.CTkEntry, frame: ctk.CTkFrame) -> None:
        place_suggestions_under_entry(entry, frame, self)

    def _on_contract_key_for(self, entry: ctk.CTkEntry) -> None:
        self._hide_all_suggests()
        for w in self.suggest_contract_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        place_suggestions_under_entry(entry, self.suggest_contract_frame, self)
        text = entry.get().strip()
        with get_connection() as conn:
            rows = suggestions.suggest_contracts(conn, text, CONFIG.autocomplete_limit)
        shown = 0
        for _id, label in rows:
            create_suggestion_button(
                self.suggest_contract_frame,
                text=label,
                command=lambda i=_id, l=label, e=entry: self._pick_contract_for(
                    i, l, e
                ),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        for label in get_recent(
            "work_orders.contract", text, CONFIG.autocomplete_limit
        ):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(
                    self.suggest_contract_frame,
                    text=label,
                    command=lambda l=label, e=entry: self._pick_contract_for(
                        self.selected_contract_id or 0, l, e
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        if shown == 0:
            with get_connection() as conn:
                all_contracts = suggestions.suggest_contracts(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_contracts:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_contract_frame,
                    text=label,
                    command=lambda i=_id, l=label, e=entry: self._pick_contract_for(
                        i, l, e
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_contract_for(
        self, contract_id: int, label: str, entry: ctk.CTkEntry
    ) -> None:
        try:
            entry.delete(0, "end")
            entry.insert(0, label)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        record_use("work_orders.contract", label)
        self.suggest_contract_frame.place_forget()

    def _on_product_key_for(self, entry: ctk.CTkEntry) -> None:
        self._hide_all_suggests()
        for w in self.suggest_product_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        place_suggestions_under_entry(entry, self.suggest_product_frame, self)
        text = entry.get().strip()
        with get_connection() as conn:
            rows = suggestions.suggest_products(conn, text, CONFIG.autocomplete_limit)
        shown = 0
        for _id, label in rows:
            create_suggestion_button(
                self.suggest_product_frame,
                text=label,
                command=lambda i=_id, l=label, e=entry: self._pick_product_for(i, l, e),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        for label in get_recent("work_orders.product", text, CONFIG.autocomplete_limit):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(
                    self.suggest_product_frame,
                    text=label,
                    command=lambda l=label, e=entry: self._pick_product_for(
                        self.selected_product_id or 0, l, e
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        if shown == 0:
            with get_connection() as conn:
                all_products = suggestions.suggest_products(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_products:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_product_frame,
                    text=label,
                    command=lambda i=_id, l=label, e=entry: self._pick_product_for(
                        i, l, e
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_product_for(
        self, product_id: int, label: str, entry: ctk.CTkEntry
    ) -> None:
        try:
            entry.delete(0, "end")
            entry.insert(0, label)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Установим выбранное изделие
        self.selected_product_id = product_id
        record_use("work_orders.product", label)
        # Автоподстановка контракта по изделию
        try:
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT c.id AS cid, c.code AS code FROM products p LEFT JOIN contracts c ON c.id = p.contract_id WHERE p.id=?",
                    (product_id,),
                ).fetchone()
                code = None
                cid = None
                if row:
                    try:
                        cid = int(row["cid"]) if row["cid"] is not None else None
                        code = row["code"]
                    except Exception:
                        cid = int(row[0]) if row[0] is not None else None
                        code = row[1] if len(row) > 1 else None
                # Если у изделия нет контракта — привяжем к "Без контракта"
                if cid is None:
                    try:
                        cid = q.get_or_create_default_contract(conn)
                        q.set_product_contract(conn, int(product_id), int(cid))
                        code = conn.execute(
                            "SELECT code FROM contracts WHERE id=?", (cid,)
                        ).fetchone()[0]
                    except Exception as exc:
                        logging.getLogger(__name__).exception(
                            "Ignored unexpected error: %s", exc
                        )
                self.selected_contract_id = cid
                try:
                    self.contract_entry.configure(state="normal")
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
                try:
                    self.contract_entry.delete(0, "end")
                    if code:
                        self.contract_entry.insert(0, str(code))
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
                try:
                    self.contract_entry.configure(state="disabled")
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
        except Exception:
            try:
                self.contract_entry.configure(state="disabled")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        self.suggest_product_frame.place_forget()

    # Убраны добавления дополнительных контрактов (разрешён только один)

    # Убраны добавления дополнительных изделий (только одно изделие)

    def _on_job_key(self, _evt=None) -> None:
        self._hide_all_suggests()
        for w in self.suggest_job_frame.winfo_children():
            w.destroy()
        
        place_suggestions_under_entry(self.job_entry, self.suggest_job_frame, self)
        
        with get_connection() as conn:
            rows = suggestions.suggest_job_types(
                conn, self.job_entry.get().strip(), CONFIG.autocomplete_limit
            )
        
        shown = 0
        for _id, label in rows:
            create_suggestion_button(
                self.suggest_job_frame,
                text=label,
                command=lambda i=_id, l=label: self._pick_job(i, l),
            ).pack(fill="x", padx=2, pady=1)
            shown += 1
        
        for label in get_recent(
            "work_orders.job_type",
            self.job_entry.get().strip(),
            CONFIG.autocomplete_limit,
        ):
            if label not in [lbl for _, lbl in rows]:
                create_suggestion_button(
                    self.suggest_job_frame,
                    text=label,
                    command=lambda l=label: self._pick_job(
                        getattr(self.job_entry, "_selected_job_id", 0) or 0, l
                    ),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1
        
        # Если нет данных из БД и истории, показываем все виды работ
        if shown == 0:
            with get_connection() as conn:
                all_job_types = suggestions.suggest_job_types(
                    conn, "", CONFIG.autocomplete_limit
                )
            for _id, label in all_job_types:
                if shown >= CONFIG.autocomplete_limit:
                    break
                create_suggestion_button(
                    self.suggest_job_frame,
                    text=label,
                    command=lambda i=_id, l=label: self._pick_job(i, l),
                ).pack(fill="x", padx=2, pady=1)
                shown += 1

    def _pick_job(self, job_type_id: int, label: str) -> None:
        self.job_entry.delete(0, "end")
        self.job_entry.insert(0, label)
        self.job_entry._selected_job_id = job_type_id
        record_use("work_orders.job_type", label)
        self.suggest_job_frame.place_forget()

    def _pick_product(self, product_id: int, label: str) -> None:
        # Проверяем, не добавлено ли уже
        if product_id in self.selected_product_ids:
            messagebox.showwarning("Предупреждение", f"Изделие '{label}' уже добавлено")
            return

        # Добавляем изделие
        self.selected_product_ids.append(product_id)
        # Старый метод _refresh_products_display удален
        self._update_contract_from_products()

        # Очищаем поле ввода
        self.product_entry.delete(0, "end")
        self.suggest_product_frame.place_forget()

    def _on_worker_key(self, _evt=None) -> None:
        # legacy entry-based suggestions removed
        return

    def _pick_worker(self, worker_id: int, label: str) -> None:
        # legacy entry-based selection removed
        return

    def _add_worker_from_entry(self) -> None:
        # Add an empty editable worker row
        self._manual_worker_counter -= 1
        manual_worker_id = self._manual_worker_counter
        self.selected_workers[manual_worker_id] = ""
        # Старый метод _refresh_workers_display удален
        self._update_totals()

    def _on_global_click(self, event=None) -> None:
        widget = getattr(event, "widget", None)
        if widget is None:
            self._hide_all_suggests()
            return
        # Если клик внутри поля "Вид работ" — откроем подсказки по месту клика и не будем их скрывать
        ent, row_idx = self._find_job_entry_row(widget)
        if ent is not None and row_idx is not None:
            try:
                self._on_job_key_edit(ent, row_idx)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            return
        for frame in (
            self.suggest_contract_frame,
            self.suggest_product_frame,
            self.suggest_job_frame,
            self.suggest_worker_frame,
        ):
            w = widget
            while w is not None:
                if w == frame:
                    return
                w = getattr(w, "master", None)
        self._hide_all_suggests()

    # ---- Items and Workers manipulation ----
    # Старый метод _add_item удален - используется новый виджет видов работ
    def _placeholder_method(self) -> None:
        job_type_id = getattr(self.job_entry, "_selected_job_id", None)
        if not job_type_id:
            messagebox.showwarning("Проверка", "Выберите вид работ из подсказки")
            return
        try:
            qty = float(self.qty_var.get().strip() or "0")
        except Exception:
            messagebox.showwarning("Проверка", "Количество должно быть числом")
            return
        if qty <= 0:
            messagebox.showwarning("Проверка", "Количество должно быть > 0")
            return

        with get_connection() as conn:
            row = conn.execute(
                "SELECT name, price FROM job_types WHERE id = ?", (job_type_id,)
            ).fetchone()
            if not row:
                messagebox.showerror("Ошибка", "Вид работ не найден")
                return
            name = row["name"]
            unit_price = float(row["price"]) if row["price"] is not None else 0.0

        amount = float(Decimal(str(unit_price)) * Decimal(str(qty)))
        item = ItemRow(
            job_type_id=job_type_id,
            job_type_name=name,
            quantity=qty,
            unit_price=unit_price,
            line_amount=amount,
        )
        self.item_rows.append(item)
        # UI row
        # Создаем строку в общей сетке
        row_index = len(self._item_widgets)
        # Редактируемая строка: Вид работ (Entry с подсказками), Кол-во (Entry), Цена (Label), Сумма (Label), + и Удалить
        name_var = ctk.StringVar(value=name)
        name_entry = ctk.CTkEntry(self.items_table, textvariable=name_var)
        name_entry.grid(row=row_index, column=0, sticky="ew", padx=4, pady=2)
        name_entry.bind(
            "<KeyRelease>",
            lambda _e=None, ent=name_entry, i=row_index: self._on_job_key_edit(ent, i),
        )
        name_entry.bind(
            "<FocusIn>",
            lambda _e=None, ent=name_entry, i=row_index: self._on_job_key_edit(ent, i),
        )
        # При клике фокус уже у виджета — откроем подсказки в том же тикe
        name_entry.bind(
            "<Button-1>",
            lambda e, ent=name_entry, i=row_index: self._on_job_click_show(e, ent, i),
        )

        qty_var = ctk.StringVar(value=str(qty))
        qty_entry = ctk.CTkEntry(
            self.items_table, textvariable=qty_var, width=self._col_qty_w
        )
        qty_entry.grid(row=row_index, column=1, sticky="e", padx=4, pady=2)
        qty_entry.bind(
            "<KeyRelease>",
            lambda _e=None, i=row_index, v=qty_var: self._on_qty_change(i, v),
        )

        price_label = ctk.CTkLabel(
            self.items_table, text=f"{unit_price:.2f}", anchor="e"
        )
        price_label.grid(row=row_index, column=2, sticky="e", padx=4, pady=2)
        amount_label = ctk.CTkLabel(self.items_table, text=f"{amount:.2f}", anchor="e")
        amount_label.grid(row=row_index, column=3, sticky="e", padx=4, pady=2)

        add_btn_row = ctk.CTkButton(
            self.items_table, text="+", width=28, command=self._add_blank_item_row
        )
        add_btn_row.grid(row=row_index, column=4, sticky="e", padx=2, pady=2)
        del_btn = ctk.CTkButton(
            self.items_table,
            text="Удалить",
            width=self._col_delete_w - self._col_pad_px,
            fg_color="#b91c1c",
            hover_color="#7f1d1d",
        )
        del_btn.grid(row=row_index, column=5, sticky="e", padx=4, pady=2)
        self._item_row_widgets.append(name_entry)
        idx = len(self.item_rows) - 1
        del_btn.configure(command=lambda i=idx: self._remove_item_row(i))

        self.job_entry.delete(0, "end")
        if hasattr(self.job_entry, "_selected_job_id"):
            delattr(self.job_entry, "_selected_job_id")
        # qty_var больше не используется (построчное редактирование)

        self._update_totals()
        # Обновим обрезку текста
        self._update_items_columns_widths()

    def _remove_item_row(self, idx: int, row_frame: ctk.CTkFrame | None = None) -> None:
        if 0 <= idx < len(self.item_rows):
            self.item_rows.pop(idx)
        # Удалить виджеты из табличного контейнера и сдвинуть остальные вверх
        try:
            row_widgets = self._item_widgets[idx]
        except Exception:
            row_widgets = None
        if row_widgets:
            for key in ("name", "qty", "price", "amount", "btn"):
                try:
                    row_widgets[key].grid_forget()
                    row_widgets[key].destroy()
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
            try:
                self._item_widgets.pop(idx)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        # Переназначить grid-позиции и команды кнопок
        for new_idx, wmap in enumerate(self._item_widgets):
            try:
                wmap["name"].grid_configure(row=new_idx)
                wmap["qty"].grid_configure(row=new_idx)
                wmap["price"].grid_configure(row=new_idx)
                wmap["amount"].grid_configure(row=new_idx)
                wmap["btn_add"].grid_configure(row=new_idx)
                wmap["btn_del"].grid_configure(row=new_idx)
                wmap["btn_del"].configure(
                    command=lambda i=new_idx: self._remove_item_row(i)
                )
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        self._update_totals()
        self._update_items_columns_widths()

    def _clear_items(self) -> None:
        # Очистить табличный контейнер
        try:
            for child in self.items_table.winfo_children():
                child.destroy()
            self._item_widgets.clear()
            self._item_row_widgets.clear()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self.item_rows.clear()
        self._update_totals()

    # Старый метод _add_blank_item_row удален - используется новый виджет видов работ
    def _on_job_key_edit(self, entry: ctk.CTkEntry, idx: int) -> None:
        # Подсказки по виду работ, выбор обновляет job_type_id, price, amount
        self._hide_all_suggests()
        for w in self.suggest_job_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        place_suggestions_under_entry(entry, self.suggest_job_frame, self)
        text = (entry.get() or "").strip()
        with get_connection() as conn:
            rows = suggestions.suggest_job_types(conn, text, CONFIG.autocomplete_limit)
        # Если пустой ввод — дополнительно показать недавние из истории
        if not text:
            extras: list[tuple[int, str]] = []
            for label in get_recent(
                "work_orders.job_type", "", CONFIG.autocomplete_limit
            ):
                try:
                    with get_connection() as conn:
                        r = conn.execute(
                            "SELECT id FROM job_types WHERE name_norm = ?",
                            (label.casefold(),),
                        ).fetchone()
                        if r:
                            jt_id = int(r["id"] if isinstance(r, dict) else r[0])
                            extras.append((jt_id, label))
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
            # добавим, избегая дублей по id
            seen = {rid for rid, _ in rows}
            rows.extend((rid, lbl) for rid, lbl in extras if rid not in seen)
        for jt_id, label in rows:
            create_suggestion_button(
                self.suggest_job_frame,
                text=label,
                command=lambda i=jt_id, l=label, row=idx: self._pick_job_for_row(
                    row, i, l
                ),
            ).pack(fill="x", padx=2, pady=1)

    def _on_job_click_show(self, event, entry: ctk.CTkEntry, idx: int):
        # Показ подсказок по клику и остановка всплытия события, чтобы глобальный клик не спрятал подсказки
        try:
            self._on_job_key_edit(entry, idx)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        return "break"

    def _pick_job_for_row(self, row_idx: int, job_type_id: int, label: str) -> None:
        # Установить вид работ и цену из БД, пересчитать сумму
        if not (0 <= row_idx < len(self.item_rows)):
            return
        self.item_rows[row_idx].job_type_id = job_type_id
        self.item_rows[row_idx].job_type_name = label
        # Найти виджеты строки
        w = self._item_widgets[row_idx]
        try:
            w["name_var"].set(label)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        with get_connection() as conn:
            row = conn.execute(
                "SELECT price FROM job_types WHERE id=?", (job_type_id,)
            ).fetchone()
        price = float(row["price"]) if row and row["price"] is not None else 0.0
        self.item_rows[row_idx].unit_price = price
        qty = 0.0
        try:
            qty = float((w["qty_var"].get() or "0").replace(",", "."))
        except Exception:
            qty = 0.0
        amount = float(Decimal(str(price)) * Decimal(str(qty)))
        self.item_rows[row_idx].line_amount = amount
        try:
            w["price"].configure(text=f"{price:.2f}")
            w["amount"].configure(text=f"{amount:.2f}")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self._update_totals()

    def _on_qty_change(self, row_idx: int, qty_var: ctk.StringVar) -> None:
        if not (0 <= row_idx < len(self.item_rows)):
            return
        raw = (qty_var.get() or "0").replace(",", ".")
        try:
            qty = float(raw)
        except Exception:
            qty = 0.0
        if qty < 0:
            qty = 0.0
        self.item_rows[row_idx].quantity = qty
        price = float(self.item_rows[row_idx].unit_price or 0.0)
        amount = float(Decimal(str(price)) * Decimal(str(qty)))
        self.item_rows[row_idx].line_amount = amount
        w = self._item_widgets[row_idx]
        try:
            w["amount"].configure(text=f"{amount:.2f}")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self._update_totals()

    def _add_worker(
        self, worker_id: Optional[int] = None, label: Optional[str] = None
    ) -> None:
        if worker_id is None:
            return
        
        # Проверяем корректность ID
        if not isinstance(worker_id, int):
            logger.warning("Попытка добавить некорректный ID работника: %s", worker_id)
            return
        
        # Проверяем, не добавлен ли уже этот работник
        if worker_id in self.selected_workers:
            logger.info("Работник %s уже добавлен в бригаду", worker_id)
            return
        
        # Добавляем работника
        self.selected_workers[worker_id] = label or f"Работник {worker_id}"
        
        # Обновляем отображение списка работников
        # Старый метод _refresh_workers_display удален
        self._update_totals()
    
    # Старый метод _refresh_workers_display удален - используется новый виджет работников

    def _remove_worker(self, worker_id: int) -> None:
        if worker_id in self.selected_workers:
            del self.selected_workers[worker_id]
            if worker_id in self.worker_amounts:
                del self.worker_amounts[worker_id]
            if worker_id in self._manual_amount_ids:
                self._manual_amount_ids.discard(worker_id)
            # Старый метод _refresh_workers_display удален
            self._update_totals()

    def _update_totals(self) -> None:
        total = sum(i.line_amount for i in self.item_rows)
        num_workers = max(1, len(self.selected_workers))
        per_worker = total / num_workers if num_workers else 0.0
        self.total_var.set(f"{total:.2f}")
        self.per_worker_var.set(f"{per_worker:.2f}")
        # Обновляем распределение по работникам
        self._recalculate_worker_amounts()
        self._update_worker_amount_entries()

    def _update_worker_amount_entries(self) -> None:
        for wid, var in self._worker_amount_vars.items():
            try:
                var.set(f"{float(self.worker_amounts.get(wid, 0.0)):.2f}")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

    def _on_worker_amount_change(self, worker_id: int) -> None:
        var = self._worker_amount_vars.get(worker_id)
        if not var:
            return
        if self._readonly:
            return
        raw = (var.get() or "").strip().replace(",", ".")
        try:
            entered = round(float(raw), 2)
        except Exception:
            return
        if entered < 0:
            entered = 0.0
        # Фиксируем ручное значение; перераспределения в ручном режиме не выполняем
        self._manual_amount_ids.add(worker_id)
        self.worker_amounts[worker_id] = float(entered)
        self._update_worker_amount_entries()

    def _recalculate_worker_amounts(self) -> None:
        """Распределение: если есть ручные суммы — оставляем их, остальное поровну; если все нули — поровну всем."""
        ids = list(self.selected_workers.keys())
        if not ids:
            return
        total = round(sum(i.line_amount for i in self.item_rows), 2)
        manual = {
            wid: self.worker_amounts.get(wid, 0.0)
            for wid in ids
            if wid in self._manual_amount_ids
            and self.worker_amounts.get(wid, 0.0) > 0.0
        }
        unspecified = [wid for wid in ids if wid not in manual]
        remaining = max(0.0, total - sum(manual.values()))
        if unspecified:
            per = round(remaining / len(unspecified), 2)
            amounts = [per] * len(unspecified)
            diff = round(remaining - round(per * len(unspecified), 2), 2)
            if amounts and abs(diff) >= 0.01:
                amounts[-1] = round(amounts[-1] + diff, 2)
            for wid, amt in zip(unspecified, amounts):
                self.worker_amounts[wid] = float(amt)
        for wid, amt in manual.items():
            self.worker_amounts[wid] = float(amt)

    def _toggle_manual_mode(self) -> None:
        # Только если редактирование включено, разрешаем переключение режима
        if getattr(self, "_edit_locked", False):
            return
        self._manual_mode = not self._manual_mode
        try:
            self.manual_btn.configure(
                text=f"Ручной ввод сумм: {'ВКЛ' if self._manual_mode else 'ВЫКЛ'}"
            )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        if not self._manual_mode:
            # Выходим из ручного режима: очищаем ручные отметки и равномерно распределяем
            self._manual_amount_ids.clear()
            self._recalculate_worker_amounts()
            self._update_worker_amount_entries()
        # Перерисовать строки работников с актуальной доступностью полей
        # Старый метод _refresh_workers_display удален

    def _set_edit_locked(self, locked: bool) -> None:
        """Включает/выключает режим просмотра (блокирует поля формы)."""
        self._edit_locked = locked
        # В текущей версии нет отдельных job_entry/qty_entry (редактирование построчное)
        widgets = [self.date_entry, self.product_entry]
        for w in widgets:
            try:
                w.configure(state=("disabled" if locked else "normal"))
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        # Контракт всегда недоступен для ручного ввода
        try:
            self.contract_entry.configure(state="disabled")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Кнопки: в режиме просмотра активна только "Изменить"; в режиме редактирования — "Сохранить" и "Удалить"
        try:
            self.save_btn.configure(state=("disabled" if locked else "normal"))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.delete_btn.configure(state=("disabled" if locked else "normal"))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.edit_btn.configure(state=("normal" if locked else "disabled"))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Кнопка Отмена всегда активна
        try:
            self.cancel_btn.configure(state="normal")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Перерисовать работников (включит/выключит поля сумм)
        # Старый метод _refresh_workers_display удален

    def _enable_editing(self) -> None:
        # При включении редактирования не менять суммы автоматически: остаемся в ручном режиме
        self._set_edit_locked(False)

    def _open_date_picker(self) -> None:
        self._hide_all_suggests()
        open_for_anchor(
            self,
            self.date_entry,
            self.date_var.get().strip(),
            lambda d: self.date_var.set(d),
        )

    def _open_date_picker_for(self, var, anchor=None) -> None:
        self._hide_all_suggests()
        if anchor is None:
            return
        open_for_anchor(self, anchor, var.get().strip(), lambda d: var.set(d))

    # ---- Orders list ----
    def _load_recent_orders(self) -> None:
        # Сбросить и загрузить первую страницу
        self._reset_orders_list()
        self._load_more_orders()

    def _reset_orders_list(self) -> None:
        for iid in getattr(self, "_order_rows", []):
            try:
                self.orders_tree.delete(iid)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        self._order_rows = []
        self._orders_offset = 0
        self._orders_can_load_more = True
        self._orders_loading = False

    def _fetch_orders_page(self, limit: int, offset: int) -> list:
        date_from = (
            (self.filter_from.get().strip() or None)
            if hasattr(self, "filter_from")
            else None
        )
        date_to = (
            (self.filter_to.get().strip() or None)
            if hasattr(self, "filter_to")
            else None
        )
        where = []
        params: list = []
        if date_from:
            where.append("wo.date >= ?")
            params.append(date_from)
        if date_to:
            where.append("wo.date <= ?")
            params.append(date_to)
        sql = (
            "SELECT wo.id, wo.order_no, wo.date, c.code AS contract_code, GROUP_CONCAT(p.name, ', ') AS product_name, wo.total_amount "
            "FROM work_orders wo "
            "LEFT JOIN contracts c ON c.id = wo.contract_id "
            "LEFT JOIN work_order_products wop ON wop.work_order_id = wo.id "
            "LEFT JOIN products p ON p.id = wop.product_id "
        )
        if where:
            sql += "WHERE " + " AND ".join(where) + " "
        sql += "GROUP BY wo.id, wo.order_no, wo.date, c.code, wo.total_amount "
        # По умолчанию сортируем по номеру наряда по убыванию
        sql += "ORDER BY wo.order_no DESC, wo.date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with get_connection() as conn:
            return conn.execute(sql, params).fetchall()

    def _load_more_orders(self) -> None:
        if self._orders_loading or not self._orders_can_load_more:
            return
        self._orders_loading = True
        try:
            rows = self._fetch_orders_page(self._orders_page_size, self._orders_offset)
            for r in rows:
                iid = str(r["id"])  # уникальный идентификатор строки
                if iid in self._order_rows:
                    continue
                self.orders_tree.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        r["order_no"],
                        r["date"],
                        r["contract_code"] or "",
                        r["product_name"] or "",
                        f"{r['total_amount']:.2f}",
                    ),
                )
                self._order_rows.append(iid)
            self._orders_offset += len(rows)
            if len(rows) < self._orders_page_size:
                self._orders_can_load_more = False
            self._autosize_orders_columns()
        finally:
            self._orders_loading = False

    def _on_orders_scroll(self, first: str, last: str) -> None:
        # Прокрутка: передать в реальный скроллбар
        try:
            if self._orders_vsb is not None:
                self._orders_vsb.set(first, last)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Динамическая подгрузка при достижении низа списка
        try:
            float(first)
            l = float(last)
            if l > 0.98:
                self.after(1, self._load_more_orders)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _apply_filter(self) -> None:
        # Применяем фильтр дат и перезагружаем первую страницу
        self._reset_orders_list()
        self._load_more_orders()

    def _sort_orders_by(self, col: str) -> None:
        # Текущее направление
        direction = getattr(self, "_orders_sort_dir", {}).get(col, "asc")
        new_dir = "desc" if direction == "asc" else "asc"
        # Собираем все элементы и сортируем локально
        rows = []
        for iid in self.orders_tree.get_children(""):
            vals = self.orders_tree.item(iid, "values")
            rows.append((iid, vals))
        index_map = {"no": 0, "date": 1, "contract": 2, "product": 3, "total": 4}
        idx = index_map[col]

        def key_func(item):
            vals = item[1]
            val = vals[idx]
            if col == "no":
                try:
                    return int(val)
                except Exception:
                    return 0
            if col == "total":
                try:
                    return float(val.replace(" ", "").replace(",", "."))
                except Exception:
                    return 0.0
            if col == "date":
                # ДД.ММ.ГГГГ -> ГГГГММДД для корректной сортировки строкой
                try:
                    d, m, y = val.split(".")
                    return f"{y}{m}{d}"
                except Exception:
                    return val
            return val.casefold() if isinstance(val, str) else val

        rows.sort(key=key_func, reverse=(new_dir == "desc"))
        # Переставляем элементы
        for pos, (iid, _vals) in enumerate(rows):
            self.orders_tree.move(iid, "", pos)
        # Сохраняем направление для колонки
        if not hasattr(self, "_orders_sort_dir"):
            self._orders_sort_dir = {}
        self._orders_sort_dir[col] = new_dir

    def _on_order_select(self, _evt=None) -> None:
        sel = self.orders_tree.selection()
        if not sel:
            return
        work_order_id = int(sel[0])
        try:
            from services.work_orders import load_work_order  # lazy import

            with get_connection() as conn:
                data = load_work_order(conn, work_order_id)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось загрузить наряд: {exc}")
            return
        self._fill_form_from_loaded(data)

    def _fill_form_from_loaded(self, data) -> None:
        self.editing_order_id = data.id
        self._loaded_snapshot = data
        # визуально показать режим редактирования
        try:
            self.save_btn.configure(text="Сохранить", fg_color="#2563eb")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self.date_var.set(data.date)
        # Показать номер наряда
        try:
            self.order_no_var.set(str(data.order_no))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Загружаем изделия и контракт
        with get_connection() as conn:
            # Загружаем изделия наряда
            products = q.get_work_order_products(conn, data.id)
            self.selected_product_ids = [p["id"] for p in products]
            
            # Заполняем новую структуру selected_products
            self.selected_products.clear()
            product_items = []
            for i, product in enumerate(products):
                # Используем положительные ID для реальных изделий
                product_id = product["id"]
                product_name = f"{product['product_no']} — {product['name']}"
                self.selected_products[product_id] = product_name
                product_items.append((product_id, product_name, {}))
            
            # Загружаем в новый виджет
            if hasattr(self, 'products_widget'):
                self.products_widget.set_items(product_items)
                
            # Старый метод _refresh_products_display удален

            # Загружаем контракт
            self.selected_contract_id = data.contract_id
            if data.contract_id:
                contract = q.get_contract(conn, data.contract_id)
                if contract:
                    self.contract_entry.delete(0, "end")
                    self.contract_entry.insert(
                        0, f"{contract['code']} — {contract['name']}"
                    )
            else:
                self.contract_entry.delete(0, "end")
        # items (редактируемые строки)
        self._clear_items()
        for job_type_id, name, qty, unit_price, line_amount in data.items:
            # модель
            self.item_rows.append(
                ItemRow(
                    job_type_id=job_type_id,
                    job_type_name=name,
                    quantity=qty,
                    unit_price=unit_price,
                    line_amount=line_amount,
                )
            )
            row_index = len(self._item_widgets)
            name_var = ctk.StringVar(value=name)
            name_entry = ctk.CTkEntry(self.items_table, textvariable=name_var)
            name_entry.grid(row=row_index, column=0, sticky="ew", padx=4, pady=2)
            cur_idx = len(self.item_rows) - 1
            name_entry.bind(
                "<KeyRelease>",
                lambda _e=None, ent=name_entry, i=cur_idx: self._on_job_key_edit(
                    ent, i
                ),
            )
            name_entry.bind(
                "<FocusIn>",
                lambda _e=None, ent=name_entry, i=cur_idx: self._on_job_key_edit(
                    ent, i
                ),
            )
            name_entry.bind(
                "<Button-1>",
                lambda e, ent=name_entry, i=cur_idx: self._on_job_click_show(e, ent, i),
            )
            qty_var = ctk.StringVar(value=str(qty))
            qty_entry = ctk.CTkEntry(
                self.items_table, textvariable=qty_var, width=self._col_qty_w
            )
            qty_entry.grid(row=row_index, column=1, sticky="e", padx=4, pady=2)
            qty_entry.bind(
                "<KeyRelease>",
                lambda _e=None, i=cur_idx, v=qty_var: self._on_qty_change(i, v),
            )
            price_label = ctk.CTkLabel(
                self.items_table, text=f"{unit_price:.2f}", anchor="e"
            )
            price_label.grid(row=row_index, column=2, sticky="e", padx=4, pady=2)
            amount_label = ctk.CTkLabel(
                self.items_table, text=f"{line_amount:.2f}", anchor="e"
            )
            amount_label.grid(row=row_index, column=3, sticky="e", padx=4, pady=2)
            add_btn_row = ctk.CTkButton(
                self.items_table, text="+", width=28, command=self._add_blank_item_row
            )
            add_btn_row.grid(row=row_index, column=4, sticky="e", padx=2, pady=2)
            del_btn = ctk.CTkButton(
                self.items_table,
                text="Удалить",
                width=self._col_delete_w - self._col_pad_px,
                fg_color="#b91c1c",
                hover_color="#7f1d1d",
                command=lambda i=cur_idx: self._remove_item_row(i),
            )
            del_btn.grid(row=row_index, column=5, sticky="e", padx=4, pady=2)
            self._item_row_widgets.append(name_entry)
            self._item_widgets.append(
                {
                    "name": name_entry,
                    "qty": qty_entry,
                    "price": price_label,
                    "amount": amount_label,
                    "btn_add": add_btn_row,
                    "btn_del": del_btn,
                    "name_var": name_var,
                    "qty_var": qty_var,
                }
            )
        # Загружаем данные в новый виджет видов работ
        if hasattr(self, 'job_types_widget'):
            job_items = []
            for job_type_id, name, qty, unit_price, line_amount in data.items:
                job_items.append((job_type_id, name, {
                    'quantity': qty,
                    'price': unit_price,
                    'total': line_amount
                }))
            self.job_types_widget.set_items(job_items)
        
        # workers — показываем в режиме просмотра, суммы не пересчитываем
        self.selected_workers.clear()
        self.worker_amounts.clear()
        with get_connection() as conn:
            for wid, amount in data.workers:
                r = conn.execute(
                    "SELECT full_name FROM workers WHERE id=?", (wid,)
                ).fetchone()
                self.selected_workers[wid] = r["full_name"] if r else str(wid)
                try:
                    self.worker_amounts[wid] = float(amount)
                except Exception:
                    self.worker_amounts[wid] = 0.0
        # Просмотр: фиксируем ручные значения, чтобы не пересчитывать
        self._manual_amount_ids = set(self.selected_workers.keys())
        self._set_edit_locked(True)
        # Старый метод _refresh_workers_display удален
        # Обновим числа (без перерасчета распределения)
        try:
            total = sum(i.line_amount for i in self.item_rows)
            self.total_var.set(f"{total:.2f}")
            num = max(1, len(self.selected_workers))
            self.per_worker_var.set(f"{(total/num if num else 0.0):.2f}")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    # ---- Save/Update/Delete ----
    def _build_input(self) -> Optional[WorkOrderInput]:
        # Получаем данные из нового виджета видов работ
        job_types_data = self.job_types_widget.get_items_data()
        # Фильтруем пустые элементы (с пустым именем)
        valid_job_types = [item for item in job_types_data if item['name'].strip()]
        if not valid_job_types:
            messagebox.showwarning("Проверка", "Добавьте хотя бы одну строку работ")
            return None
        # Проверка: должно быть выбрано хотя бы одно изделие
        if not self.selected_product_ids:
            messagebox.showwarning("Проверка", "Добавьте хотя бы одно изделие")
            return None
        date_str = self.date_var.get().strip()
        try:
            validate_date(date_str)
        except Exception as exc:
            messagebox.showwarning("Проверка", str(exc))
            return None
        # Номер наряда (необязателен; если указан — проверим число)
        order_no_val: int | None = None
        raw_no = (self.order_no_var.get() or "").strip()
        if raw_no:
            try:
                order_no_val = int(raw_no)
                if order_no_val <= 0:
                    raise ValueError
            except Exception:
                messagebox.showwarning(
                    "Проверка", "Номер наряда должен быть положительным числом"
                )
                return None
        # Изделие строго из БД — берём выбранный ID

        # Проверяем работников
        worker_ids = list(self.selected_workers.keys())
        if not worker_ids:
            messagebox.showwarning("Проверка", "Добавьте работников в бригаду")
            return None
        # Проверяем на дубликаты и некорректные ID
        unique_worker_ids = list(set(worker_ids))
        if len(unique_worker_ids) != len(worker_ids):
            messagebox.showwarning(
                "Проверка", "Обнаружены дублирующиеся работники в бригаде"
            )
            return None
        for worker_id in unique_worker_ids:
            if not isinstance(worker_id, int) or worker_id <= 0:
                messagebox.showwarning(
                    "Проверка",
                    "Все работники должны быть выбраны из подсказки (из базы)",
                )
                return None
            with get_connection() as conn:
                exists = conn.execute(
                    "SELECT 1 FROM workers WHERE id = ?", (worker_id,)
                ).fetchone()
                if not exists:
                    messagebox.showwarning(
                        "Проверка", f"Работник с ID {worker_id} не найден в базе данных"
                    )
            return None
        # Проверим, что виды работ выбраны корректно
        items: list[WorkOrderItemInput] = []
        for job_data in valid_job_types:
            if not job_data['id'] or job_data['id'] <= 0:
                messagebox.showwarning(
                    "Проверка", "Выберите вид работ из подсказок для каждой строки"
                )
                return None
            items.append(
                WorkOrderItemInput(job_type_id=job_data['id'], quantity=job_data['quantity'])
            )
        # Создаем список работников с именами и суммами
        workers: list[WorkOrderWorkerInput] = []
        for worker_id, worker_name in self.selected_workers.items():
            amount = self.worker_amounts.get(worker_id)
            workers.append(
                WorkOrderWorkerInput(
                    worker_id=worker_id, worker_name=worker_name, amount=amount
                )
            )

        # Проверяем существование изделий
        with get_connection() as conn:
            for product_id in self.selected_product_ids:
                p_row = conn.execute(
                    "SELECT 1 FROM products WHERE id=?", (product_id,)
                ).fetchone()
            if not p_row:
                messagebox.showwarning(
                    "Проверка",
                    f"Изделие с ID {product_id} не найдено в базе. Повторите выбор из подсказки",
                )
                return None

        return WorkOrderInput(
            order_no=order_no_val,
            date=date_str,
            product_id=None,  # Больше не используется
            contract_id=(
                int(self.selected_contract_id)
                if self.selected_contract_id is not None
                else None
            ),
            items=items,
            workers=workers,
            extra_product_ids=self.selected_product_ids,
        )

    def _save(self) -> None:
        if getattr(self, "_readonly", False):
            return
        
        wo = self._build_input()
        if not wo:
            return
        
        # Логируем данные для диагностики
        logger.info(
            "Попытка сохранения наряда: работники=%s, контракт=%s, изделия=%s, строк=%d",
            [(w.worker_id, w.worker_name) for w in wo.workers],
            wo.contract_id,
            wo.extra_product_ids,
            len(wo.items),
        )

        try:

            if self.editing_order_id:
                from services.work_orders import update_work_order  # lazy import

                with get_connection() as conn:
                    update_work_order(conn, self.editing_order_id, wo)
                messagebox.showinfo("Сохранено", "Наряд обновлен")
                logger.info("Наряд %s успешно обновлен", self.editing_order_id)
            else:
                with get_connection() as conn:
                    _id = create_work_order(conn, wo)
                messagebox.showinfo("Сохранено", "Наряд успешно сохранен")
                logger.info("Наряд %s успешно создан", _id)
        except sqlite3.IntegrityError as exc:
            logger.error("Ошибка целостности БД при сохранении наряда: %s", exc)
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {exc}")
            return
        except Exception as exc:
            logger.error(
                "Неожиданная ошибка при сохранении наряда: %s", exc, exc_info=True
            )
            messagebox.showerror("Ошибка", f"Не удалось сохранить наряд: {exc}")
            return
        
        self._reset_form()
        self._load_recent_orders()

    def _delete(self) -> None:
        if getattr(self, "_readonly", False):
            return
        if not self.editing_order_id:
            messagebox.showwarning("Проверка", "Выберите наряд в списке справа")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный наряд?"):
            return
        try:
            from services.work_orders import delete_work_order  # lazy import

            with get_connection() as conn:
                delete_work_order(conn, self.editing_order_id)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось удалить наряд: {exc}")
            return
        messagebox.showinfo("Готово", "Наряд удален")
        self._reset_form()
        self._load_recent_orders()

    def _cancel_edit(self) -> None:
        self._reset_form()

    def _reset_form(self) -> None:
        self.editing_order_id = None
        self.selected_contract_id = None
        self.selected_product_ids.clear()
        self.selected_products.clear()
        self.selected_workers.clear()
        self.item_rows.clear()
        self._manual_worker_counter = -1
        self._manual_product_counter = -1
        
        # Очищаем новые виджеты
        if hasattr(self, 'products_widget'):
            self.products_widget.clear_items()
        if hasattr(self, 'workers_widget'):
            self.workers_widget.clear_items()
        if hasattr(self, 'job_types_widget'):
            self.job_types_widget.clear_items()
        
        # Очищаем старые виджеты
        # Старый метод _refresh_products_display удален
        for w in self.workers_list.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        for w in self.suggest_contract_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        for w in self.suggest_product_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        for w in self.suggest_job_frame.winfo_children():
            try:
                w.destroy()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        self.suggest_contract_frame.place_forget()
        self.suggest_product_frame.place_forget()
        self.suggest_job_frame.place_forget()
        self.date_var.set(dt.date.today().strftime(CONFIG.date_format))
        try:
            # Автозаполнение следующего номера при создании нового наряда
            with get_connection() as conn:
                self.order_no_var.set(str(q.next_order_no(conn)))
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self.contract_entry.delete(0, "end")
        self.product_entry.delete(0, "end")
        try:
            for child in self.items_table.winfo_children():
                child.destroy()
            self._item_widgets.clear()
            self._item_row_widgets.clear()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Стартовая пустая строка для видов работ - удалена, используется новый виджет
        self._update_totals()
        try:
            self.save_btn.configure(
                text="Сохранить",
                fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
            )
        except Exception:
            self.save_btn.configure(text="Сохранить")
        try:
            self._set_edit_locked(False)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _show_inline_item_editor(self) -> None:
        try:
            self._inline_item_editor.grid()
            self.job_entry.focus_set()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _show_inline_worker_editor(self) -> None:
        try:
            self._inline_worker_editor.grid()
            self.worker_entry.focus_set()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _pick_worker_for_row(
        self, wid_current: int, worker_id: int, label: str, entry: ctk.CTkEntry
    ) -> None:
        # Установить имя в строке; если пришёл положительный id — заменим ключ, иначе оставим вручную
        try:
            entry.delete(0, "end")
            entry.insert(0, label)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        record_use("work_orders.worker", label)
        # Если это новый id, перенесём сумму
        if worker_id > 0 and wid_current in self.selected_workers:
            amount = self.worker_amounts.get(wid_current, 0.0)
            # Удалим старый ключ и добавим новый
            del self.selected_workers[wid_current]
            self.selected_workers[worker_id] = label
            if amount:
                self.worker_amounts[worker_id] = amount
            if wid_current in self.worker_amounts:
                del self.worker_amounts[wid_current]
            if wid_current in self._manual_amount_ids:
                self._manual_amount_ids.discard(wid_current)
        else:
            self.selected_workers[wid_current] = label
        self.suggest_worker_frame.place_forget()
        # Старый метод _refresh_workers_display удален


    def _remove_product(self, product_id: int) -> None:
        """Удаляет изделие из списка"""
        if product_id in self.selected_products:
            del self.selected_products[product_id]
            # Также удаляем из старого списка если есть
            if product_id in self.selected_product_ids:
                self.selected_product_ids.remove(product_id)
            # Старый метод _refresh_products_display удален
            self._update_contract_from_products()

    # Старые методы для работы с изделиями удалены - используется новый виджет

    # Новые методы для работы с едиными виджетами
    
    def _on_product_add(self, product_id: int, product_name: str):
        """Обработчик добавления изделия"""
        try:
            if product_id > 0 and product_id not in self.selected_product_ids:
                self.selected_product_ids.append(product_id)
                self._update_contract_from_products()
                record_use("work_orders.product", product_name)
        except Exception as exc:
            logger.exception("Ошибка добавления изделия: %s", exc)
    
    def _on_product_remove(self, product_id: int):
        """Обработчик удаления изделия"""
        try:
            if product_id in self.selected_product_ids:
                self.selected_product_ids.remove(product_id)
                self._update_contract_from_products()
        except Exception as exc:
            logger.exception("Ошибка удаления изделия: %s", exc)
    
    def _on_worker_add(self, worker_id: int, worker_name: str):
        """Обработчик добавления работника"""
        try:
            if worker_id > 0 and worker_id not in self.selected_workers:
                self.selected_workers[worker_id] = worker_name
                self.worker_amounts[worker_id] = 0.0
                self._update_totals()
                record_use("work_orders.worker", worker_name)
                # Пересчитываем суммы работников
                self._redistribute_worker_amounts()
        except Exception as exc:
            logger.exception("Ошибка добавления работника: %s", exc)
    
    def _on_worker_remove(self, worker_id: int):
        """Обработчик удаления работника"""
        try:
            if worker_id in self.selected_workers:
                del self.selected_workers[worker_id]
                if worker_id in self.worker_amounts:
                    del self.worker_amounts[worker_id]
                self._update_totals()
                # Пересчитываем суммы работников
                self._redistribute_worker_amounts()
        except Exception as exc:
            logger.exception("Ошибка удаления работника: %s", exc)
    
    def _on_worker_amount_change(self, worker_id: int, amount: float):
        """Обработчик изменения суммы работника"""
        try:
            self.worker_amounts[worker_id] = amount
            self._update_totals()
        except Exception as exc:
            logger.exception("Ошибка изменения суммы работника: %s", exc)
    
    def _on_job_type_add(self, job_type_id: int, job_type_name: str):
        """Обработчик добавления вида работ"""
        try:
            # Создаем новый элемент работы
            item = ItemRow(
                job_type_id=job_type_id,
                job_type_name=job_type_name,
                quantity=1.0,
                unit_price=0.0,
                line_amount=0.0,
            )
            self.item_rows.append(item)
            # Старый метод _add_blank_item_row удален - используется новый виджет
            record_use("work_orders.job_type", job_type_name)
        except Exception as exc:
            logger.exception("Ошибка добавления вида работ: %s", exc)
    
    def _on_job_type_remove(self, job_type_id: int):
        """Обработчик удаления вида работ"""
        try:
            # Находим и удаляем соответствующий элемент
            for i, item in enumerate(self.item_rows):
                if item.job_type_id == job_type_id:
                    self._remove_item_row(i)
                    break
        except Exception as exc:
            logger.exception("Ошибка удаления вида работ: %s", exc)
    
    def _on_job_type_quantity_change(self, job_type_id: int, quantity: float):
        """Обработчик изменения количества вида работ"""
        try:
            # Находим соответствующий элемент и обновляем количество
            for item in self.item_rows:
                if item.job_type_id == job_type_id:
                    item.quantity = quantity
                    item.line_amount = item.quantity * item.unit_price
                    self._update_totals()
                    break
            
            # Пересчитываем суммы работников
            self._redistribute_worker_amounts()
        except Exception as exc:
            logger.exception("Ошибка изменения количества вида работ: %s", exc)

    # Старый метод _refresh_products_display удален - используется новый виджет изделий

    def _redistribute_worker_amounts(self) -> None:
        """Равномерно распределить суммы видов работ между работниками"""
        try:
            # Получаем общую сумму всех видов работ
            total_job_amount = 0.0
            job_types_data = self.job_types_widget.get_items_data()
            # Фильтруем пустые элементы для расчета
            valid_job_types = [item for item in job_types_data if item['name'].strip()]
            for job_data in valid_job_types:
                total_job_amount += job_data['total']
            
            # Получаем количество работников
            worker_count = len(self.selected_workers)
            
            if worker_count == 0 or total_job_amount == 0:
                # Если нет работников или сумма равна 0, обнуляем все суммы
                for worker_id in self.worker_amounts:
                    self.worker_amounts[worker_id] = 0.0
            else:
                # Распределяем сумму равномерно между работниками
                amount_per_worker = total_job_amount / worker_count
                for worker_id in self.selected_workers:
                    self.worker_amounts[worker_id] = amount_per_worker
            
            # Обновляем отображение сумм работников
            self._update_totals()
            
        except Exception as exc:
            logger.exception("Ошибка пересчета сумм работников: %s", exc)

    def _update_contract_from_products(self) -> None:
        """Обновляет контракт на основе выбранных изделий"""
        # Используем новый список ID изделий
        product_ids = [pid for pid in self.selected_product_ids if pid > 0]
        
        if not product_ids:
            self.selected_contract_id = None
            self.contract_entry.delete(0, "end")
            return

        with get_connection() as conn:
            contract_id = q.get_contract_from_products(conn, product_ids)

            if contract_id:
                self.selected_contract_id = contract_id
                contract = q.get_contract(conn, contract_id)
                if contract:
                    self.contract_entry.delete(0, "end")
                    self.contract_entry.insert(
                        0, f"{contract['code']} — {contract['name']}"
                    )
            else:
                # Если нет общего контракта, показываем предупреждение
                self.selected_contract_id = None
                self.contract_entry.delete(0, "end")
                self.contract_entry.insert(0, "Разные контракты")
