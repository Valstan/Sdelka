import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import pandas as pd


class ReportPreview:
    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Фрейм для таблицы предпросмотра
        table_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Таблица для предпросмотра
        columns = ("worker", "date", "work_type", "quantity", "amount", "product", "contract")
        self.preview_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        # Настройка заголовков
        self.preview_table.heading("worker", text="Работник")
        self.preview_table.heading("date", text="Дата")
        self.preview_table.heading("work_type", text="Вид работы")
        self.preview_table.heading("quantity", text="Количество")
        self.preview_table.heading("amount", text="Сумма, руб.")
        self.preview_table.heading("product", text="Изделие")
        self.preview_table.heading("contract", text="Контракт")

        # Настройка ширин столбцов
        self.preview_table.column("worker", width=150)
        self.preview_table.column("date", width=100, anchor="center")
        self.preview_table.column("work_type", width=200)
        self.preview_table.column("quantity", width=100, anchor="center")
        self.preview_table.column("amount", width=100, anchor="e")
        self.preview_table.column("product", width=150)
        self.preview_table.column("contract", width=100)

        # Добавление прокрутки
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.preview_table.yview)
        self.preview_table.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.preview_table.xview)
        self.preview_table.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_table.pack(fill=tk.BOTH, expand=True)

    def preview(self, df: pd.DataFrame):
        # Очищаем таблицу
        for item in self.preview_table.get_children():
            self.preview_table.delete(item)

        # Заполняем таблицу данными
        for _, row in df.iterrows():
            self.preview_table.insert(
                "", "end",
                values=(
                    row['worker'],
                    row['date'],
                    row['work_type'],
                    row['quantity'],
                    f"{row['amount']:.2f}",
                    row['product'],
                    row['contract']
                )
            )
