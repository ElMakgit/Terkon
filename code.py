
import tkinter as tk
from tkinter import messagebox, filedialog, BooleanVar, ttk
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
        self.root.title("Преобразователь сигналов ТС и ТП прецизионные ТЕРКОН")
        self.root.geometry("1000x600") #Increased window size for better plot visibility
        messagebox.showwarning("Внимание", "Программа создана ElMak")

        # Создаем вкладки
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Главный экран
        self.main_frame = tk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Главный экран")

        # Создаем панель для разделения окон
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=15)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Левая панель для данных
        self.data_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.data_frame, minsize=400)

        self.data_label = tk.Label(self.data_frame, text="Данные:")
        self.data_label.pack(side=tk.TOP, anchor='w', padx=5, pady=5)

        self.data_display = tk.Text(self.data_frame, state='disabled', height=10, width=70)
        self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Правая панель для портов
        self.port_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.port_frame, minsize=200)

        self.port_label = tk.Label(self.port_frame, text="COM-порт:")
        self.port_label.pack(side=tk.TOP, anchor='w', padx=5, pady=5)

        self.port_listbox = tk.Listbox(self.port_frame, width=20, height=10)
        self.port_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.port_listbox.bind('<Double-1>', self.connect_to_device)

        # Создаем фрейм для кнопок
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.save_button = tk.Button(self.button_frame, text="Выбрать файл для сохранения", command=self.choose_file)
        self.save_button.pack(side=tk.LEFT, padx=2)

        self.start_record_button = tk.Button(self.button_frame, text="Начать запись", command=self.start_recording)
        self.start_record_button.pack(side=tk.LEFT, padx=2)

        self.stop_record_button = tk.Button(self.button_frame, text="Закончить запись", command=self.stop_recording)
        self.stop_record_button.pack(side=tk.LEFT, padx=2)

        self.disconnect_button = tk.Button(self.button_frame, text="Отключиться от порта", command=self.disconnect_from_device)
        self.disconnect_button.pack(side=tk.LEFT, padx=2)

        self.update_port_button = tk.Button(self.button_frame, text="Обновить порты", command=self.update_port_list)
        self.update_port_button.pack(side=tk.LEFT, padx=2)

        # Галочки для выбора типа данных
        self.data_type_var = BooleanVar()
        self.data_type_r = tk.Radiobutton(self.main_frame, text="Тип данных R", variable=self.data_type_var, value=True, command=self.update_data_type)
        self.data_type_r.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
        self.data_type_c = tk.Radiobutton(self.main_frame, text="Тип данных C", variable=self.data_type_var, value=False, command=self.update_data_type)
        self.data_type_c.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
        self.data_type_var.set(True)  # По умолчанию выбран тип данных R

        # Вкладка для графика
        self.plot_frame = tk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="График")


        self.serial_port = None
        self.start_time = None
        self.start_time_str = None
        self.file_path = None
        self.data_r1 = []
        self.data_r2 = []
        self.data_c1 = []
        self.data_c2 = []
        self.is_recording = False
        self.read_data_thread = None
        self.data_type = 'R'  # По умолчанию тип данных R
        self.attempts = 0
        self.max_attempts = 3  # Максимальное количество попыток
        self.open_plot_window()
        self.plot_type = 'both' #default to show both plots

    def update_plot(self):
        """Обновляет график данных в реальном времени."""
        if self.data_type == 'R':
            times = [self.convert_time_to_seconds(entry[0]) for entry in self.data_r1]
            values_r1 = [entry[1] for entry in self.data_r1]
            values_r2 = [entry[1] for entry in self.data_r2]
            self.plot_data(times, values_r1, values_r2, 'R1', 'R2')
        elif self.data_type == 'C':
            times = [self.convert_time_to_seconds(entry[0]) for entry in self.data_c1]
            values_c1 = [entry[1] for entry in self.data_c1]
            values_c2 = [entry[1] for entry in self.data_c2]
            self.plot_data(times, values_c1, values_c2, 'C1', 'C2')

    def plot_data(self, times, values1, values2, label1, label2):
        self.ax.clear()
        self.ax.set_xlabel('Время (секунды)')
        self.ax.set_ylabel('Значение')
        self.ax.set_title('График данных')
        self.ax.grid(True)

        if self.plot_type == 'both' or self.plot_type == label1:
            self.ax.plot(times, values1, label=label1)
        if self.plot_type == 'both' or self.plot_type == label2:
            self.ax.plot(times, values2, label=label2)

        self.ax.legend()
        self.canvas.draw()


    def update_plot_thread(self):
        """Обновляет график данных в реальном времени в отдельном потоке."""
        while self.is_recording and self.serial_port and self.serial_port.is_open:
            self.update_plot()
            time.sleep(0.1)

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
            self.start_time_str = datetime.datetime.now().strftime(
                "%H:%M:%S.%f")  # Запоминаем время начала записи в строковом формате
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

    def update_data_type(self):
        """Обновляет тип данных на основе выбора пользователя."""
        if self.data_type_var.get():
            self.data_type = 'R'
        else:
            self.data_type = 'C'
        self.attempts = 0  # Сброс счетчика попыток при смене типа данных

    def read_data(self):
        """Читает данные из COM-порта и обновляет отображение данных и график."""
        while self.is_recording and self.serial_port and self.serial_port.is_open:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                if line:
                    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")
                    formatted_data = f"{current_time} - {line}"
                    self.root.after(0, self.update_data_display, formatted_data)

                    if self.file_path:
                        self.write_to_file(formatted_data)

                    if self.data_type == 'R':
                        self.parse_r_data(line, current_time)
                    elif self.data_type == 'C':
                        self.parse_c_data(line, current_time)

            except serial.SerialException as e:
                messagebox.showerror("Ошибка", f"Ошибка чтения данных: {e}")
                self.disconnect_from_device()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Непредвиденная ошибка: {e}")
                self.disconnect_from_device()
            time.sleep(0.1)

    def parse_r_data(self, line, current_time):
        parts = line.split()
        if len(parts) == 2:
            try:
                r1_value = float(parts[0])
                r2_value = float(parts[1])
                self.data_r1.append((current_time, r1_value))
                self.data_r2.append((current_time, r2_value))
            except ValueError:
                messagebox.showerror("Ошибка", "Ошибка преобразования данных R.")

    def parse_c_data(self, line, current_time):
        parts = line.split()
        if len(parts) == 2:
            try:
                c1_value = float(parts[0])
                c2_value = float(parts[1])
                self.data_c1.append((current_time, c1_value))
                self.data_c2.append((current_time, c2_value))
            except ValueError:
                messagebox.showerror("Ошибка", "Ошибка преобразования данных C.")

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
                current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")  # Текущее время с миллисекундами

                if self.data_type == 'R':
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

                    if r1_value is not None and r2_value is not None:
                        writer.writerow([current_time, r1_value, r2_value])

                elif self.data_type == 'C':
                    c1_value = None
                    c2_value = None
                    c1_index = data.find('1C')
                    c2_index = data.find('2C')

                    if c1_index != -1:
                        c1_str = data[c1_index + 2:]  # Берем строку, начиная с символа после '1C'
                        c1_end_index = c1_str.find(' ') if ' ' in c1_str else len(c1_str)
                        c1_value_str = c1_str[:c1_end_index]
                        try:
                            c1_value = float(c1_value_str)
                        except ValueError:
                            messagebox.showerror("Ошибка", f"Ошибка парсинга данных C1: {c1_value_str}")

                    if c2_index != -1:
                        c2_str = data[c2_index + 2:]  # Берем строку, начиная с символа после '2C'
                        c2_end_index = c2_str.find(' ') if ' ' in c2_str else len(c2_str)
                        c2_value_str = c2_str[:c2_end_index]
                        try:
                            c2_value = float(c2_value_str)
                        except ValueError:
                            messagebox.showerror("Ошибка", f"Ошибка парсинга данных C2: {c2_value_str}")

                    if c1_value is not None and c2_value is not None:
                        writer.writerow([current_time, c1_value, c2_value])
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
        self.ax.set_xlabel('Время (секунды)')
        self.ax.set_ylabel('Значение')
        self.ax.set_title('График данных')
        self.ax.grid(True)  # Добавление сетки

        plot_frame = tk.Frame(self.plot_frame)
        plot_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.show_r1_button = tk.Button(plot_frame, text="Показать R1", command=lambda: self.update_plot_type('R1'))
        self.show_r1_button.pack(side=tk.LEFT, padx=2)

        self.show_r2_button = tk.Button(plot_frame, text="Показать R2", command=lambda: self.update_plot_type('R2'))
        self.show_r2_button.pack(side=tk.LEFT, padx=2)

        self.show_both_button = tk.Button(plot_frame, text="Показать R1 и R2",
                                          command=lambda: self.update_plot_type('both'))
        self.show_both_button.pack(side=tk.LEFT, padx=2)

        if self.data_type == 'R':
            self.times_r1 = []
            self.values_r1 = []
            self.times_r2 = []
            self.values_r2 = []

            self.line_r1, = self.ax.plot(self.times_r1, self.values_r1, label='R1')
            self.line_r2, = self.ax.plot(self.times_r2, self.values_r2, label='R2')
        elif self.data_type == 'C':
            self.times_c1 = []
            self.values_c1 = []
            self.times_c2 = []
            self.values_c2 = []

            self.line_c1, = self.ax.plot(self.times_c1, self.values_c1, label='C1')
            self.line_c2, = self.ax.plot(self.times_c2, self.values_c2, label='C2')

        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_ylim(bottom=0.00001, top=9999)
        self.ax.set_xlim(left=0)

    def update_plot_type(self, plot_type):
        self.plot_type = plot_type
        self.update_plot()

    def convert_time_to_seconds(self, time_str):
        time_format = "%H:%M:%S.%f"
        time_obj = datetime.datetime.strptime(time_str, time_format)
        start_time_obj = datetime.datetime.strptime(self.start_time_str, time_format)
        delta = time_obj - start_time_obj
        return delta.total_seconds()

    def close_app(self):
        self.is_recording = False #Stop recording before closing
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.read_data_thread and self.read_data_thread.is_alive():
            self.read_data_thread.join(timeout=1)
        if self.update_plot_thread and self.update_plot_thread.is_alive():
            self.update_plot_thread.join(timeout=1)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TermexApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app) #Use app.close_app directly
    root.mainloop()

