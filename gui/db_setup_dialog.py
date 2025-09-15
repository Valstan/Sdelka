from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

from utils.user_prefs import set_db_path, get_current_db_path
from db.sqlite import get_connection
from db.schema import initialize_schema


import logging


class DbSetupDialog(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Настройка базы данных")
        self.geometry("520x220")
        self.resizable(False, False)
        try:
            # Всегда поверх и модально по отношению к временной корневой
            self.transient(master)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.attributes("-topmost", True)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.grab_set()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.focus_force()
            self.lift()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

        ctk.CTkLabel(
            self,
            text=(
                "База данных не найдена.\n"
                "Выберите существующую БД или создайте новую.\n"
                "Путь будет сохранен в настройках."
            ),
            justify="left",
        ).pack(padx=16, pady=(16, 12), anchor="w")

        btns = ctk.CTkFrame(self)
        btns.pack(fill="x", padx=16, pady=6)

        ctk.CTkButton(
            btns, text="Выбрать существующую БД...", command=self._choose_existing
        ).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Создать новую БД...", command=self._create_new).pack(
            side="left", padx=6
        )
        ctk.CTkButton(
            btns, text="Выход", fg_color="#6b7280", command=self._cancel
        ).pack(side="right", padx=6)

        self.result: bool = False

    def _choose_existing(self) -> None:
        path = self._ask_open_db()
        if not path:
            return
        p = Path(path)
        if not p.exists():
            messagebox.showerror("База данных", "Файл не найден", parent=self)
            return
        # Проверим, что можно открыть
        try:
            with get_connection(p) as conn:
                # Лёгкая проверка — запроc sqlite_master
                conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        except Exception as exc:
            messagebox.showerror(
                "База данных", f"Не удалось открыть файл БД: {exc}", parent=self
            )
            return
        set_db_path(p)
        self._ok_and_close()

    def _create_new(self) -> None:
        initial_name = "base_sdelka_rmz.db"
        cur = Path(get_current_db_path())
        try:
            if cur.parent.exists():
                initial_name = cur.name
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        path = self._ask_save_db(initial_name)
        if not path:
            return
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            set_db_path(p)
            with get_connection(p) as conn:
                initialize_schema(conn)
        except Exception as exc:
            messagebox.showerror(
                "Создание БД", f"Не удалось создать БД: {exc}", parent=self
            )
            return
        self._ok_and_close()

    def _cancel(self) -> None:
        self.result = False
        try:
            self.grab_release()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self.destroy()

    def _ok_and_close(self) -> None:
        self.result = True
        try:
            self.update_idletasks()
            self.grab_release()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        self.destroy()

    # --- Вспомогательные методы для корректного вызова диалогов файловой системы ---
    def _before_system_dialog(self) -> None:
        # Снять topmost и grab, чтобы системный проводник не прятался под окном
        try:
            self.attributes("-topmost", False)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.grab_release()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.update_idletasks()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _after_system_dialog(self) -> None:
        # Вернуть модальность и поверх всех окон
        try:
            self.grab_set()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.attributes("-topmost", True)
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        try:
            self.lift()
            self.focus_force()
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)

    def _ask_open_db(self) -> str | None:
        self._before_system_dialog()
        try:
            return filedialog.askopenfilename(
                parent=self,
                title="Выберите файл базы данных",
                filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
            )
        finally:
            self._after_system_dialog()

    def _ask_save_db(self, initial_name: str) -> str | None:
        self._before_system_dialog()
        try:
            return filedialog.asksaveasfilename(
                parent=self,
                title="Создать новую базу данных",
                defaultextension=".db",
                initialfile=initial_name,
                filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
            )
        finally:
            self._after_system_dialog()
