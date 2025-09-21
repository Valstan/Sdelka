"""Диалог настройки Яндекс.Диска при проблемах с токеном"""

from __future__ import annotations

import customtkinter as ctk
import tkinter.messagebox as messagebox
import webbrowser
from utils.user_prefs import load_prefs, save_prefs


class YaDiskSetupDialog(ctk.CTkToplevel):
    """Диалог настройки Яндекс.Диска"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Настройка Яндекс.Диска")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Центрируем окно
        self.transient(parent)
        self.grab_set()
        
        if parent:
            parent.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 200
            self.geometry(f"500x400+{x}+{y}")
        
        self.result = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка интерфейса"""
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ Проблема с Яндекс.Диском",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#dc2626"
        )
        title_label.pack(pady=(10, 20))
        
        # Описание проблемы
        problem_text = """Не удалось подключиться к Яндекс.Диску для синхронизации данных.

Возможные причины:
• Токен авторизации недействителен или истек
• Нет доступа к интернету
• Проблемы с сервисом Яндекс.Диска

Что делать:"""
        
        problem_label = ctk.CTkLabel(
            main_frame,
            text=problem_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        problem_label.pack(pady=(0, 20), anchor="w")
        
        # Кнопки действий
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Получить новый токен
        get_token_btn = ctk.CTkButton(
            buttons_frame,
            text="🔑 Получить новый токен",
            command=self._get_new_token,
            width=200,
            height=40
        )
        get_token_btn.pack(pady=5)
        
        # Ввести токен вручную
        manual_token_btn = ctk.CTkButton(
            buttons_frame,
            text="📝 Ввести токен вручную",
            command=self._enter_token_manually,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        manual_token_btn.pack(pady=5)
        
        # Работать без синхронизации
        offline_btn = ctk.CTkButton(
            buttons_frame,
            text="💻 Работать без синхронизации",
            command=self._work_offline,
            width=200,
            height=40,
            fg_color="#7c3aed",
            hover_color="#5b21b6"
        )
        offline_btn.pack(pady=5)
        
        # Информация внизу
        info_label = ctk.CTkLabel(
            main_frame,
            text="При работе без синхронизации данные будут сохраняться только локально.",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        info_label.pack(pady=(10, 0))
        
    def _get_new_token(self):
        """Открыть страницу получения токена"""
        try:
            # Открываем страницу получения токена
            webbrowser.open("https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d")
            
            messagebox.showinfo(
                "Получение токена",
                """1. В открывшемся браузере войдите в свой аккаунт Яндекс
2. Разрешите доступ к Яндекс.Диску
3. Скопируйте токен из адресной строки (после access_token=)
4. Вернитесь в программу и нажмите "Ввести токен вручную" """,
                parent=self
            )
            
        except Exception as exc:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось открыть браузер: {exc}\n\nПерейдите вручную по ссылке:\nhttps://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d",
                parent=self
            )
    
    def _enter_token_manually(self):
        """Ввод токена вручную"""
        from tkinter import simpledialog
        
        token = simpledialog.askstring(
            "Токен Яндекс.Диска",
            "Введите токен доступа к Яндекс.Диску:",
            parent=self
        )
        
        if token and token.strip():
            # Сохраняем токен в настройках
            try:
                prefs = load_prefs()
                prefs.yandex_oauth_token = token.strip()
                save_prefs(prefs)
                
                messagebox.showinfo(
                    "Токен сохранен",
                    "Токен Яндекс.Диска сохранен в настройках.\nПрограмма попробует синхронизироваться при следующем запуске.",
                    parent=self
                )
                
                self.result = "token_saved"
                self.destroy()
                
            except Exception as exc:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось сохранить токен: {exc}",
                    parent=self
                )
    
    def _work_offline(self):
        """Работать без синхронизации"""
        self.result = "offline"
        self.destroy()
