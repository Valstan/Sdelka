from __future__ import annotations

import logging
import tkinter as tk
from tkinter import filedialog, messagebox

from config.settings import ensure_data_directories
from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db
from utils.logging import configure_logging
from gui.app_window import AppWindow
from gui.login_dialog import LoginDialog
from utils.user_prefs import get_current_db_path, set_db_path


def handle_tcl_error(func, *args, **kwargs):
    """Обработчик ошибок TclError для CustomTkinter виджетов."""
    try:
        return func(*args, **kwargs)
    except tk.TclError as e:
        # Игнорируем ошибки с недействительными именами команд canvas
        if "invalid command name" in str(e):
            logging.getLogger(__name__).debug(f"Ignored TclError: {e}")
            return None
        else:
            # Пробрасываем другие TclError
            raise e


def setup_tcl_error_handling():
    """Настройка глобальной обработки ошибок TclError."""
    import sys
    
    def tcl_error_handler(exc_type, exc_value, exc_traceback):
        if exc_type is tk.TclError:
            error_msg = str(exc_value)
            if "invalid command name" in error_msg or "can't invoke" in error_msg:
                logger.debug(f"Ignored global TclError: {error_msg}")
                return
        # Для всех других ошибок используем стандартную обработку
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = tcl_error_handler


def _ensure_db_available(logger: logging.Logger) -> None:
    """Ensure database path is set and DB exists; prompt user if necessary.

    Новая логика: работаем только с локальной БД, синхронизация через Яндекс.Диск
    """
    db_path = get_current_db_path()
    if db_path.exists():
        return

    logger.info("Локальная БД не найдена. Создаем новую или выбираем существующую...")

    # Простой диалог выбора
    try:
        tmp = tk.Tk()
        tmp.withdraw()
        create_new = messagebox.askyesno(
            "База данных",
            "Локальная база данных не найдена.\n\nСоздать новую базу данных?\n(Нет — выбрать существующую)\n\nПримечание: Синхронизация с другими компьютерами будет происходить через Яндекс.Диск",
            parent=tmp,
        )
        chosen: str | None = None
        if create_new:
            initial = "base_sdelka.db"
            chosen = filedialog.asksaveasfilename(
                parent=tmp,
                title="Создать новую базу данных",
                defaultextension=".db",
                initialfile=initial,
                filetypes=[["SQLite DB", "*.db"], ["Все файлы", "*.*"]],
            )
            if chosen:
                from pathlib import Path as _P

                p = _P(chosen)
                p.parent.mkdir(parents=True, exist_ok=True)
                set_db_path(p)
                with get_connection(p) as conn:
                    initialize_schema(conn)
        else:
            chosen = filedialog.askopenfilename(
                parent=tmp,
                title="Выберите файл базы данных",
                filetypes=[["SQLite DB", "*.db"], ["Все файлы", "*.*"]],
            )
            if chosen:
                from pathlib import Path as _P

                p = _P(chosen)
                set_db_path(p)
        try:
            tmp.destroy()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
    except Exception as exc:
        logger.exception("Ошибка в диалоге выбора БД: %s", exc)


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Настройка обработки ошибок TclError для CustomTkinter
    setup_tcl_error_handling()
    
    # Применение патчей для CustomTkinter
    from utils.customtkinter_patches import apply_all_patches
    apply_all_patches()

    # Create data/logs/backups dirs explicitly at startup
    try:
        ensure_data_directories()
    except Exception:
        logger.exception("Не удалось создать служебные директории")

    # Ensure DB is available (may prompt the user)
    _ensure_db_available(logger)

    db_path = get_current_db_path()
    if not db_path.exists():
        logger.error("База данных не выбрана/не создана. Завершение.")
        return

    # Бэкап БД (если файл существует)
    backup_sqlite_db(db_path)

    # Инициализация схемы (идемпотентно, не затирает данные существующей БД)
    with get_connection() as conn:
        initialize_schema(conn)

    # Единый root: создаём основное окно, скрываем, показываем диалог, затем синхронизацию, затем раскрываем окно
    from utils.runtime_mode import set_mode, AppMode

    app = AppWindow()
    try:
        try:
            app.withdraw()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            dlg = LoginDialog(app)
            app.wait_window(dlg)
        except Exception:
            set_mode(AppMode.FULL)

        # Пересобрать формы под итоговый режим (readonly/full) но пока не показываем окно
        try:
            app.rebuild_forms_for_mode()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        # Запускаем фоновую синхронизацию при старте (без диалога)
        try:
            logging.getLogger(__name__).info(
                "Запуск фоновой синхронизации при старте..."
            )
            from services.auto_sync import sync_on_startup
            import threading

            # Запускаем синхронизацию в фоновом потоке
            def background_sync():
                try:
                    sync_on_startup()
                    # После завершения обновляем статус
                    app.after(
                        0, lambda: app._update_sync_status("Синхронизация завершена")
                    )
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ошибка фоновой синхронизации: %s", exc
                    )
                    app.after(
                        0, lambda: app._update_sync_status("Ошибка синхронизации")
                    )

            sync_thread = threading.Thread(target=background_sync, daemon=True)
            sync_thread.start()

            # Показываем статус синхронизации
            app.after(1000, lambda: app._update_sync_status("Синхронизация в фоне..."))

        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Ошибка запуска фоновой синхронизации: %s", exc
            )

        # Показать и развернуть главное окно (синхронизация идет в фоне)
        try:
            app.deiconify()
            app.update_idletasks()
            try:
                app.lift()
                app.focus_force()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ignored unexpected error: %s", exc
                )

            # Небольшая задержка перед разворачиванием, чтобы избежать мигания
            def _zoom():
                try:
                    app.state("zoomed")
                except Exception as exc:
                    logging.getLogger(__name__).exception(
                        "Ignored unexpected error: %s", exc
                    )

            try:
                app.after(50, _zoom)
            except Exception:
                _zoom()

            # Запуск периодической синхронизации в фоне
            try:
                app.start_auto_sync()
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Ошибка запуска периодической синхронизации: %s", exc
                )

        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        app.mainloop()
    finally:
        # Безопасно отменяем отложенные коллбеки, чтобы не было ошибок after script на первом старте
        try:
            if hasattr(app, "_after_ids"):
                for aid in list(app._after_ids):
                    try:
                        app.after_cancel(aid)
                    except Exception as exc:
                        logging.getLogger(__name__).exception(
                            "Ignored unexpected error: %s", exc
                        )
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)


if __name__ == "__main__":
    main()
