from __future__ import annotations

import customtkinter as ctk
import tkinter.font as tkfont

from gui.forms.workers_form import WorkersForm
from gui.forms.job_types_form import JobTypesForm
from gui.forms.products_form import ProductsForm
from gui.forms.contracts_form import ContractsForm
from gui.forms.work_order_form import WorkOrdersForm
from gui.forms.reports_view import ReportsView
from gui.forms.settings_view import SettingsView
from utils.user_prefs import load_prefs
from utils.ui_theming import apply_user_fonts
from utils.versioning import get_version
from utils.runtime_mode import is_readonly


class AppWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        try:
            ver = get_version()
        except Exception:
            ver = "3.1"
        self._version = ver
        self._app_title = f"СДЕЛКА РМЗ {ver}"
        self.title(self._app_title)
        self.geometry("1200x760")
        self._tab_font_normal = None
        self._tab_font_active = None
        self._tabview = None
        self._segmented_button = None
        self._title_badge = None
        # Применить пользовательские шрифты для остального UI
        try:
            prefs = load_prefs()
            apply_user_fonts(self, prefs)
        except Exception:
            pass
        self._build_ui()

    def _build_ui(self) -> None:
        # Основной Tabview
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both", pady=0)
        self._tabview = tabview

        self.tab_orders = tabview.add("Наряды")
        self.tab_refs = tabview.add("Справочники")
        self.tab_reports = tabview.add("Отчеты")
        self.tab_settings = tabview.add("Настройки")

        # Формы
        WorkOrdersForm(self.tab_orders, readonly=is_readonly()).pack(expand=True, fill="both")

        refs_tabs = ctk.CTkTabview(self.tab_refs)
        refs_tabs.pack(expand=True, fill="both", padx=10, pady=(0, 0))
        tab_workers = refs_tabs.add("Работники")
        tab_jobs = refs_tabs.add("Виды работ")
        tab_products = refs_tabs.add("Изделия")
        tab_contracts = refs_tabs.add("Контракты")

        WorkersForm(tab_workers, readonly=is_readonly()).pack(expand=True, fill="both")
        JobTypesForm(tab_jobs, readonly=is_readonly()).pack(expand=True, fill="both")
        ProductsForm(tab_products, readonly=is_readonly()).pack(expand=True, fill="both")
        ContractsForm(tab_contracts, readonly=is_readonly()).pack(expand=True, fill="both")

        ReportsView(self.tab_reports).pack(expand=True, fill="both")
        SettingsView(self.tab_settings, readonly=is_readonly()).pack(expand=True, fill="both")

        # Фиксированные шрифты вкладок (не зависят от настроек пользователя)
        self._setup_tab_fonts(self._tabview)
        self._setup_tab_fonts(refs_tabs)
        try:
            self.bind("<<UIFontsChanged>>", lambda e: [self._setup_tab_fonts(self._tabview), self._setup_tab_fonts(refs_tabs)])
        except Exception:
            pass

        # Создаем компактный бейдж названия/версии на одном уровне с кнопками табов
        self._create_title_badge()
        # Следим за ресайзом, чтобы поддерживать позиционирование на уровне сегментированных кнопок
        self.bind("<Configure>", lambda e: self._place_title_badge(), add="+")
        try:
            seg = getattr(self._tabview, "_segmented_button", None)
            if seg is not None:
                seg.bind("<Configure>", lambda e: self._place_title_badge(), add="+")
        except Exception:
            pass
        # Первичное размещение
        self.after(50, self._place_title_badge)

    def _create_title_badge(self) -> None:
        # Фиксированный шрифт ~8pt в пикселях (не зависит от scaling/настроек)
        try:
            base_family = tkfont.nametofont("TkDefaultFont").cget("family")
        except Exception:
            base_family = "TkDefaultFont"
        # 8pt ~ 11px при 96dpi; используем 11px для стабильности
        fixed_font_small = ctk.CTkFont(family=base_family, size=11, weight="normal")
        fixed_font_small_bold = ctk.CTkFont(family=base_family, size=11, weight="bold")

        badge = ctk.CTkFrame(self, corner_radius=4, border_width=1, border_color=("gray70", "gray40"))
        # Минимальные внутренние отступы
        inner = ctk.CTkFrame(badge, fg_color="transparent")
        inner.pack(padx=3, pady=0)

        # Фиксированная минимальная высота строк, чтобы убрать межстрочные зазоры
        line_h = 12  # px

        # Строки названия без межстрочных отступов
        short = ctk.CTkLabel(inner, text=f"СДЕЛКА РМЗ {self._version}", font=fixed_font_small_bold, anchor="w", justify="left", height=line_h)
        short.pack(anchor="w", pady=0)
        line2 = ctk.CTkLabel(inner, text="Программа учёта нарядов и контрактов", font=fixed_font_small, anchor="w", justify="left", height=line_h)
        line2.pack(anchor="w", pady=0)
        line3 = ctk.CTkLabel(inner, text="РМЗ", font=fixed_font_small, anchor="w", justify="left", height=line_h)
        line3.pack(anchor="w", pady=0)

        self._title_badge = badge

    def _place_title_badge(self) -> None:
        badge = self._title_badge
        if badge is None or not badge.winfo_exists():
            return
        try:
            seg = getattr(self._tabview, "_segmented_button", None)
            self.update_idletasks()
            badge.update_idletasks()
            if seg is not None and seg.winfo_exists():
                seg.update_idletasks()
                seg_y = seg.winfo_rooty()
                seg_h = seg.winfo_height()
                win_y = self.winfo_rooty()
                by = (seg_y - win_y) + max(0, (seg_h - badge.winfo_height()) // 2)
            else:
                by = 8
            # Левый верхний угол с небольшим отступом
            bx = 8
            # Не выходить за верхний край
            if by < 0:
                by = 0
            badge.place(x=bx, y=by)
            badge.lift()
        except Exception:
            try:
                badge.place_forget()
            except Exception:
                pass

    def _setup_tab_fonts(self, tabview: ctk.CTkTabview) -> None:
        try:
            base_family = tkfont.nametofont("TkDefaultFont").cget("family")
        except Exception:
            base_family = "TkDefaultFont"
        # Отрицательное значение размера = пиксели (не зависит от tk scaling и пользовательских настроек)
        normal = tkfont.Font(family=base_family, size=-20, weight="normal")
        active = tkfont.Font(family=base_family, size=-24, weight="bold")
        seg = getattr(tabview, "_segmented_button", None)
        if seg is None:
            return
        # Сохраняем ссылки, чтобы GC не удалил шрифты
        if not hasattr(seg, "_fixed_fonts"):
            seg._fixed_fonts = {}
        seg._fixed_fonts["normal"] = normal
        seg._fixed_fonts["active"] = active

        def apply_fonts():
            current = None
            try:
                current = tabview.get()
            except Exception:
                pass
            buttons = getattr(seg, "_buttons_dict", {})
            for name, btn in buttons.items():
                f = active if name == current else normal
                try:
                    btn.configure(font=f)
                except Exception:
                    pass
                # Без разрывов между кнопками
                try:
                    btn.grid_configure(padx=0, pady=0)
                except Exception:
                    try:
                        btn.pack_configure(padx=0, pady=0)
                    except Exception:
                        pass
                # Применим шрифт всем дочерним виджетам внутри кнопки
                try:
                    for child in btn.winfo_children():
                        try:
                            child.configure(font=f)
                        except Exception:
                            pass
                except Exception:
                    pass
        try:
            seg.bind("<ButtonRelease-1>", lambda e: apply_fonts(), add="+")
            seg.bind("<KeyRelease>", lambda e: apply_fonts(), add="+")
        except Exception:
            pass
        # Периодически отслеживать смену вкладки и обновлять шрифты
        try:
            seg._last_tab_caption = None
            def _watch():
                try:
                    current = tabview.get()
                except Exception:
                    current = None
                if getattr(seg, "_last_tab_caption", None) != current:
                    seg._last_tab_caption = current
                    apply_fonts()
                tabview.after(120, _watch)
            tabview.after(80, _watch)
        except Exception:
            pass
        tabview.after(50, apply_fonts)