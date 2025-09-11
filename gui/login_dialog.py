from __future__ import annotations

import customtkinter as ctk
from utils.runtime_mode import AppMode, set_mode
import tkinter as tk
from tkinter import simpledialog, messagebox
from utils.security import verify_user_password, verify_admin_password, save_user_password, user_password_is_set


class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Режим работы")
        self.geometry("440x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Выберите режим работы:").pack(pady=(16, 12))
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=6)

        btn_width = 180
        ctk.CTkButton(btns, text="Полный доступ", width=btn_width, command=lambda: self._choose(AppMode.FULL)).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Только просмотр", width=btn_width, command=lambda: self._choose(AppMode.READONLY)).pack(side="left", padx=8)
        # Подсказка и кнопка админа внизу (кнопка под надписью)
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(14, 8))
        ctk.CTkLabel(bottom, text="Пароль админа М@2").pack(anchor="center")
        ctk.CTkButton(bottom, text="Режим админа", width=btn_width, command=self._admin_flow).pack(anchor="center", pady=(8, 0))

    def _choose(self, mode: AppMode) -> None:
        if mode == AppMode.READONLY:
            set_mode(mode)
            try:
                self.grab_release()
            except Exception:
                pass
            self.destroy()
            return
        # Полный доступ
        # Если пользовательский пароль ещё НЕ установлен — предложить установить его сейчас
        if not user_password_is_set():
            if messagebox.askyesno("Пароль", "Пользовательский пароль не установлен. Установить сейчас?", parent=self):
                if self._set_user_password_new():
                    set_mode(AppMode.FULL)
                    try:
                        self.grab_release()
                    except Exception:
                        pass
                    self.destroy()
                    return
            # Если отказались или установка не удалась — запустить в режиме просмотра
            messagebox.showwarning("Режим", "Пароль не установлен. Запуск в режиме 'Просмотр'.", parent=self)
            set_mode(AppMode.READONLY)
            try:
                self.grab_release()
            except Exception:
                pass
            self.destroy()
            return
        # Иначе: спросить пароль, до 3 попыток
        attempts = 0
        granted = False
        is_admin_login = False
        while attempts < 3 and not granted:
            attempts += 1
            pw = simpledialog.askstring("Пароль", f"Введите пароль (попытка {attempts} из 3):", parent=self, show="*")
            if pw is None:
                # Отмена — сразу в просмотр
                break
            # Разрешаем вход только если пароль админа ИЛИ корректный установленный пользовательский пароль
            if verify_admin_password(pw):
                is_admin_login = True
                granted = True
                break
            if verify_user_password(pw):
                granted = True
                break
        if granted:
            # Предложить действия при админ-входе
            try:
                if is_admin_login and not user_password_is_set():
                    if messagebox.askyesno("Пароль", "Пользовательский пароль не установлен. Установить сейчас?", parent=self):
                        self._set_user_password_new()
                elif is_admin_login:
                    if messagebox.askyesno("Пароль", "Вход как администратор. Сменить пароль пользователя сейчас?", parent=self):
                        self._change_user_password()
            except Exception:
                pass
            set_mode(AppMode.FULL)
        else:
            messagebox.showwarning("Режим", "Пароль не подтверждён. Запуск в режиме 'Просмотр'.", parent=self)
            set_mode(AppMode.READONLY)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _change_user_password(self) -> None:
        # Требует действующего пароля пользователя или админа
        # 1) Проверка текущего
        cur = simpledialog.askstring("Смена пароля", "Введите текущий пароль:", parent=self, show="*")
        if cur is None:
            return
        if not (verify_user_password(cur) or verify_admin_password(cur)):
            messagebox.showerror("Смена пароля", "Текущий пароль неверен.", parent=self)
            return
        # 2) Новый дважды
        new1 = simpledialog.askstring("Смена пароля", "Введите новый пароль:", parent=self, show="*")
        if new1 is None or new1.strip() == "":
            return
        new2 = simpledialog.askstring("Смена пароля", "Повторите новый пароль:", parent=self, show="*")
        if new2 is None:
            return
        if new1 != new2:
            messagebox.showerror("Смена пароля", "Пароли не совпадают.", parent=self)
            return
        try:
            save_user_password(new1)
            messagebox.showinfo("Смена пароля", "Пароль сохранён.", parent=self)
        except Exception as exc:
            messagebox.showerror("Смена пароля", f"Ошибка сохранения: {exc}", parent=self)

    def _set_user_password_new(self) -> None:
        # Установка нового пользовательского пароля (без проверки старого)
        new1 = simpledialog.askstring("Установка пароля", "Введите новый пароль пользователя:", parent=self, show="*")
        if new1 is None or new1.strip() == "":
            return
        new2 = simpledialog.askstring("Установка пароля", "Повторите новый пароль пользователя:", parent=self, show="*")
        if new2 is None:
            return
        if new1 != new2:
            messagebox.showerror("Пароль", "Пароли не совпадают.", parent=self)
            return
        try:
            save_user_password(new1)
            messagebox.showinfo("Пароль", "Пароль пользователя установлен.", parent=self)
        except Exception as exc:
            messagebox.showerror("Пароль", f"Ошибка сохранения: {exc}", parent=self)

    def _admin_flow(self) -> None:
        # Вход в админ-режим: 3 попытки, иначе переход в просмотр
        attempts = 0
        while attempts < 3:
            attempts += 1
            pw = simpledialog.askstring("Режим администратора", f"Введите пароль администратора (попытка {attempts} из 3):", parent=self, show="*")
            if pw is None:
                return
            if verify_admin_password(pw):
                # Прямо открываем окно смены пароля пользователя без проверки текущего
                self._set_user_password_new()
                return
        # После трёх неудачных попыток
        ro = ctk.CTkToplevel(self)
        ro.title("Доступ ограничен")
        ro.geometry("420x140")
        ctk.CTkLabel(ro, text="Вы не можете вносить изменения в базу данных!").pack(pady=(16, 10))
        def _go_ro():
            set_mode(AppMode.READONLY)
            try:
                ro.destroy()
            except Exception:
                pass
        ctk.CTkButton(ro, text="Открыть программу в режиме просмотра.", command=_go_ro).pack(pady=(6, 10))


