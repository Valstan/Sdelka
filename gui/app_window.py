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


import logging


class AppWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        try:
            ver = get_version()
        except Exception:
            ver = get_version()
        self._version = ver
        self._app_title = f"СДЕЛКА РМЗ {ver}"
        self.title(self._app_title)
        # Стартовать развёрнутым на весь экран (Windows: state('zoomed')).
        # Оставляем системную панель задач и кнопки заголовка.
        try:
            self.state("zoomed")
        except Exception:
            # Запасной вариант: задать крупный размер
            self.geometry("1600x900")
        # Разрешить изменение размера пользователем
        try:
            self.resizable(True, True)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self._tab_font_normal = None
        self._tab_font_active = None
        self._tabview = None
        self._segmented_button = None
        self._title_badge = None
        # Отслеживание запланированных after-задач для корректного завершения
        self._after_ids: set[str] = set()
        self._closing: bool = False
        try:
            self.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Применить пользовательские шрифты для остального UI
        try:
            prefs = load_prefs()
            apply_user_fonts(self, prefs)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Универсальный менеджер синхронизации
        from gui.sync_progress_dialog import SyncProgressManager

        self._sync_progress_manager = SyncProgressManager(self)
        self._build_ui()

    def _build_ui(self) -> None:
        # Верхняя панель с кнопкой синхронизации
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(fill="x", padx=5, pady=(5, 0))
        top_frame.pack_propagate(False)

        # Кнопка принудительной синхронизации
        self._sync_button = ctk.CTkButton(
            top_frame,
            text="🔄 Обновить данные",
            fg_color="#dc2626",  # Красный цвет
            hover_color="#b91c1c",
            width=200,
            height=35,
            command=self._force_sync,
        )
        self._sync_button.pack(side="right", padx=10, pady=7)

        # Статус синхронизации
        self._sync_status_label = ctk.CTkLabel(
            top_frame, text="Готов к работе", font=ctk.CTkFont(size=12)
        )
        self._sync_status_label.pack(side="left", padx=10, pady=7)

        # Основной Tabview
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both", pady=(5, 0))
        self._tabview = tabview

        self.tab_orders = tabview.add("Наряды")
        self.tab_refs = tabview.add("Справочники")
        self.tab_reports = tabview.add("Отчеты")
        self.tab_settings = tabview.add("Настройки")

        # Формы (первичная сборка)
        self._build_forms_for_current_mode()

        # Фиксированные шрифты вкладок (не зависят от настроек пользователя)
        self._setup_tab_fonts(self._tabview)
        try:
            if hasattr(self, "_refs_tabs") and getattr(self, "_refs_tabs") is not None:
                self._setup_tab_fonts(self._refs_tabs)  # type: ignore[arg-type]
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.bind(
                "<<UIFontsChanged>>",
                lambda e: [
                    self._setup_tab_fonts(self._tabview),
                    (
                        self._setup_tab_fonts(self._refs_tabs)
                        if hasattr(self, "_refs_tabs")
                        and getattr(self, "_refs_tabs") is not None
                        else None
                    ),
                ],
            )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Создаем компактный бейдж названия/версии на одном уровне с кнопками табов
        self._create_title_badge()
        # Следим за ресайзом, чтобы поддерживать позиционирование на уровне сегментированных кнопок
        self.bind("<Configure>", lambda e: self._place_title_badge(), add="+")
        try:
            seg = getattr(self._tabview, "_segmented_button", None)
            if (
                seg is not None
                and hasattr(seg, "__class__")
                and "CTkSegmentedButton" not in str(seg.__class__)
            ):
                seg.bind("<Configure>", lambda e: self._place_title_badge(), add="+")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        # Первичное размещение
        self._schedule_after(50, self._place_title_badge)

        # Малый бейдж "Режим просмотра" справа от сегментированных кнопок
        try:
            seg = getattr(self._tabview, "_segmented_button", None)
            self._readonly_badge = ctk.CTkLabel(
                self, text="Режим просмотра", text_color="#dc2626"
            )

            def place_badge():
                try:
                    # Проверяем существование всех виджетов
                    if (
                        not hasattr(self, "_readonly_badge")
                        or self._readonly_badge is None
                        or not self._readonly_badge.winfo_exists()
                    ):
                        return

                    if seg is None or not seg.winfo_exists():
                        try:
                            self._readonly_badge.place_forget()
                        except Exception:
                            pass
                        return

                    # Показывать бейдж только в режиме readonly
                    if not is_readonly():
                        try:
                            self._readonly_badge.place_forget()
                        except Exception:
                            pass
                        return

                    self.update_idletasks()
                    seg.update_idletasks()
                    self._readonly_badge.update_idletasks()
                    x = seg.winfo_rootx() - self.winfo_rootx()
                    y = seg.winfo_rooty() - self.winfo_rooty()
                    w = seg.winfo_width()
                    self._readonly_badge.place(x=x + w + 16, y=y + 6)
                    self._readonly_badge.lift()
                except Exception:
                    try:
                        if (
                            hasattr(self, "_readonly_badge")
                            and self._readonly_badge
                            and self._readonly_badge.winfo_exists()
                        ):
                            self._readonly_badge.place_forget()
                    except Exception:
                        pass  # Полностью игнорируем ошибки

            self.bind("<Configure>", lambda e: place_badge(), add="+")
            if (
                seg is not None
                and hasattr(seg, "__class__")
                and "CTkSegmentedButton" not in str(seg.__class__)
            ):
                try:
                    seg.bind("<Configure>", lambda e: place_badge(), add="+")
                except Exception:
                    pass  # Не поддерживает bind
            self._schedule_after(60, place_badge)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _create_title_badge(self) -> None:
        # Фиксированный шрифт ~8pt в пикселях (не зависит от scaling/настроек)
        try:
            base_family = tkfont.nametofont("TkDefaultFont").cget("family")
        except Exception:
            base_family = "TkDefaultFont"
        # 8pt ~ 11px при 96dpi; используем 11px для стабильности
        fixed_font_small = ctk.CTkFont(family=base_family, size=11, weight="normal")
        fixed_font_small_bold = ctk.CTkFont(family=base_family, size=11, weight="bold")

        badge = ctk.CTkFrame(
            self, corner_radius=4, border_width=1, border_color=("gray70", "gray40")
        )
        # Минимальные внутренние отступы
        inner = ctk.CTkFrame(badge, fg_color="transparent")
        inner.pack(padx=3, pady=0)

        # Фиксированная минимальная высота строк, чтобы убрать межстрочные зазоры
        line_h = 12  # px

        # Строки названия без межстрочных отступов
        short = ctk.CTkLabel(
            inner,
            text=f"СДЕЛКА РМЗ {self._version}",
            font=fixed_font_small_bold,
            anchor="w",
            justify="left",
            height=line_h,
        )
        short.pack(anchor="w", pady=0)
        line2 = ctk.CTkLabel(
            inner,
            text="Программа учёта нарядов и контрактов",
            font=fixed_font_small,
            anchor="w",
            justify="left",
            height=line_h,
        )
        line2.pack(anchor="w", pady=0)
        line3 = ctk.CTkLabel(
            inner,
            text="РМЗ",
            font=fixed_font_small,
            anchor="w",
            justify="left",
            height=line_h,
        )
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
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

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
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            buttons = getattr(seg, "_buttons_dict", {})
            for name, btn in buttons.items():
                f = active if name == current else normal
                try:
                    # Преобразуем tkinter.font.Font в формат CustomTkinter
                    if hasattr(f, "cget"):
                        font_family = f.cget("family")
                        font_size = f.cget("size")
                        font_weight = f.cget("weight")
                        font_slant = f.cget("slant")
                        ctk_font = (font_family, font_size, font_weight, font_slant)
                    else:
                        ctk_font = f
                    btn.configure(font=ctk_font)
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
                # Без разрывов между кнопками
                try:
                    btn.grid_configure(padx=0, pady=0)
                except Exception:
                    try:
                        btn.pack_configure(padx=0, pady=0)
                    except Exception as exc:
                        logging.getLogger(__name__).exception(
                            "Ignored unexpected error: %s", exc
                        )
                # Применим шрифт всем дочерним виджетам внутри кнопки
                try:
                    for child in btn.winfo_children():
                        try:
                            # Проверяем, поддерживает ли виджет шрифты
                            if (
                                hasattr(child, "configure")
                                and "font" in child.configure()
                            ):
                                if hasattr(f, "cget"):
                                    font_family = f.cget("family")
                                    font_size = f.cget("size")
                                    font_weight = f.cget("weight")
                                    font_slant = f.cget("slant")
                                    ctk_font = (
                                        font_family,
                                        font_size,
                                        font_weight,
                                        font_slant,
                                    )
                                else:
                                    ctk_font = f
                                child.configure(font=ctk_font)
                        except Exception as exc:
                            logging.getLogger(__name__).exception(
                                "Ignored unexpected error: %s", exc
                            )
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )

        # CTkSegmentedButton не поддерживает bind, пропускаем
        if hasattr(seg, "__class__") and "CTkSegmentedButton" not in str(seg.__class__):
            try:
                seg.bind("<ButtonRelease-1>", lambda e: apply_fonts(), add="+")
                seg.bind("<KeyRelease>", lambda e: apply_fonts(), add="+")
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        # Периодически отслеживать смену вкладки и обновлять шрифты
        try:
            seg._last_tab_caption = None

            def _watch():
                if self._closing:
                    return
                try:
                    current = tabview.get()
                except Exception:
                    current = None
                if getattr(seg, "_last_tab_caption", None) != current:
                    seg._last_tab_caption = current
                    apply_fonts()
                self._schedule_after(120, _watch)

            self._schedule_after(80, _watch)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self._schedule_after(50, apply_fonts)

    def _clear_children(self, widget) -> None:
        try:
            for child in list(widget.winfo_children()):
                try:
                    child.destroy()
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _build_forms_for_current_mode(self) -> None:
        # Очистить вкладки и пересоздать формы согласно текущему режиму
        try:
            self._clear_children(self.tab_orders)
            self._clear_children(self.tab_refs)
            self._clear_children(self.tab_reports)
            self._clear_children(self.tab_settings)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Наряды
        WorkOrdersForm(self.tab_orders, readonly=is_readonly()).pack(
            expand=True, fill="both"
        )

        # Справочники (внутренние вкладки)
        refs_tabs = ctk.CTkTabview(self.tab_refs)
        self._refs_tabs = refs_tabs
        refs_tabs.pack(expand=True, fill="both", padx=10, pady=(0, 0))
        tab_workers = refs_tabs.add("Работники")
        tab_jobs = refs_tabs.add("Виды работ")
        tab_products = refs_tabs.add("Изделия")
        tab_contracts = refs_tabs.add("Контракты")

        WorkersForm(tab_workers, readonly=is_readonly()).pack(expand=True, fill="both")
        JobTypesForm(tab_jobs, readonly=is_readonly()).pack(expand=True, fill="both")
        ProductsForm(tab_products, readonly=is_readonly()).pack(
            expand=True, fill="both"
        )
        ContractsForm(tab_contracts, readonly=is_readonly()).pack(
            expand=True, fill="both"
        )

        # Отчеты
        ReportsView(self.tab_reports).pack(expand=True, fill="both")

        # Настройки
        SettingsView(self.tab_settings, readonly=is_readonly()).pack(
            expand=True, fill="both"
        )

    def rebuild_forms_for_mode(self) -> None:
        # Публичный метод для пересборки после смены режима (после диалога входа)
        self._build_forms_for_current_mode()
        try:
            self._setup_tab_fonts(self._tabview)
            if hasattr(self, "_refs_tabs") and getattr(self, "_refs_tabs") is not None:
                self._setup_tab_fonts(self._refs_tabs)  # type: ignore[arg-type]
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _schedule_after(self, delay_ms: int, callback) -> None:
        if self._closing:
            return
        try:
            aid = self.after(delay_ms, callback)
            try:
                self._after_ids.add(aid)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _on_close(self) -> None:
        self._closing = True

        # Выполняем синхронизацию при выключении
        try:
            from services.auto_sync import sync_on_shutdown

            # Используем универсальный метод синхронизации
            self.sync_with_dialog(sync_on_shutdown, "Синхронизация при выключении")

            # Ждем завершения синхронизации асинхронно
            def wait_for_sync_completion():
                if (
                    not self._sync_progress_manager._sync_thread
                    or not self._sync_progress_manager._sync_thread.is_alive()
                ):
                    # Синхронизация завершена, можно закрывать
                    self._finalize_close()
                else:
                    # Проверяем снова через 500мс
                    self.after(500, wait_for_sync_completion)

            self.after(500, wait_for_sync_completion)
            return  # Не закрываем сразу, ждем синхронизацию

        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка синхронизации при закрытии: %s", exc
            )
            # Если ошибка синхронизации, закрываем принудительно
            self._finalize_close()

    def _finalize_close(self) -> None:
        """Финальное закрытие программы после синхронизации"""
        # Отменить все запланированные after
        for aid in list(self._after_ids):
            try:
                self.after_cancel(aid)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )
            try:
                self._after_ids.discard(aid)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

        # Очищаем менеджер прогресса
        if hasattr(self, "_sync_progress_manager") and self._sync_progress_manager:
            try:
                self._sync_progress_manager.cleanup()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

        # Очищаем readonly badge
        if hasattr(self, "_readonly_badge") and self._readonly_badge:
            try:
                if self._readonly_badge.winfo_exists():
                    self._readonly_badge.destroy()
            except Exception:
                pass

        try:
            super().destroy()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _force_sync(self) -> None:
        """Принудительная синхронизация по нажатию красной кнопки"""
        try:
            from services.auto_sync import force_sync

            self.sync_with_dialog(force_sync, "Принудительная синхронизация")

            # Обновляем UI после завершения
            def check_completion():
                if self._sync_progress_manager.dialog is None:
                    # Диалог закрыт, обновляем формы
                    self._refresh_all_forms()
                    self._update_sync_status("Готов к работе")
                else:
                    # Проверяем снова через секунду
                    self.after(1000, check_completion)

            self.after(1000, check_completion)

        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка запуска принудительной синхронизации: %s", exc
            )
            self._update_sync_status("Ошибка синхронизации")

    def _sync_completed(self, success: bool) -> None:
        """Обработка завершения синхронизации"""
        try:
            # Включаем кнопку обратно
            self._sync_button.configure(state="normal", text="🔄 Обновить данные")

            if success:
                self._sync_status_label.configure(
                    text="Синхронизация завершена успешно"
                )
                # Обновляем все формы
                self._refresh_all_forms()
            else:
                self._sync_status_label.configure(text="Ошибка синхронизации")

        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка обработки завершения синхронизации: %s", exc
            )

    def _refresh_all_forms(self) -> None:
        """Обновление всех форм после синхронизации"""
        try:
            # Пересоздаем все формы, чтобы они подтянули новые данные
            self._build_forms_for_current_mode()
            logging.getLogger(__name__).info("Формы обновлены после синхронизации")
        except Exception as exc:
            logging.getLogger(__name__).exception("Ошибка обновления форм: %s", exc)

    def _update_sync_status(self, status: str) -> None:
        """Обновление статуса синхронизации"""
        try:
            if hasattr(self, "_sync_status_label"):
                self._sync_status_label.configure(text=status)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ошибка обновления статуса: %s", exc)

    def sync_with_dialog(
        self, sync_function, title: str = "Синхронизация данных"
    ) -> None:
        """Универсальный метод синхронизации с диалогом прогресса"""
        try:
            self._sync_progress_manager.start_sync(
                sync_function=sync_function, title=title
            )
        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка запуска синхронизации с диалогом: %s", exc
            )

    def wait_for_sync_completion(self) -> None:
        """Ожидание завершения синхронизации (для блокирующих операций)"""
        import time

        while (
            self._sync_progress_manager._sync_thread
            and self._sync_progress_manager._sync_thread.is_alive()
        ):
            self.update()
            time.sleep(0.1)
        # Дополнительная пауза для завершения UI обновлений
        time.sleep(1)

    def start_auto_sync(self) -> None:
        """Запуск периодической автоматической синхронизации (только в фоне)"""
        try:
            from services.auto_sync import start_auto_sync

            # Запускаем только периодическую синхронизацию
            start_auto_sync(
                ui_refresh_callback=self._refresh_all_forms,
                sync_status_callback=self._update_sync_status,
            )
            logging.getLogger(__name__).info("Автоматическая синхронизация запущена")

        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка запуска автоматической синхронизации: %s", exc
            )
