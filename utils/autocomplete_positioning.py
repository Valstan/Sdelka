from __future__ import annotations

import customtkinter as ctk
from typing import Union, Callable, Any


def place_suggestions_under_entry(
    entry: ctk.CTkEntry,
    suggestions_frame: ctk.CTkFrame,
    master_widget: ctk.CTkFrame,
) -> None:
    try:
        # Обновляем геометрию
        try:
            entry.update_idletasks()
            suggestions_frame.update_idletasks()
        except Exception:
            pass

        # Текущий коэффициент масштабирования CustomTkinter
        try:
            scale = float(ctk.get_widget_scaling())
            if scale <= 0:
                scale = 1.0
        except Exception:
            scale = 1.0

        # Экранные координаты поля ввода (физические пиксели)
        ex = entry.winfo_rootx()
        ey = entry.winfo_rooty()
        ew = max(1, entry.winfo_width())
        eh = entry.winfo_height()

        # Используем корневое окно (как у календаря) в качестве системы координат
        try:
            host = suggestions_frame.winfo_toplevel()
            host.update_idletasks()
        except Exception:
            host = master_widget

        hx = host.winfo_rootx()
        hy = host.winfo_rooty()

        # Относительные координаты в корневом окне (физические пиксели)
        relx_px = ex - hx
        rely_px = (ey - hy) + eh

        # Контроль нижнего края экрана: если не влазит — поднять над полем
        screen_h = host.winfo_screenheight()
        sf_h_est_px = 200  # оценка предельной высоты в пикселях
        if (ey + eh + sf_h_est_px) > (screen_h - 2):
            rely_px = (ey - hy) - sf_h_est_px

        # Контроль правого края экрана
        screen_w = host.winfo_screenwidth()
        if (ex + ew) > (screen_w - 2):
            relx_px = (ex + ew) - hx - ew

        # Конвертируем физические пиксели в логические единицы CTk с учетом масштабирования
        relx = int(round(relx_px / scale))
        rely = int(round(rely_px / scale))
        width_units = int(round(ew / scale))

        # Ширина подсказок = ширине поля (в логических единицах)
        try:
            suggestions_frame.configure(width=width_units)
        except Exception:
            pass

        suggestions_frame.place(x=relx, y=rely)
        suggestions_frame.lift()
    except Exception as e:
        print(f"Ошибка позиционирования подсказок: {e}")
        try:
            suggestions_frame.place_forget()
            suggestions_frame.place(relx=0.5, rely=0.0, anchor="n")
            suggestions_frame.lift()
        except Exception:
            pass


def place_suggestions_under_widget(
    widget: Union[ctk.CTkEntry, ctk.CTkFrame],
    suggestions_frame: ctk.CTkFrame,
    master_widget: ctk.CTkFrame,
    offset_x: int = 0,
    offset_y: int = 0
) -> None:
    """
    Позиционирует фрейм с подсказками под указанным виджетом
    с возможностью смещения.

    Args:
        widget: Виджет, под которым нужно показать подсказки
        suggestions_frame: Фрейм с подсказками
        master_widget: Основной виджет-контейнер
        offset_x: Горизонтальное смещение
        offset_y: Вертикальное смещение
    """
    try:
        # Получаем координаты виджета
        widget_x = widget.winfo_rootx()
        widget_y = widget.winfo_rooty()
        widget_height = widget.winfo_height()

        # Получаем координаты основного виджета
        master_x = master_widget.winfo_rootx()
        master_y = master_widget.winfo_rooty()

        # Вычисляем относительные координаты
        relative_x = widget_x - master_x + offset_x
        relative_y = widget_y - master_y + widget_height + offset_y

        # Размещаем фрейм
        suggestions_frame.place(x=relative_x, y=relative_y)
        suggestions_frame.lift()

    except Exception as e:
        print(f"Ошибка позиционирования подсказок: {e}")
        # Fallback
        suggestions_frame.place(relx=0.5, rely=0.5, anchor="center")


def create_suggestion_button(
    parent: ctk.CTkFrame,
    text: str,
    command: Callable[[], Any],
    **kwargs
) -> ctk.CTkButton:
    """
    Создает унифицированную кнопку подсказки с единым стилем.

    Args:
        parent: Родительский виджет
        text: Текст кнопки
        command: Команда при нажатии
        **kwargs: Дополнительные параметры для кнопки

    Returns:
        Созданная кнопка подсказки
    """
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color="transparent",
        hover_color=("gray80", "gray25"),
        text_color=("black", "white"),  # Черные буквы на светлом фоне
        anchor="w",
        height=26,
        corner_radius=2,
        border_width=0,
        font=("Arial", 10),
        **kwargs
    )


def create_suggestions_frame(parent: ctk.CTkFrame) -> ctk.CTkFrame:
    """
    Создает унифицированный фрейм для подсказок с единым стилем.

    Родителем делаем корневое окно (toplevel), чтобы позиционирование было
    в экранных координатах и совпадало с логикой календаря.
    """
    try:
        host = parent.winfo_toplevel()
    except Exception:
        host = parent

    frame = ctk.CTkFrame(
        host,
        fg_color=("gray95", "gray10"),  # Светло-серый фон
        corner_radius=4,
        border_width=1,
        border_color=("gray70", "gray30"),
    )

    # Настройка размеров по умолчанию; ширина затем равняется ширине поля
    frame.configure(width=250, height=200)

    return frame
