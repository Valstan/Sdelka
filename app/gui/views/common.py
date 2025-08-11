from __future__ import annotations

import customtkinter as ctk


class BaseView(ctk.CTkFrame):  # pragma: no cover - GUI glue
    def __init__(self, master: ctk.CTkBaseClass | None = None) -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _add_section_title(self, text: str) -> None:
        label = ctk.CTkLabel(self, text=text, font=("Arial", 16, "bold"))
        label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))