from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

from utils.user_prefs import set_db_path, get_current_db_path
from db.sqlite import get_connection
from db.schema import initialize_schema


class DbSetupDialog(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Настройка базы данных")
        self.geometry("520x220")
        self.resizable(False, False)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        try:
            self.grab_set()
        except Exception:
            pass

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

        ctk.CTkButton(btns, text="Выбрать существующую БД...", command=self._choose_existing).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Создать новую БД...", command=self._create_new).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Выход", fg_color="#6b7280", command=self._cancel).pack(side="right", padx=6)

        self.result: bool = False

    def _choose_existing(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        if not p.exists():
            messagebox.showerror("База данных", "Файл не найден")
            return
        # Проверим, что можно открыть
        try:
            with get_connection(p) as conn:
                # Лёгкая проверка — запроc sqlite_master
                conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        except Exception as exc:
            messagebox.showerror("База данных", f"Не удалось открыть файл БД: {exc}")
            return
        set_db_path(p)
        self._ok_and_close()

    def _create_new(self) -> None:
        initial_name = "app.db"
        cur = Path(get_current_db_path())
        try:
            if cur.parent.exists():
                initial_name = cur.name
        except Exception:
            pass
        path = filedialog.asksaveasfilename(
            title="Создать новую базу данных",
            defaultextension=".db",
            initialfile=initial_name,
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            set_db_path(p)
            with get_connection(p) as conn:
                initialize_schema(conn)
        except Exception as exc:
            messagebox.showerror("Создание БД", f"Не удалось создать БД: {exc}")
            return
        self._ok_and_close()

    def _cancel(self) -> None:
        self.result = False
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _ok_and_close(self) -> None:
        self.result = True
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


