import tkinter as tk
from tkinter import messagebox, filedialog, BooleanVar, ttk
import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import threading
from openpyxl import Workbook
import sys
import queue
from datetime import datetime
import requests
import subprocess

class TermexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ТЕРКОН")
        self.root.geometry("1300x800")
        self.stop_auto_update = False
        self.data_count_checked = False
        self.connecting_to_new_port = False

        self.font_size = 16

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["TIME", "R1", "R2", "T1", "T2"])

        self.current_version = "1.0"  # Текущая версия

        # Создание вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Главный экран
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Главный экран")

        # Панель с разделителем
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=15)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Фрейм для отображения данных
        self.data_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.data_frame, minsize=400)

        self.data_label = tk.Label(self.data_frame, text="Данные:", font=("Helvetica", self.font_size))
        self.data_label.pack(side=tk.TOP, anchor='w', padx=30, pady=5)

        self.data_display = tk.Text(self.data_frame, state='disabled', height=10, width=70, font=("Helvetica", self.font_size))
        self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=5)

        # Фрейм для выбора COM-порта
        self.port_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.port_frame, minsize=200)

        self.port_label = tk.Label(self.port_frame, text="COM-порт:", font=("Helvetica", self.font_size))
        self.port_label.pack(side=tk.TOP, anchor='w', padx=5, pady=5)

        self.port_listbox = tk.Listbox(self.port_frame, width=20, height=10, font=("Helvetica", self.font_size))
        self.port_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.port_listbox.bind('<Double-1>', self.connect_to_device)

        self.scrollbar = ttk.Scrollbar(self.data_frame, command=self.data_display.yview)
        self.scrollbar.place(x=1, y=5, relheight=1.0)
        self.data_display.config(yscrollcommand=self.scrollbar.set)

        # Фрейм для кнопок
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.create_file_button = ttk.Button(self.button_frame, text="Создать файл для сохранения", command=self.create_file, style="TButton")
        self.create_file_button.pack(side=tk.LEFT, padx=5)

        self.start_record_button = ttk.Button(self.button_frame, text="Начать запись", command=self.start_recording, style="TButton")
        self.start_record_button.pack(side=tk.LEFT, padx=5)

        self.stop_record_button = ttk.Button(self.button_frame, text="Закончить запись", command=self.stop_recording, style="TButton")
        self.stop_record_button.pack(side=tk.LEFT, padx=5)
        self.stop_record_button.config(state='disabled')

        self.disconnect_button = ttk.Button(self.button_frame, text="Отключиться от порта", command=self.disconnect_from_device, style="TButton")
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.update_port_button = ttk.Button(self.button_frame, text="Обновить порты", command=self.update_port_list, style="TButton")
        self.update_port_button.pack(side=tk.LEFT, padx=5)

        # Фрейм для графика
        self.plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="График")

        self.serial_port = None
        self.start_time = None
        self.file_path = None
        self.data_r1 = []
        self.data_r2 = []
        self.data_t1 = []
        self.data_t2 = []
        self.is_recording = False
        self.read_data_thread = None
        self.update_plot_thread = None
        self.attempts = 0
        self.max_attempts = 3

        self.times_r1 = []
        self.values_r1 = []
        self.times_r2 = []
        self.values_r2 = []
        self.times_t1 = []
        self.values_t1 = []
        self.times_t2 = []
        self.values_t2 = []

        self.show_r1 = BooleanVar(value=True)
        self.show_r2 = BooleanVar(value=True)
        self.show_t1 = BooleanVar(value=True)
        self.show_t2 = BooleanVar(value=True)

        self.r1_checkbox = ttk.Checkbutton(self.plot_frame, text="Показать 1R", variable=self.show_r1, command=self.update_plot, style="TCheckbutton")
        self.r1_checkbox.pack(anchor="se")

        self.r2_checkbox = ttk.Checkbutton(self.plot_frame, text="Показать 2R", variable=self.show_r2, command=self.update_plot, style="TCheckbutton")
        self.r2_checkbox.pack(anchor="se")

        self.t1_checkbox = ttk.Checkbutton(self.plot_frame, text="Показать T1", variable=self.show_t1, command=self.update_plot, style="TCheckbutton")
        self.t1_checkbox.pack(anchor="se")

        self.t2_checkbox = ttk.Checkbutton(self.plot_frame, text="Показать T2", variable=self.show_t2, command=self.update_plot, style="TCheckbutton")
        self.t2_checkbox.pack(anchor="se")

        self.open_plot_window()

        # Фрейм для настроек
        self.setting_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.setting_frame, text="Настройки")

        self.language_var = tk.StringVar(value="Ru")
        self.language_menu = ttk.OptionMenu(self.setting_frame, self.language_var, "Ru", "Ru", "En", command=self.change_language)
        self.language_menu.pack(side=tk.TOP, anchor='e', padx=10, pady=10)

        self.a1_label = ttk.Label(self.setting_frame, text="a (1R):", font=("Helvetica", self.font_size))
        self.a1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.a1_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size), width=10)
        self.a1_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.a1_entry.insert(0, "3.96868e-3")
        self.a1_entry.bind("<FocusOut>", self.check_developer_code)
        self.a1_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.b1_label = ttk.Label(self.setting_frame, text="b (1R):", font=("Helvetica", self.font_size))
        self.b1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.b1_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size))
        self.b1_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.b1_entry.insert(0, "-5.802e-7")
        self.b1_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.scale1_label = ttk.Label(self.setting_frame, text="scale1 (1R):", font=("Helvetica", self.font_size))
        self.scale1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.scale1_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size))
        self.scale1_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.scale1_entry.insert(0, "1000")
        self.scale1_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.a2_label = ttk.Label(self.setting_frame, text="a (2R):", font=("Helvetica", self.font_size))
        self.a2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.a2_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size))
        self.a2_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.a2_entry.insert(0, "3.96868e-3")
        self.a2_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.b2_label = ttk.Label(self.setting_frame, text="b (2R):", font=("Helvetica", self.font_size))
        self.b2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.b2_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size))
        self.b2_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.b2_entry.insert(0, "-5.802e-7")
        self.b2_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.scale2_label = ttk.Label(self.setting_frame, text="scale2 (2R):", font=("Helvetica", self.font_size))
        self.scale2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.scale2_entry = ttk.Entry(self.setting_frame, font=("Helvetica", self.font_size))
        self.scale2_entry.pack(side=tk.TOP, anchor='w', padx=10)
        self.scale2_entry.insert(0, "1000")
        self.scale2_entry.bind("<KeyRelease>", self.adjust_entry_width)

        self.save_settings_button = ttk.Button(self.setting_frame, text="Сохранить значения", command=self.save_settings, style="TButton")
        self.save_settings_button.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        self.reset_settings_button = ttk.Button(self.setting_frame, text="Вернуть настройки по умолчанию", command=self.reset_settings, style="TButton")
        self.reset_settings_button.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        self.save_temperature = BooleanVar(value=False)
        self.save_temperature_checkbox = ttk.Checkbutton(self.setting_frame, text="Сохранять температуру в файл", variable=self.save_temperature, style="TCheckbutton")
        self.save_temperature_checkbox.pack(anchor="w", padx=10, pady=10)

        self.a1 = 3.96868e-3
        self.b1 = -5.802e-7
        self.scale1 = 1000
        self.a2 = 3.96868e-3
        self.b2 = -5.802e-7
        self.scale2 = 1000

        self.temperature_label = ttk.Label(self.main_frame, text="T1: 0.00, T2: 0.00", font=("Helvetica", self.font_size))
        self.temperature_label.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)

        self.read_line_mode = BooleanVar(value=False)

        self.cursor_label = ttk.Label(self.plot_frame, text="", font=("Helvetica", self.font_size))
        self.cursor_label.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)

        self.recording_indicator = tk.Label(self.main_frame, text="●", font=("Helvetica", self.font_size), fg="red")
        self.recording_indicator.pack(side=tk.BOTTOM, anchor='e', padx=10, pady=10)
        self.recording_indicator.pack_forget()

        # Кнопка для проверки обновлений
        self.check_update_button = ttk.Button(self.setting_frame, text="Проверить обновление", command=self.check_for_updates, style="TButton")
        self.check_update_button.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        # Фрейм для помощи
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="Помощь")

        self.help_label = ttk.Label(self.help_frame, text="Раздел помощи", font=("Helvetica", self.font_size))
        self.help_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        self.help_text = tk.Text(self.help_frame, state='disabled', height=20, width=80, font=("Helvetica", self.font_size))
        self.help_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        help_content = """
        Основные функции:
        - Подключение к COM-порту
        - Запись данных в Excel файл
        - Отображение данных в реальном времени на графике
        - Настройка параметров для расчета температуры

        Инструкции:
        1. Выберите COM-порт из списка и подключитесь к нему.
        2. Создайте файл для сохранения данных.
        3. Нажмите "Начать запись" для начала сбора данных.
        4. Нажмите "Закончить запись" для остановки сбора данных.
        5. Настройте параметры a, b и scale1 для обоих каналов в разделе "Настройки".
        6. Включите или отключите отображение кривых на графике с помощью чекбоксов.

        Подробные инструкции:
        - Подключение к COM-порту:
          Выберите COM-порт из списка доступных портов и дважды щелкните по нему.
          Приложение подключится к выбранному порту и начнет получать данные.

        - Запись данных:
          Для начала записи данных нажмите кнопку "Начать запись".
          Данные будут сохраняться в выбранный файл. Для остановки записи нажмите кнопку "Закончить запись".

        - Отображение данных на графике:
          Данные будут отображаться на графике в реальном времени.
          Вы можете включить или отключить отображение кривых с помощью чекбоксов.

        - Настройка параметров:
          В разделе "Настройки" вы можете настроить параметры a, b и scale1 для обоих каналов.
          Эти параметры используются для расчета температуры.

        - Сохранение данных:
          Данные сохраняются в Excel файл.
          Вы можете создать файл для сохранения данных, нажав кнопку "Создать файл".

        Контакты разработчика:
        Telegram: @Abob_TGm
        """
        self.help_text.config(state='normal')
        self.help_text.insert(tk.END, help_content)
        self.help_text.config(state='disabled')

        self.translations = {
            "Ru": {
                "title": "ТЕРКОН",
                "main_tab": "Главный экран",
                "plot_tab": "График",
                "settings_tab": "Настройки",
                "help_tab": "Помощь",
                "data_label": "Данные:",
                "port_label": "COM-порт:",
                "create_button": "Создать файл",
                "start_button": "Начать запись",
                "stop_button": "Закончить запись",
                "disconnect_button": "Отключиться от порта",
                "update_port_button": "Обновить порты",
                "a1_label": "a (1R):",
                "b1_label": "b (1R):",
                "scale1_label": "scale1 (1R):",
                "a2_label": "a (2R):",
                "b2_label": "b (2R):",
                "scale2_label": "scale2 (2R):",
                "save_settings_button": "Сохранить значения",
                "reset_settings_button": "Вернуть настройки по умолчанию",
                "save_temperature_checkbox": "Сохранять температуру в файл",
                "temperature_label": "T1: 0.00, T2: 0.00",
                "help_label": "Раздел помощи",
                "help_content": help_content,
                "show_r1": "Показать 1R",
                "show_r2": "Показать 2R",
                "show_t1": "Показать T1",
                "show_t2": "Показать T2",
                "clear_plot_button": "Очистить график",
                "update_plot_button": "Обновить график",
                "check_update_button": "Проверить обновление"
            },
            "En": {
                "title": "TERKON",
                "main_tab": "Main Screen",
                "plot_tab": "Plot",
                "settings_tab": "Settings",
                "help_tab": "Help",
                "data_label": "Data:",
                "port_label": "COM Port:",
                "create_button": "Create File",
                "start_button": "Start Recording",
                "stop_button": "Stop Recording",
                "disconnect_button": "Disconnect from Port",
                "update_port_button": "Update Ports",
                "a1_label": "a (1R):",
                "b1_label": "b (1R):",
                "scale1_label": "scale1 (1R):",
                "a2_label": "a (2R):",
                "b2_label": "b (2R):",
                "scale2_label": "scale2 (2R):",
                "save_settings_button": "Save Values",
                "reset_settings_button": "Reset to Default",
                "save_temperature_checkbox": "Save Temperature to File",
                "temperature_label": "T1: 0.00, T2: 0.00",
                "help_label": "Help Section",
                "help_content": """
                    Main functions:
                    - Connect to COM port
                    - Save data to Excel file
                    - Display data in real-time on a graph
                    - Adjust parameters for temperature calculation

                    Instructions:
                    1. Select a COM port from the list and connect to it.
                    2. Create a file to save the data.
                    3. Click "Start Recording" to begin data collection.
                    4. Click "Stop Recording" to stop data collection.
                    5. Adjust the parameters a, b, and scale1 for both channels in the "Settings" section.
                    6. Enable or disable the display of curves on the graph using the checkboxes.

                    Detailed Instructions:
                    - Connecting to COM Port:
                      Select a COM port from the list of available ports and double-click it.
                      The application will connect to the selected port and start receiving data.

                    - Recording Data:
                      To start recording data, click the "Start Recording" button.
                      Data will be saved to the selected file. To stop recording, click the "Stop Recording" button.

                    - Displaying Data on the Graph:
                      Data will be displayed on the graph in real-time.
                      You can enable or disable the display of curves using the checkboxes.

                    - Adjusting Parameters:
                      In the "Settings" section, you can adjust the parameters a, b, and scale1 for both channels.
                      These parameters are used for temperature calculation.

                    - Saving Data:
                      Data is saved to an Excel file.
                      You can create a file to save the data by clicking the "Create File" button.

                    Developer Contacts:
                    Telegram: @Abob_TGm
                    """,
                "show_r1": "Show 1R",
                "show_r2": "Show 2R",
                "show_t1": "Show T1",
                "show_t2": "Show T2",
                "clear_plot_button": "Clear Plot",
                "update_plot_button": "Update Plot",
                "check_update_button": "Check for Updates"
            }
        }

        self.notification_shown = False

        self.data_queue = queue.Queue()

        self.write_thread = None
        self.write_thread_running = False

        # Привязка клавиатурных событий
        self.root.bind("<Up>", self.focus_previous)
        self.root.bind("<Down>", self.focus_next)
        self.root.bind("<Left>", self.focus_previous_tab)
        self.root.bind("<Right>", self.focus_next_tab)
        self.root.bind("<Return>", self.activate_focused_widget)

    def change_language(self, *args):
        # Этот участок кода выполняет смену языка интерфейса
        language = self.language_var.get()
        translations = self.translations[language]

        self.root.title(translations["title"])
        self.notebook.tab(self.main_frame, text=translations["main_tab"])
        self.notebook.tab(self.plot_frame, text=translations["plot_tab"])
        self.notebook.tab(self.setting_frame, text=translations["settings_tab"])
        self.notebook.tab(self.help_frame, text=translations["help_tab"])

        self.data_label.config(text=translations["data_label"])
        self.port_label.config(text=translations["port_label"])
        self.create_file_button.config(text=translations["create_button"])
        self.start_record_button.config(text=translations["start_button"])
        self.stop_record_button.config(text=translations["stop_button"])
        self.disconnect_button.config(text=translations["disconnect_button"])
        self.update_port_button.config(text=translations["update_port_button"])

        self.a1_label.config(text=translations["a1_label"])
        self.b1_label.config(text=translations["b1_label"])
        self.scale1_label.config(text=translations["scale1_label"])
        self.a2_label.config(text=translations["a2_label"])
        self.b2_label.config(text=translations["b2_label"])
        self.scale2_label.config(text=translations["scale2_label"])
        self.save_settings_button.config(text=translations["save_settings_button"])
        self.reset_settings_button.config(text=translations["reset_settings_button"])
        self.save_temperature_checkbox.config(text=translations["save_temperature_checkbox"])
        self.temperature_label.config(text=translations["temperature_label"])
        self.help_label.config(text=translations["help_label"])

        self.help_text.config(state='normal')
        self.help_text.delete(1.0, tk.END)
        self.help_text.insert(tk.END, translations["help_content"])
        self.help_text.config(state='disabled')

        self.r1_checkbox.config(text=translations["show_r1"])
        self.r2_checkbox.config(text=translations["show_r2"])
        self.t1_checkbox.config(text=translations["show_t1"])
        self.t2_checkbox.config(text=translations["show_t2"])

        self.clear_plot_button.config(text=translations["clear_plot_button"])
        self.update_plot_button.config(text=translations["update_plot_button"])
        self.check_update_button.config(text=translations["check_update_button"])

    def adjust_entry_width(self, event):
        # Этот участок кода выполняет изменение ширины поля ввода в зависимости от длины текста
        entry = event.widget
        text_length = len(entry.get())
        entry.config(width=text_length + 2)

    def check_developer_code(self, event):
        # Этот участок кода выполняет проверку кода разработчика
        if self.a1_entry.get() == "HELLO_WORLD":
            self.show_developer_settings()

    def show_developer_settings(self):
        # Этот участок кода выполняет отображение настроек разработчика
        if not hasattr(self, 'developer_frame'):
            self.developer_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.developer_frame, text="Настройки разработчика")

            self.read_line_checkbox = ttk.Checkbutton(self.developer_frame, text="Читать строку, а не 14 байт",
                                                      variable=self.read_line_mode, style="TCheckbutton")
            self.read_line_checkbox.pack(anchor="w", padx=10, pady=10)

            self.console_label = ttk.Label(self.developer_frame, text="Консоль:", font=("Helvetica", self.font_size))
            self.console_label.pack(anchor="w", padx=10, pady=10)

            self.console_output = tk.Text(self.developer_frame, state='disabled', height=10, width=80,
                                          font=("Helvetica", self.font_size))
            self.console_output.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

            sys.stdout = self.ConsoleRedirector(self.console_output)

            self.exit_developer_button = ttk.Button(self.developer_frame, text="Выйти из настроек разработчика",
                                                    command=self.hide_developer_settings, style="TButton")
            self.exit_developer_button.pack(anchor="w", padx=10, pady=10)

    def hide_developer_settings(self):
        # Этот участок кода выполняет скрытие настроек разработчика
        if hasattr(self, 'developer_frame'):
            self.notebook.forget(self.developer_frame)
            del self.developer_frame

    def update_plot_thread(self):
        # Этот участок кода выполняет обновление графика в отдельном потоке
        while self.serial_port and self.serial_port.is_open:
            self.update_plot()
            time.sleep(0.1)

    def update_port_list(self):
        # Этот участок кода выполняет обновление списка COM-портов
        self.port_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_listbox.insert(tk.END, port.device)

    def connect_to_device(self, event):
        # Этот участок кода выполняет подключение к устройству через COM-порт
        if self.serial_port and self.serial_port.is_open:
            if messagebox.askokcancel("Подтверждение", "Все данные на графике будут удалены. Продолжить?"):
                self.connecting_to_new_port = True
                self.disconnect_from_device()

        selected_port = self.port_listbox.get(self.port_listbox.curselection())
        try:
            if messagebox.askokcancel("Подтверждение", "Все данные на графике будут удалены. Продолжить?"):
                self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                self.data_display.config(state='normal')
                self.data_display.insert(tk.END, "Успешно подключено к " + selected_port + "\n")
                self.data_display.config(state='disabled')
                self.start_time = time.time()

                # Проверка на наличие активных потоков и их завершение
                if self.read_data_thread and self.read_data_thread.is_alive():
                    self.read_data_thread.join(timeout=1)
                if self.update_plot_thread and self.update_plot_thread.is_alive():
                    self.update_plot_thread.join(timeout=1)

                self.read_data_thread = threading.Thread(target=self.read_data)
                self.read_data_thread.daemon = True
                self.read_data_thread.start()

                self.update_plot_thread = threading.Thread(target=self.update_plot_thread)
                self.update_plot_thread.daemon = True
                self.update_plot_thread.start()

                self.stop_reading = False

        except serial.SerialException as e:
            messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))

    def disconnect_from_device(self):
        # Этот участок кода выполняет отключение от устройства
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Отключено от порта\n")
            self.data_display.config(state='disabled')

            if self.read_data_thread and self.read_data_thread.is_alive():
                self.read_data_thread.join(timeout=1)
            if self.update_plot_thread and self.update_plot_thread.is_alive():
                self.update_plot_thread.join(timeout=1)

            if self.connecting_to_new_port:
                self.clear_data()
                self.connecting_to_new_port = False

    def clear_data(self):
        # Этот участок кода выполняет очистку данных
        self.data_r1 = []
        self.data_r2 = []
        self.data_t1 = []
        self.data_t2 = []
        self.times_r1 = []
        self.values_r1 = []
        self.times_r2 = []
        self.values_r2 = []
        self.times_t1 = []
        self.values_t1 = []
        self.times_t2 = []
        self.values_t2 = []

    def clear_plot(self):
        # Этот участок кода выполняет очистку графика
        if messagebox.askokcancel("Подтверждение", "Все данные на графике будут удалены. Продолжить?"):
            self.ax.clear()
            self.ax.set_xlabel('Время (секунды)', fontsize=self.font_size)
            self.ax.set_ylabel('Значение', fontsize=self.font_size)
            self.ax.set_title('График данных', fontsize=self.font_size)
            self.ax.grid(True)
            self.line_r1, = self.ax.plot([], [], label='R1')
            self.line_r2, = self.ax.plot([], [], label='R2')
            self.line_t1, = self.ax.plot([], [], label='T1')
            self.line_t2, = self.ax.plot([], [], label='T2')
            self.ax.legend(fontsize=self.font_size)
            self.canvas.draw()

    def read_data(self):
        # Этот участок кода выполняет чтение данных с устройства
        self.serial_port.dtr = True
        self.serial_port.rts = False

        while self.serial_port and self.serial_port.is_open:
            try:
                if self.read_line_mode.get():
                    data = self.serial_port.readline().decode('utf-8').strip()
                else:
                    data = self.serial_port.read(14).decode('utf-8').strip()

                current_time = time.time() - self.start_time
                formatted_data = f"{current_time:.2f} - {data}"
                self.root.after(0, self.update_data_display, formatted_data)

                if self.is_recording and self.file_path:
                    self.data_queue.put(formatted_data)

                if '1R' not in data and '2R' not in data:
                    self.attempts += 1
                    if self.attempts >= self.max_attempts:
                        self.root.after(0, self.show_error_message, "Неверный тип данных. Ожидаются данные типа R.")
                        self.disconnect_from_device()
                        return
                    continue
                else:
                    self.attempts = 0

                r1_value = None
                r2_value = None
                temperature_r1 = None
                temperature_r2 = None
                r1_index = data.find('1R')
                r2_index = data.find('2R')

                if r1_index != -1:
                    r1_str = data[r1_index + 2:]
                    r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
                    r1_value_str = r1_str[:r1_end_index]
                    try:
                        r1_value = float(r1_value_str)
                        temperature_r1 = self.calculate_temperature(r1_value, self.a1, self.b1, self.scale1)
                    except ValueError:
                        self.root.after(0, self.show_error_message, f"Ошибка парсинга данных R1: {r1_value_str}")

                if r2_index != -1:
                    r2_str = data[r2_index + 2:]
                    r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
                    r2_value_str = r2_str[:r2_end_index]
                    try:
                        r2_value = float(r2_value_str)
                        temperature_r2 = self.calculate_temperature(r2_value, self.a2, self.b2, self.scale2)
                    except ValueError:
                        self.root.after(0, self.show_error_message, f"Ошибка парсинга данных R2: {r2_value_str}")

                if r1_value is not None:
                    self.data_r1.append((current_time, r1_value))
                    self.data_t1.append((current_time, temperature_r1))
                    self.update_temperature_label(temperature_r1, None)

                if r2_value is not None:
                    self.data_r2.append((current_time, r2_value))
                    self.data_t2.append((current_time, temperature_r2))
                    self.update_temperature_label(None, temperature_r2)

                if not self.data_count_checked:
                    self.root.after(0, self.check_data_count)
                    self.data_count_checked = True

                if not self.stop_auto_update:
                    self.update_plot()

                # Вывод в консоль разраба
                current_time_str = datetime.now().strftime("%H:%M:%S")
                print(f"{current_time_str} - Received data: {data}")
                if r1_value is not None:
                    print(f"{current_time_str} - Parsed R1 value: {r1_value}")
                if r2_value is not None:
                    print(f"{current_time_str} - Parsed R2 value: {r2_value}")
                if temperature_r1 is not None:
                    print(f"{current_time_str} - Calculated T1 value: {temperature_r1}")
                if temperature_r2 is not None:
                    print(f"{current_time_str} - Calculated T2 value: {temperature_r2}")

            except serial.SerialException as e:
                self.root.after(0, self.show_error_message, "Ошибка чтения данных: " + str(e))
                exit()
            except ValueError as e:
                self.root.after(0, self.show_error_message, "Ошибка парсинга данных: " + str(e))
                exit()
            time.sleep(0.1)

    def check_data_count(self):
        # Этот участок кода выполняет проверку количества данных для отображения на графике
        if len(self.data_r1) + len(self.data_r2) + len(self.data_t1) + len(self.data_t2) > 250:
            if not self.notification_shown:
                messagebox.showinfo("Информация",
                                    "Динамическое обновление графика приостановлено, чтобы обновить график нужно нажать кнопку 'Обновить график'(рекомендуется выполнить обновление графика после отключения от порта)")
                self.notification_shown = True
            self.stop_auto_update = True
            self.update_plot_button.config(state='normal')
        else:
            self.stop_auto_update = False
            self.update_plot_button.config(state='disabled')
        self.data_count_checked = False

    def update_plot(self):
        # Этот участок кода выполняет обновление графика
        if self.stop_auto_update:
            return

        if not self.data_r1 and not self.data_r2 and not self.data_t1 and not self.data_t2:
            messagebox.showinfo("Информация", "Нет данных для отображения на графике.")
            return

        times_r1 = [entry[0] for entry in self.data_r1 if isinstance(entry[1], (int, float))]
        values_r1 = [entry[1] for entry in self.data_r1 if isinstance(entry[1], (int, float))]
        times_r2 = [entry[0] for entry in self.data_r2 if isinstance(entry[1], (int, float))]
        values_r2 = [entry[1] for entry in self.data_r2 if isinstance(entry[1], (int, float))]
        times_t1 = [entry[0] for entry in self.data_t1 if isinstance(entry[1], (int, float))]
        values_t1 = [entry[1] for entry in self.data_t1 if isinstance(entry[1], (int, float))]
        times_t2 = [entry[0] for entry in self.data_t2 if isinstance(entry[1], (int, float))]
        values_t2 = [entry[1] for entry in self.data_t2 if isinstance(entry[1], (int, float))]

        if self.show_r1.get():
            self.line_r1.set_xdata(times_r1)
            self.line_r1.set_ydata(values_r1)
        else:
            self.line_r1.set_xdata([])
            self.line_r1.set_ydata([])

        if self.show_r2.get():
            self.line_r2.set_xdata(times_r2)
            self.line_r2.set_ydata(values_r2)
        else:
            self.line_r2.set_xdata([])
            self.line_r2.set_ydata([])

        if self.show_t1.get():
            self.line_t1.set_xdata(times_t1)
            self.line_t1.set_ydata(values_t1)
        else:
            self.line_t1.set_xdata([])
            self.line_t1.set_ydata([])

        if self.show_t2.get():
            self.line_t2.set_xdata(times_t2)
            self.line_t2.set_ydata(values_t2)
        else:
            self.line_t2.set_xdata([])
            self.line_t2.set_ydata([])

        all_times = times_r1 + times_r2 + times_t1 + times_t2
        all_values = []

        if self.show_r1.get():
            all_values.extend(values_r1)
        if self.show_r2.get():
            all_values.extend(values_r2)
        if self.show_t1.get():
            all_values.extend(values_t1)
        if self.show_t2.get():
            all_values.extend(values_t2)

        if all_times:
            max_time = max(all_times)
            if all_values:
                max_value = max(all_values)
                min_value = min(all_values)
                self.ax.set_xlim(left=0, right=max_time + 20)
                self.ax.set_ylim(bottom=min_value - min_value * 0.01,
                                 top=max_value + max_value * 0.01)
            else:
                self.ax.set_xlim(left=0, right=20)
                self.ax.set_ylim(bottom=0.00001, top=20)
        else:
            self.ax.set_xlim(left=0, right=20)
            self.ax.set_ylim(bottom=0.00001, top=20)

        self.canvas.draw()

    def update_data_display(self, data):
        # Этот участок кода выполняет обновление отображения данных
        self.data_display.config(state='normal')
        self.data_display.insert(tk.END, data + "\n")
        self.data_display.config(state='disabled')
        self.data_display.see(tk.END)

    def write_to_file(self):
        # Этот участок кода выполняет запись данных в файл
        while self.write_thread_running:
            try:
                data = self.data_queue.get()

                current_time = time.time() - self.start_time

                r1_value = None
                r2_value = None
                t1_value = None
                t2_value = None
                r1_index = data.find('1R')
                r2_index = data.find('2R')

                if r1_index != -1:
                    r1_str = data[r1_index + 2:]
                    r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
                    r1_value_str = r1_str[:r1_end_index]
                    try:
                        r1_value = float(r1_value_str.replace(',', '.'))
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R1: {r1_value_str}")

                if r2_index != -1:
                    r2_str = data[r2_index + 2:]
                    r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
                    r2_value_str = r2_str[:r2_end_index]
                    try:
                        r2_value = float(r2_value_str.replace(',', '.'))
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R2: {r2_value_str}")

                if self.save_temperature.get():
                    if r1_value is not None:
                        t1_value = self.calculate_temperature(r1_value, self.a1, self.b1, self.scale1)
                    if r2_value is not None:
                        t2_value = self.calculate_temperature(r2_value, self.a2, self.b2, self.scale2)

                self.ws.append([f"{current_time:.6f}".replace(',', '.'),
                                f"{r1_value:.6f}".replace(',', '.') if r1_value is not None else '',
                                f"{r2_value:.6f}".replace(',', '.') if r2_value is not None else '',
                                f"{t1_value:.6f}".replace(',', '.') if t1_value is not None else '',
                                f"{t2_value:.6f}".replace(',', '.') if t2_value is not None else ''])
                self.wb.save(self.file_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка записи данных в файл: {str(e)}")

    def create_file(self):
        # Этот участок кода выполняет создание файла для сохранения данных
        self.file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if self.file_path:
            messagebox.showinfo("Информация", f"Файл для сохранения данных создан: {self.file_path}")

    def start_recording(self):
        # Этот участок кода выполняет начало записи данных
        if not self.file_path:
            messagebox.showerror("Ошибка", "Сначала создайте файл для сохранения данных.")
            return
        if not self.is_recording:
            self.is_recording = True
            self.start_record_button.config(state='disabled')
            self.stop_record_button.config(state='normal')
            messagebox.showinfo("Информация", "Запись данных начата.")
            self.recording_indicator.pack()
            self.blink_indicator()

            self.write_thread_running = True
            self.write_thread = threading.Thread(target=self.write_to_file)
            self.write_thread.daemon = True
            self.write_thread.start()

    def stop_recording(self):
        # Этот участок кода выполняет остановку записи данных
        if not self.file_path:
            messagebox.showerror("Ошибка", "Сначала создайте файл для сохранения данных.")
            return
        if self.is_recording:
            self.is_recording = False
            self.start_record_button.config(state='normal')
            self.stop_record_button.config(state='disabled')
            messagebox.showinfo("Информация", "Запись данных завершена.")
            self.recording_indicator.pack_forget()

            self.write_thread_running = False
            if self.write_thread and self.write_thread.is_alive():
                self.write_thread.join(timeout=1)

    def open_plot_window(self):
        # Этот участок кода выполняет открытие окна с графиком
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Время (секунды)', fontsize=self.font_size)
        self.ax.set_ylabel('Значение', fontsize=self.font_size)
        self.ax.set_title('График данных', fontsize=self.font_size)
        self.ax.grid(True)

        self.line_r1, = self.ax.plot([], [], label='R1')
        self.line_r2, = self.ax.plot([], [], label='R2')
        self.line_t1, = self.ax.plot([], [], label='T1')
        self.line_t2, = self.ax.plot([], [], label='T2')

        self.ax.legend(fontsize=self.font_size)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_ylim(bottom=0.00001, top=9999)
        self.ax.set_xlim(left=0)

        self.canvas.mpl_connect('scroll_event', self.on_mouse_wheel)

        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        self.clear_plot_button = ttk.Button(self.plot_frame, text="Очистить график", command=self.clear_plot,
                                             style="TButton")
        self.clear_plot_button.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)

        self.update_plot_button = ttk.Button(self.plot_frame, text="Обновить график", command=self.update_plot,
                                              style="TButton")
        self.update_plot_button.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)
        self.update_plot_button.config(state='disabled')

    def on_mouse_wheel(self, event):
        # Этот участок кода выполняет масштабирование графика при прокрутке колеса мыши
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        scale_factor = 1.1 if event.button == 'up' else 0.9
        new_xlim = (current_xlim[0] * scale_factor, current_xlim[1] * scale_factor)
        new_ylim = (current_ylim[0] * scale_factor, current_ylim[1] * scale_factor)

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw()

    def on_mouse_move(self, event):
        # Этот участок кода выполняет обновление координат курсора на графике
        if event.inaxes:
            x, y = event.xdata, event.ydata
            self.update_cursor_label(x, y)

    def update_cursor_label(self, x, y):
        # Этот участок кода выполняет обновление метки курсора на графике
        self.cursor_label.config(text=f"X: {x:.2f}, Y: {y:.2f}")

    def save_settings(self):
        # Этот участок кода выполняет сохранение настроек
        try:
            a1_value = self.a1_entry.get().strip()
            b1_value = self.b1_entry.get().strip()
            scale1_value = self.scale1_entry.get().strip()
            a2_value = self.a2_entry.get().strip()
            b2_value = self.b2_entry.get().strip()
            scale2_value = self.scale2_entry.get().strip()

            if not a1_value or not b1_value or not scale1_value or not a2_value or not b2_value or not scale2_value:
                raise ValueError("Одно или несколько полей пусты.")

            self.a1 = float(a1_value)
            self.b1 = float(b1_value)
            self.scale1 = float(scale1_value)
            self.a2 = float(a2_value)
            self.b2 = float(b2_value)
            self.scale2 = float(scale2_value)

            messagebox.showinfo("Информация", "Значения сохранены.")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных. {str(e)}")

    def reset_settings(self):
        # Этот участок кода выполняет сброс настроек к значениям по умолчанию
        self.a1_entry.delete(0, tk.END)
        self.a1_entry.insert(0, "3.96868e-3")
        self.b1_entry.delete(0, tk.END)
        self.b1_entry.insert(0, "-5.802e-7")
        self.scale1_entry.delete(0, tk.END)
        self.scale1_entry.insert(0, "1000")
        self.a2_entry.delete(0, tk.END)
        self.a2_entry.insert(0, "3.96868e-3")
        self.b2_entry.delete(0, tk.END)
        self.b2_entry.insert(0, "-5.802e-7")
        self.scale2_entry.delete(0, tk.END)
        self.scale2_entry.insert(0, "1000")
        messagebox.showinfo("Информация", "Значения сброшены к значениям по умолчанию.")

    def calculate_temperature(self, R, a, b, scale):
        # Этот участок кода выполняет расчет температуры
        if not isinstance(R, (int, float)) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not isinstance(scale, (int, float)):
            raise ValueError("Все параметры должны быть числовыми значениями.")
        return (-a + (a**2 - 4 * b * (1 - R / scale))**0.5) / (2 * b)

    def update_temperature_label(self, t1=None, t2=None):
        # Этот участок кода выполняет обновление метки температуры
        current_t1 = self.temperature_label.cget("text").split("T1: ")[1].split(", T2: ")[0]
        current_t2 = self.temperature_label.cget("text").split("T2: ")[1]

        if t1 is not None and isinstance(t1, (int, float)):
            current_t1 = f"{t1:.2f}"
        if t2 is not None and isinstance(t2, (int, float)):
            current_t2 = f"{t2:.2f}"

        self.temperature_label.config(text=f"T1: {current_t1}, T2: {current_t2}")

    class ConsoleRedirector:
        # Этот класс выполняет перенаправление вывода консоли в текстовое поле
        def __init__(self, text_widget):
            self.text_widget = text_widget

        def write(self, msg):
            self.text_widget.config(state='normal')
            self.text_widget.insert(tk.END, msg)
            self.text_widget.config(state='disabled')
            self.text_widget.see(tk.END)

        def flush(self):
            pass

    def blink_indicator(self):
        # Этот участок кода выполняет мигание индикатора записи
        if self.is_recording:
            self.recording_indicator.config(fg="red" if self.recording_indicator.cget("fg") == "gray" else "gray")
            self.root.after(500, self.blink_indicator)

    def show_error_message(self, message):
        # Этот участок кода выполняет отображение сообщения об ошибке
        messagebox.showerror("Ошибка", message)

    def focus_previous(self, event):
        # Этот участок кода выполняет переход фокуса на предыдущий элемент
        self.root.event_generate("<Tab>")

    def focus_next(self, event):
        # Этот участок кода выполняет переход фокуса на следующий элемент
        self.root.event_generate("<Shift-Tab>")

    def focus_previous_tab(self, event):
        # Этот участок кода выполняет переход на предыдущую вкладку
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab > 0:
            self.notebook.select(current_tab - 1)

    def focus_next_tab(self, event):
        # Этот участок кода выполняет переход на следующую вкладку
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab < self.notebook.index(tk.END) - 1:
            self.notebook.select(current_tab + 1)

    def activate_focused_widget(self, event):
        # Этот участок кода выполняет активацию фокусированного виджета
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, ttk.Button):
            focused_widget.invoke()

    def check_for_updates(self):
        # Этот участок кода выполняет проверку обновлений
        threading.Thread(target=self.perform_update_check).start()

    def perform_update_check(self):
        # Этот участок кода выполняет проверку обновлений в отдельном потоке
        update_available, download_url = check_for_updates(self.current_version)
        if update_available:
            self.show_update_notification(download_url)

    def show_update_notification(self, download_url):
        # Этот участок кода выполняет отображение уведомления об обновлении
        if messagebox.askyesno("Обновление доступно", "Доступна новая версия. Хотите обновить?"):
            download_path = "path/to/installer.exe"
            if download_update(download_url, download_path):
                install_update(download_path)

def check_for_updates(current_version):
    # Этот участок кода выполняет проверку наличия новых версий на GitHub
    url = "https://github.com/ElMakgit/Terkon/blob/main/pythonProject/version.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        latest_version_info = response.json()
        latest_version = latest_version_info.get("version")
        download_url = latest_version_info.get("download_url")

        if latest_version > current_version:
            return True, download_url
        else:
            return False, None
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")
        return False, None

def download_update(download_url, download_path):
    # Этот участок кода выполняет скачивание новой версии с GitHub
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"Error downloading update: {e}")
        return False

def install_update(installer_path):
    # Этот участок кода выполняет установку новой версии
    try:
        subprocess.Popen([sys.executable, installer_path])
        sys.exit()
    except Exception as e:
        print(f"Error installing update: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TermexApp(root)

    def on_closing():
        # Этот участок кода выполняет закрытие приложения
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            if app.serial_port and app.serial_port.is_open:
                app.serial_port.close()
            if app.read_data_thread and app.read_data_thread.is_alive():
                app.read_data_thread.join(timeout=1)
            if app.update_plot_thread and app.update_plot_thread.is_alive():
                app.update_plot_thread.join(timeout=1)
            root.destroy()
            sys.exit()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
