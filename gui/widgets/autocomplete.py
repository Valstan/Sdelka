from __future__ import annotations

import customtkinter as ctk


class AutocompleteEntry(ctk.CTkFrame):
    def __init__(
        self, master, fetch_suggestions, placeholder: str = "", width: int = 250
    ):
        super().__init__(master)
        self.fetch_suggestions = fetch_suggestions  # callable(prefix)->list[(id,str)]

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=width)
        self.entry.pack(side="top", fill="x")

        self.listbox = ctk.CTkScrollableFrame(self, height=140)
        self.listbox.pack(side="top", fill="x")
        self.listbox.pack_forget()

        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", lambda e: self._hide_list())

    def get(self) -> str:
        return self.entry.get()

    def _on_key_release(self, event) -> None:
        text = self.entry.get().strip()
        if not text:
            self._hide_list()
            return
        results = self.fetch_suggestions(text)
        self._show_results(results)

    def _show_results(self, results):
        for w in self.listbox.winfo_children():
            w.destroy()
        if not results:
            self._hide_list()
            return
        self.listbox.pack(side="top", fill="x")
        for _id, label in results:
            btn = ctk.CTkButton(
                self.listbox, text=label, command=lambda val=label: self._select(val)
            )
            btn.pack(fill="x", pady=2)

    def _select(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        self._hide_list()

    def _hide_list(self) -> None:
        self.listbox.pack_forget()
