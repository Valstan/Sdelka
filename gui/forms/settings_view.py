from __future__ import annotations

import shutil
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from config.settings import CONFIG
from services.merge_db import merge_from_file


class SettingsView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self._build_ui()

    def _build_ui(self) -> None:
        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(box, text="Резервное копирование и перенос базы данных").pack(anchor="w", pady=(0, 8))

        btns = ctk.CTkFrame(box)
        btns.pack(fill="x")

        ctk.CTkButton(btns, text="Сохранить копию базы...", command=self._export_db).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Слить с другой базой...", command=self._merge_db).pack(side="left", padx=6)

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(fill="x", padx=10, pady=10)

    def _export_db(self) -> None:
        src = Path(CONFIG.db_path)
        if not src.exists():
            messagebox.showerror("Экспорт", "Файл базы данных не найден")
            return
        dest = filedialog.asksaveasfilename(
            title="Сохранить копию базы",
            defaultextension=".db",
            initialfile=src.name,
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not dest:
            return
        try:
            shutil.copy2(src, dest)
        except Exception as exc:
            messagebox.showerror("Экспорт", f"Не удалось сохранить копию: {exc}")
            return
        messagebox.showinfo("Экспорт", "Копия базы успешно сохранена")

    def _merge_db(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите файл базы для слияния",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            refs, orders = merge_from_file(CONFIG.db_path, path)
        except Exception as exc:
            messagebox.showerror("Слияние", f"Не удалось выполнить слияние: {exc}")
            return
        messagebox.showinfo("Слияние", f"Готово. Обновлено справочников: {refs}, добавлено нарядов: {orders}")