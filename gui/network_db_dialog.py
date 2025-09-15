from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

from utils.network_db import NetworkDatabaseManager, test_network_connection
from utils.user_prefs import save_prefs, load_prefs


class NetworkDbDialog(ctk.CTkToplevel):
    """Диалог для настройки подключения к сетевой базе данных"""

    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Подключение к сетевой базе данных")
        self.geometry("500x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self._network_manager: NetworkDatabaseManager | None = None
        self._db_path: Path | None = None

        self._build_ui()
        self._test_connection()

    def _build_ui(self) -> None:
        # Заголовок
        ctk.CTkLabel(
            self,
            text="Автоматическое подключение к сетевой базе данных",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 10))

        # Сведения о сетевой папке (без раскрытия конфиденциальных данных)
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(info_frame, text="Подключение к защищенной сетевой папке...").pack(
            anchor="w", padx=10, pady=5
        )

        # Статус подключения
        self._status_label = ctk.CTkLabel(self, text="Проверка подключения...")
        self._status_label.pack(pady=10)

        # Кнопки
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=20, pady=20)

        self._retry_btn = ctk.CTkButton(
            buttons_frame, text="Повторить подключение", command=self._test_connection
        )
        self._retry_btn.pack(side="left", padx=5)

        self._manual_btn = ctk.CTkButton(
            buttons_frame, text="Указать путь вручную", command=self._manual_path
        )
        self._manual_btn.pack(side="left", padx=5)

        self._exit_btn = ctk.CTkButton(
            buttons_frame,
            text="Выход",
            command=self._exit_app,
            fg_color="#b91c1c",
            hover_color="#7f1d1d",
        )
        self._exit_btn.pack(side="right", padx=5)

    def _test_connection(self) -> None:
        """Тестирует подключение к сетевой БД"""
        self._status_label.configure(text="Подключение к сетевой папке...")
        self.update()

        try:
            # Создаем менеджер сетевого подключения
            self._network_manager = NetworkDatabaseManager(
                network_path=r"\\SRV3\sdelka",
                username="sdelka_user",
                password="87654321",
                db_filename="base_sdelka_rmz.db",
            )

            # Пытаемся подключиться
            self._db_path = self._network_manager.connect_to_network_db()

            if self._db_path and self._db_path.exists():
                # Тестируем подключение к БД
                if test_network_connection():
                    self._status_label.configure(
                        text="✓ Подключение успешно!", text_color="#16a34a"
                    )
                    self._retry_btn.configure(state="disabled")
                    self._manual_btn.configure(text="Использовать сетевую БД")
                else:
                    self._status_label.configure(
                        text="✗ БД недоступна или повреждена", text_color="#dc2626"
                    )
            else:
                self._status_label.configure(
                    text="✗ Не удалось подключиться к сетевой папке\nили файл БД не найден",
                    text_color="#dc2626",
                )

        except Exception:
            self._status_label.configure(
                text="✗ Ошибка подключения. Проверьте доступ к сети и права.",
                text_color="#dc2626",
            )

    def _manual_path(self) -> None:
        """Открывает диалог для ручного выбора пути к БД"""
        from tkinter import filedialog

        if self._db_path and self._db_path.exists():
            # Если сетевая БД доступна, используем её
            self._use_network_db()
            return

        # Иначе открываем диалог выбора файла
        path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[["SQLite DB", "*.db"], ["Все файлы", "*.*"]],
            initialdir=str(Path.cwd()),
        )

        if path:
            db_path = Path(path)
            if db_path.exists():
                self._save_db_path_and_exit(db_path)
            else:
                messagebox.showerror("Ошибка", "Выбранный файл не существует")

    def _use_network_db(self) -> None:
        """Использует сетевую БД"""
        if self._db_path:
            self._save_db_path_and_exit(self._db_path)

    def _save_db_path_and_exit(self, db_path: Path) -> None:
        """Сохраняет путь к БД и закрывает диалог"""
        try:
            prefs = load_prefs()
            prefs.db_path = str(db_path)
            save_prefs(prefs)

            messagebox.showinfo(
                "Настройка БД",
                "Параметры подключения сохранены. Приложение будет перезапущено.",
            )

            self.grab_release()
            self.destroy()

        except Exception:
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки.")

    def _exit_app(self) -> None:
        """Выход из приложения"""
        if self._network_manager:
            self._network_manager.disconnect_from_network()
        self.grab_release()
        self.destroy()

    def destroy(self) -> None:
        """Переопределяем destroy для отключения от сети"""
        if self._network_manager:
            self._network_manager.disconnect_from_network()
        super().destroy()
