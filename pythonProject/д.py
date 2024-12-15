import tkinter as tk
import customtkinter as ctk
from pywinstyles import apply_style
import serial
import serial.tools.list_ports
import time
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import threading
import csv

class TermexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ТЕРКОН")
        self.root.geometry("1300x800")

        # Увеличиваем размер шрифта
        self.font_size = 14

        # Создаем вкладки
        self.notebook = ctk.CTkTabview(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Главный экран
        self.main_frame = self.notebook.add("Главный экран")

        # Создаем панель для разделения окон
        self.paned_window = ctk.CTkPanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=15)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Левая панель для данных
        self.data_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(self.data_frame, minsize=500)  # Меняем минимальный размер

        self.data_label = ctk.CTkLabel(self.data_frame, text="Данные:", font=("Helvetica", self.font_size))
        self.data_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        self.data_display = ctk.CTkTextbox(self.data_frame, state='disabled', height=15, width=80, font=("Helvetica", self.font_size))
        self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Правая панель для портов
        self.port_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(self.port_frame, minsize=150)  # Меняем минимальный размер

        self.port_label = ctk.CTkLabel(self.port_frame, text="COM-порт:", font=("Helvetica", self.font_size))
        self.port_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        self.port_listbox = ctk.CTkListbox(self.port_frame, width=30, height=15, font=("Helvetica", self.font_size))
        self.port_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.port_listbox.bind('<Double-1>', self.connect_to_device)

        # Создаем фрейм для кнопок
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.save_button = ctk.CTkButton(self.button_frame, text="Выбрать файл для сохранения", command=self.choose_file, font=("Helvetica", self.font_size))
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.start_record_button = ctk.CTkButton(self.button_frame, text="Начать запись", command=self.start_recording, font=("Helvetica", self.font_size))
        self.start_record_button.pack(side=tk.LEFT, padx=5)

        self.stop_record_button = ctk.CTkButton(self.button_frame, text="Закончить запись", command=self.stop_recording, font=("Helvetica", self.font_size))
        self.stop_record_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = ctk.CTkButton(self.button_frame, text="Отключиться от порта", command=self.disconnect_from_device, font=("Helvetica", self.font_size))
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.update_port_button = ctk.CTkButton(self.button_frame, text="Обновить порты", command=self.update_port_list, font=("Helvetica", self.font_size))
        self.update_port_button.pack(side=tk.LEFT, padx=5)

        # Вкладка для графика
        self.plot_frame = self.notebook.add("График")

        self.serial_port = None
        self.start_time = None
        self.file_path = None
        self.data_r1 = []
        self.data_r2 = []
        self.is_recording = False
        self.read_data_thread = None
        self.attempts = 0
        self.max_attempts = 3  # Максимальное количество попыток

        # Initialize plot variables
        self.times_r1 = []
        self.values_r1 = []
        self.times_r2 = []
        self.values_r2 = []

        # Чекбоксы для включения и отключения кривых
        self.show_r1 = tk.BooleanVar(value=True)
        self.show_r2 = tk.BooleanVar(value=True)

        self.r1_checkbox = ctk.CTkCheckBox(self.plot_frame, text="Показать 1R", variable=self.show_r1, command=self.update_plot, font=("Helvetica", self.font_size))
        self.r1_checkbox.pack(anchor="se")

        self.r2_checkbox = ctk.CTkCheckBox(self.plot_frame, text="Показать 2R", variable=self.show_r2, command=self.update_plot, font=("Helvetica", self.font_size))
        self.r2_checkbox.pack(anchor="se")

        self.open_plot_window()

        # Вкладка для настроек
        self.setting_frame = self.notebook.add("Настройки")

        # Параметры для 1R
        self.a1_label = ctk.CTkLabel(self.setting_frame, text="a (1R):", font=("Helvetica", self.font_size))
        self.a1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.a1_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.a1_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.b1_label = ctk.CTkLabel(self.setting_frame, text="b (1R):", font=("Helvetica", self.font_size))
        self.b1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.b1_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.b1_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.scale1_label = ctk.CTkLabel(self.setting_frame, text="scale1 (1R):", font=("Helvetica", self.font_size))
        self.scale1_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.scale1_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.scale1_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Параметры для 2R
        self.a2_label = ctk.CTkLabel(self.setting_frame, text="a (2R):", font=("Helvetica", self.font_size))
        self.a2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.a2_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.a2_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.b2_label = ctk.CTkLabel(self.setting_frame, text="b (2R):", font=("Helvetica", self.font_size))
        self.b2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.b2_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.b2_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.scale2_label = ctk.CTkLabel(self.setting_frame, text="scale2 (2R):", font=("Helvetica", self.font_size))
        self.scale2_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)
        self.scale2_entry = ctk.CTkEntry(self.setting_frame, font=("Helvetica", self.font_size))
        self.scale2_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.save_settings_button = ctk.CTkButton(self.setting_frame, text="Сохранить значения", command=self.save_settings, font=("Helvetica", self.font_size))
        self.save_settings_button.pack(side=tk.TOP, padx=10, pady=10)

        # Инициализация параметров
        self.a1 = 3.96868e-3
        self.b1 = -5.802e-7
        self.scale1 = 1000
        self.a2 = 3.96868e-3
        self.b2 = -5.802e-7
        self.scale2 = 1000

        # Строка для отображения значений t1 и t2
        self.temperature_label = ctk.CTkLabel(self.main_frame, text="T1: 0.00, T2: 0.00", font=("Helvetica", self.font_size))
        self.temperature_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

        # Применение стиля с помощью PyWinStyles
        apply_style(self.root, style="dark")

    def update_plot(self):
        """Обновляет график данных в реальном времени."""
        print("Обновление графика")  # Отладочное сообщение
        times_r1 = [entry[0] for entry in self.data_r1]
        values_r1 = [entry[1] for entry in self.data_r1]
        times_r2 = [entry[0] for entry in self.data_r2]
        values_r2 = [entry[1] for entry in self.data_r2]
        print(f"Данные R1: {times_r1}, {values_r1}")  # Отладочное сообщение
        print(f"Данные R2: {times_r2}, {values_r2}")  # Отладочное сообщение

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

        # Обновление пределов осей
        if times_r1 and times_r2:
            max_time = max(max(times_r1), max(times_r2))
            max_value = max(max(values_r1), max(values_r2))
            self.ax.set_xlim(left=0, right=max_time + 20)  # Увеличиваем масштаб в два раза
            self.ax.set_ylim(bottom=0.00001, top=max_value + 200)  # Увеличиваем масштаб в два раза
        else:
            self.ax.set_xlim(left=0, right=20)  # Начальные значения для осей
            self.ax.set_ylim(bottom=0.00001, top=20)

        self.canvas.draw()

    def update_plot_thread(self):
        """Обновляет график данных в реальном времени в отдельном потоке."""
        while self.serial_port and self.serial_port.is_open:
            self.update_plot()
            time.sleep(0.1)  # Пауза между обновлениями графика

    def update_port_list(self):
        """Обновляет список доступных COM-портов."""
        self.port_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_listbox.insert(tk.END, port.device)

    def connect_to_device(self, event):
        """Подключается к выбранному COM-порту."""
        selected_port = self.port_listbox.get(self.port_listbox.curselection())
        try:
            self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Успешно подключено к " + selected_port + "\n")
            self.data_display.config(state='disabled')
            self.start_time = time.time()  # Запоминаем время начала записи
            self.read_data_thread = threading.Thread(target=self.read_data)
            self.read_data_thread.daemon = True
            self.read_data_thread.start()

            # Запуск потока для обновления графика
            self.update_plot_thread = threading.Thread(target=self.update_plot_thread)
            self.update_plot_thread.daemon = True
            self.update_plot_thread.start()

        except serial.SerialException as e:
            messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))

    def disconnect_from_device(self):
        """Отключается от текущего COM-порта."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Отключено от порта\n")
            self.data_display.config(state='disabled')
            if self.read_data_thread and self.read_data_thread.is_alive():
                self.read_data_thread.join(timeout=1)
            if self.update_plot_thread and self.update_plot_thread.is_alive():
                self.update_plot_thread.join(timeout=1)

    def read_data(self):
        print("функция работает")
        self.serial_port.dtr = True
        self.serial_port.rts = False

        """Читает данные из COM-порта и обновляет отображение данных и график."""
        while self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.read(14).decode('utf-8').strip()
                print("Это чтение с порта: ", data)
                current_time = time.time() - self.start_time  # Текущее время с начала записи
                formatted_data = f"{current_time:.2f} - {data}"
                self.root.after(0, self.update_data_display, formatted_data)

                if self.is_recording and self.file_path:
                    self.write_to_file(formatted_data)

                # Парсинг данных
                if '1R' not in data and '2R' not in data:
                    self.attempts += 1
                    if self.attempts >= self.max_attempts:
                        messagebox.showerror("Ошибка", "Неверный тип данных. Ожидаются данные типа R.")
                        self.disconnect_from_device()
                        return
                    continue
                else:
                    self.attempts = 0  # Сброс счетчика попыток при успешном получении данных

                r1_value = None
                r2_value = None
                r1_index = data.find('1R')
                r2_index = data.find('2R')

                if r1_index != -1:
                    r1_str = data[r1_index + 2:]  # Берем строку, начиная с символа после '1R'
                    r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
                    r1_value_str = r1_str[:r1_end_index]
                    try:
                        r1_value = float(r1_value_str)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R1: {r1_value_str}")

                if r2_index != -1:
                    r2_str = data[r2_index + 2:]  # Берем строку, начиная с символа после '2R'
                    r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
                    r2_value_str = r2_str[:r2_end_index]
                    try:
                        r2_value = float(r2_value_str)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R2: {r2_value_str}")

                if r1_value is not None:
                    temperature_r1 = self.calculate_temperature(r1_value, self.a1, self.b1, self.scale1)
                    self.data_r1.append((current_time, temperature_r1))
                    print(f"Добавлено значение R1: {current_time}, {temperature_r1}")  # Отладочное сообщение
                    self.update_temperature_label(temperature_r1, None)

                if r2_value is not None:
                    temperature_r2 = self.calculate_temperature(r2_value, self.a2, self.b2, self.scale2)
                    self.data_r2.append((current_time, temperature_r2))
                    print(f"Добавлено значение R2: {current_time}, {temperature_r2}")  # Отладочное сообщение
                    self.update_temperature_label(None, temperature_r2)

            except serial.SerialException as e:
                messagebox.showerror("Ошибка", "Ошибка чтения данных: " + str(e))
            except ValueError as e:
                messagebox.showerror("Ошибка", "Ошибка парсинга данных: " + str(e))
            time.sleep(0.1)  # Пауза между чтениями данных

    def update_data_display(self, data):
        """Обновляет отображение данных в текстовом поле."""
        self.data_display.config(state='normal')
        self.data_display.insert(tk.END, data + "\n")
        self.data_display.config(state='disabled')
        self.data_display.see(tk.END)

    def write_to_file(self, data):
        """Записывает данные в CSV файл."""
        try:
            with open(self.file_path, "a", newline='') as file:
                writer = csv.writer(file, delimiter=',')
                current_time = time.time() - self.start_time  # Текущее время с начала записи

                r1_value = None
                r2_value = None
                r1_index = data.find('1R')
                r2_index = data.find('2R')

                if r1_index != -1:
                    r1_str = data[r1_index + 2:]  # Берем строку, начиная с символа после '1R'
                    r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
                    r1_value_str = r1_str[:r1_end_index]
                    try:
                        r1_value = float(r1_value_str)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R1: {r1_value_str}")

                if r2_index != -1:
                    r2_str = data[r2_index + 2:]  # Берем строку, начиная с символа после '2R'
                    r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
                    r2_value_str = r2_str[:r2_end_index]
                    try:
                        r2_value = float(r2_value_str)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Ошибка парсинга данных R2: {r2_value_str}")

                # Записываем данные в три колонки: время, R1, R2
                writer.writerow([current_time, r1_value if r1_value is not None else '',
                                 r2_value if r2_value is not None else ''])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка записи данных в файл: {str(e)}")

    def choose_file(self):
        """Открывает диалоговое окно для выбора файла для сохранения данных."""
        self.file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if self.file_path:
            messagebox.showinfo("Информация", f"Файл для сохранения данных выбран: {self.file_path}")

    def start_recording(self):
        """Начинает запись данных."""
        if not self.is_recording:
            self.is_recording = True
            messagebox.showinfo("Информация", "Запись данных начата.")

    def stop_recording(self):
        """Завершает запись данных."""
        if self.is_recording:
            self.is_recording = False
            messagebox.showinfo("Информация", "Запись данных завершена.")

    def open_plot_window(self):
        """Открывает окно для отображения графика данных."""
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Время (секунды)', fontsize=self.font_size)
        self.ax.set_ylabel('Значение', fontsize=self.font_size)
        self.ax.set_title('График данных', fontsize=self.font_size)
        self.ax.grid(True)  # Добавление сетки

        self.line_r1, = self.ax.plot(self.times_r1, self.values_r1, label='R1')
        self.line_r2, = self.ax.plot(self.times_r2, self.values_r2, label='R2')

        self.ax.legend(fontsize=self.font_size)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_ylim(bottom=0.00001, top=9999)
        self.ax.set_xlim(left=0)

    def close_app(self):
        """Закрывает приложение, закрывая все потоки и порты."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.read_data_thread and self.read_data_thread.is_alive():
            self.read_data_thread.join(timeout=1)
        self.root.destroy()

    def save_settings(self):
        """Сохраняет значения параметров a, b и scale1 для обоих каналов."""
        try:
            self.a1 = float(self.a1_entry.get())
            self.b1 = float(self.b1_entry.get())
            self.scale1 = float(self.scale1_entry.get())
            self.a2 = float(self.a2_entry.get())
            self.b2 = float(self.b2_entry.get())
            self.scale2 = float(self.scale2_entry.get())
            messagebox.showinfo("Информация", "Значения сохранены.")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат данных. Введите числовые значения.")

    def calculate_temperature(self, R, a, b, scale):
        """Вычисляет температуру на основе сопротивления и параметров."""
        return (-a + (a**2 - 4 * b * (1 - R / scale))**0.5) / (2 * b)

    def update_temperature_label(self, t1=None, t2=None):
        """Обновляет отображение значений температуры t1 и t2."""
        current_t1 = self.temperature_label.cget("text").split("T1: ")[1].split(", T2: ")[0]
        current_t2 = self.temperature_label.cget("text").split("T2: ")[1]

        if t1 is not None:
            current_t1 = f"{t1:.2f}"
        if t2 is not None:
            current_t2 = f"{t2:.2f}"

        self.temperature_label.config(text=f"T1: {current_t1}, T2: {current_t2}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = TermexApp(root)

    def on_closing():
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
