from __future__ import annotations

import customtkinter as ctk
from utils.runtime_mode import AppMode, set_mode


class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Режим работы")
        self.geometry("360x160")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Выберите режим работы:").pack(pady=(14, 10))
        btns = ctk.CTkFrame(self)
        btns.pack(pady=6)

        ctk.CTkButton(btns, text="Полный доступ", command=lambda: self._choose(AppMode.FULL)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Только просмотр", command=lambda: self._choose(AppMode.READONLY)).pack(side="left", padx=6)

        ctk.CTkLabel(self, text="Для смены режима перезапустите программу.").pack(pady=(10, 8))

    def _choose(self, mode: AppMode) -> None:
        set_mode(mode)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


