from __future__ import annotations

import logging

from config.settings import CONFIG
from db.schema import initialize_schema
from db.sqlite import get_connection
from utils.backup import backup_sqlite_db
from utils.logging import configure_logging
from gui.app_window import AppWindow
from gui.login_dialog import LoginDialog
from utils.user_prefs import get_current_db_path, set_db_path
from utils.network_db import get_network_db_path
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from utils.auto_yadisk import start_yadisk_upload_scheduler


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # Проверка наличия БД ДО создания основного окна.
    # Сначала пытаемся подключиться к сетевой БД, если локальная не найдена.
    db_path = get_current_db_path()
    if not db_path.exists():
        logger.info("Локальная БД не найдена. Пытаемся подключиться к сетевой БД...")
        
        # Пытаемся подключиться к сетевой БД
        network_db_path = get_network_db_path()
        if network_db_path and network_db_path.exists():
            logger.info(f"Найдена сетевая БД: {network_db_path}")
            set_db_path(network_db_path)
            db_path = network_db_path
        else:
            logger.warning("Сетевая БД недоступна. Показываем диалог выбора БД...")
            
            # Показываем диалог для выбора БД
            try:
                tmp = ctk.CTk()
                tmp.withdraw()
                
                from gui.network_db_dialog import NetworkDbDialog
                dialog = NetworkDbDialog(tmp)
                tmp.wait_window(dialog)
                tmp.destroy()
                
                # Обновляем путь после диалога
                db_path = get_current_db_path()
                
            except Exception as exc:
                logger.exception(f"Ошибка в диалоге выбора БД: {exc}")
                # Fallback к простому tkinter диалогу
                try:
                    tmp = tk.Tk()
                    tmp.withdraw()
                    create_new = messagebox.askyesno(
                        "База данных",
                        "База данных не найдена.\n\nСоздать новую базу данных?\n(Нет — выбрать существующую)",
                        parent=tmp,
                    )
                    chosen: str | None = None
                    if create_new:
                        initial = "base_sdelka_rmz.db"
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
                            try:
                                p.parent.mkdir(parents=True, exist_ok=True)
                            except Exception:
                                pass
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
                    except Exception:
                        pass
                except Exception:
                    pass
                
                # Обновляем путь после fallback диалога
                db_path = get_current_db_path()
        
        # Если по-прежнему файла нет — выходим тихо
        if not db_path.exists():
            logger.error("База данных не выбрана/не создана. Завершение.")
            return

    # Бэкап БД (если файл существует)
    backup_sqlite_db(db_path)

    # Инициализация схемы (идемпотентно, не затирает данные существующей БД)
    with get_connection() as conn:
        initialize_schema(conn)

    # Единый root: создаём основное окно, скрываем, показываем диалог, затем раскрываем окно
    from utils.runtime_mode import set_mode, AppMode
    app = AppWindow()
    try:
        try:
            app.withdraw()
        except Exception:
            pass
        try:
            dlg = LoginDialog(app)
            app.wait_window(dlg)
        except Exception:
            set_mode(AppMode.FULL)
        # Показать и развернуть главное окно
        try:
            app.deiconify()
            app.update_idletasks()
            try:
                app.lift()
                app.focus_force()
            except Exception:
                pass
            # Пересобрать формы под итоговый режим (readonly/full)
            try:
                app.rebuild_forms_for_mode()
            except Exception:
                pass
            # Небольшая задержка перед разворачиванием, чтобы избежать мигания
            def _zoom():
                try:
                    app.state("zoomed")
                except Exception:
                    pass
            try:
                app.after(50, _zoom)
            except Exception:
                _zoom()
            # Старт планировщика автовыгрузки на Яндекс.Диск (08,10,12,14,16,18)
            try:
                start_yadisk_upload_scheduler()
            except Exception:
                logging.getLogger(__name__).exception("Не удалось запустить планировщик Yandex Диска")
        except Exception:
            pass
        app.mainloop()
    finally:
        # Безопасно отменяем отложенные коллбеки, чтобы не было ошибок after script на первом старте
        try:
            if hasattr(app, "_after_ids"):
                for aid in list(app._after_ids):
                    try:
                        app.after_cancel(aid)
                    except Exception:
                        pass
        except Exception:
            pass


if __name__ == "__main__":
    main()