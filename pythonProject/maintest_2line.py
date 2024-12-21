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

print(tk.Tcl().eval('info patchlevel'))
#
# class TermexApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Преобразователь сигналов ТС и ТП прецизионные ТЕРКОН")
#         self.root.geometry("800x600")
#         messagebox.showwarning("Внимание", "Программа создана ElMak")
#
#         # Создаем вкладки
#         self.notebook = ttk.Notebook(root)
#         self.notebook.pack(fill=tk.BOTH, expand=True)
#
#         # Главный экран
#         self.main_frame = tk.Frame(self.notebook)
#         self.notebook.add(self.main_frame, text="Главный экран")
#
#         # Создаем панель для разделения окон
#         self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=15)
#         self.paned_window.pack(fill=tk.BOTH, expand=True)
#
#         # Левая панель для данных
#         self.data_frame = tk.Frame(self.paned_window)
#         self.paned_window.add(self.data_frame, minsize=400)
#
#         self.data_label = tk.Label(self.data_frame, text="Данные:")
#         self.data_label.pack(side=tk.TOP, anchor='w', padx=5, pady=5)
#
#         self.data_display = tk.Text(self.data_frame, state='disabled', height=10, width=70)
#         self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
#
#         # Правая панель для портов
#         self.port_frame = tk.Frame(self.paned_window)
#         self.paned_window.add(self.port_frame, minsize=200)
#
#         self.port_label = tk.Label(self.port_frame, text="COM-порт:")
#         self.port_label.pack(side=tk.TOP, anchor='w', padx=5, pady=5)
#
#         self.port_listbox = tk.Listbox(self.port_frame, width=20, height=10)
#         self.port_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
#         self.port_listbox.bind('<Double-1>', self.connect_to_device)
#
#         # Создаем фрейм для кнопок
#         self.button_frame = tk.Frame(self.main_frame)
#         self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
#
#         self.save_button = tk.Button(self.button_frame, text="Выбрать файл для сохранения", command=self.choose_file)
#         self.save_button.pack(side=tk.LEFT, padx=2)
#
#         self.start_record_button = tk.Button(self.button_frame, text="Начать запись", command=self.start_recording)
#         self.start_record_button.pack(side=tk.LEFT, padx=2)
#
#         self.stop_record_button = tk.Button(self.button_frame, text="Закончить запись", command=self.stop_recording)
#         self.stop_record_button.pack(side=tk.LEFT, padx=2)
#
#         self.disconnect_button = tk.Button(self.button_frame, text="Отключиться от порта", command=self.disconnect_from_device)
#         self.disconnect_button.pack(side=tk.LEFT, padx=2)
#
#         self.update_port_button = tk.Button(self.button_frame, text="Обновить порты", command=self.update_port_list)
#         self.update_port_button.pack(side=tk.LEFT, padx=2)
#
#         # Галочки для выбора типа данных
#         self.data_type_var = BooleanVar()
#         self.data_type_r = tk.Radiobutton(self.main_frame, text="Тип данных R", variable=self.data_type_var, value=True, command=self.update_data_type)
#         self.data_type_r.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
#         self.data_type_c = tk.Radiobutton(self.main_frame, text="Тип данных C", variable=self.data_type_var, value=False, command=self.update_data_type)
#         self.data_type_c.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
#         self.data_type_var.set(True)  # По умолчанию выбран тип данных R
#
#         # Вкладка для графика
#         self.plot_frame = tk.Frame(self.notebook)
#         self.notebook.add(self.plot_frame, text="График")
#
#         self.serial_port = None
#         self.start_time = None
#         self.start_time_str = None
#         self.file_path = None
#         self.data_r1 = []
#         self.data_r2 = []
#         self.data_c1 = []
#         self.data_c2 = []
#         self.is_recording = False
#         self.read_data_thread = None
#         self.data_type = 'R'  # По умолчанию тип данных R
#         self.attempts = 0
#         self.max_attempts = 3  # Максимальное количество попыток
#
#         # Initialize plot variables
#         self.times_r1 = []
#         self.values_r1 = []
#         self.times_r2 = []
#         self.values_r2 = []
#         self.times_c1 = []
#         self.values_c1 = []
#         self.times_c2 = []
#         self.values_c2 = []
#
#         self.open_plot_window()
#
#     def update_plot(self):
#         """Обновляет график данных в реальном времени."""
#         print("Обновление графика")  # Отладочное сообщение
#         if self.data_type == 'R':
#             times_r1 = [self.convert_time_to_seconds(entry[0]) for entry in self.data_r1]
#             values_r1 = [entry[1] for entry in self.data_r1]
#             times_r2 = [self.convert_time_to_seconds(entry[0]) for entry in self.data_r2]
#             values_r2 = [entry[1] for entry in self.data_r2]
#             print(f"Данные R1: {times_r1}, {values_r1}")  # Отладочное сообщение
#             print(f"Данные R2: {times_r2}, {values_r2}")  # Отладочное сообщение
#             self.line_r1.set_xdata(times_r1)
#             self.line_r1.set_ydata(values_r1)
#             self.line_r2.set_xdata(times_r2)
#             self.line_r2.set_ydata(values_r2)
#         elif self.data_type == 'C':
#             times_c1 = [self.convert_time_to_seconds(entry[0]) for entry in self.data_c1]
#             values_c1 = [entry[1] for entry in self.data_c1]
#             times_c2 = [self.convert_time_to_seconds(entry[0]) for entry in self.data_c2]
#             values_c2 = [entry[1] for entry in self.data_c2]
#             print(f"Данные C1: {times_c1}, {values_c1}")  # Отладочное сообщение
#             print(f"Данные C2: {times_c2}, {values_c2}")  # Отладочное сообщение
#             self.line_c1.set_xdata(times_c1)
#             self.line_c1.set_ydata(values_c1)
#             self.line_c2.set_xdata(times_c2)
#             self.line_c2.set_ydata(values_c2)
#
#         # Обновление пределов осей
#         if self.data_type == 'R':
#             if times_r1 and times_r2:
#                 self.ax.set_xlim(left=0, right=max(max(times_r1), max(times_r2)))
#                 self.ax.set_ylim(bottom=0.00001, top=max(max(values_r1), max(values_r2)))
#             else:
#                 self.ax.set_xlim(left=0, right=10)  # Начальные значения для осей
#                 self.ax.set_ylim(bottom=0.00001, top=10)
#         elif self.data_type == 'C':
#             if times_c1 and times_c2:
#                 self.ax.set_xlim(left=0, right=max(max(times_c1), max(times_c2)))
#                 self.ax.set_ylim(bottom=0.00001, top=max(max(values_c1), max(values_c2)))
#             else:
#                 self.ax.set_xlim(left=0, right=10)  # Начальные значения для осей
#                 self.ax.set_ylim(bottom=0.00001, top=10)
#
#         self.canvas.draw()
#
#     def update_plot_thread(self):
#         """Обновляет график данных в реальном времени в отдельном потоке."""
#         while self.serial_port and self.serial_port.is_open:
#             self.update_plot()
#             time.sleep(0.1)  # Пауза между обновлениями графика
#
#     def update_port_list(self):
#         """Обновляет список доступных COM-портов."""
#         self.port_listbox.delete(0, tk.END)
#         ports = serial.tools.list_ports.comports()
#         for port in ports:
#             self.port_listbox.insert(tk.END, port.device)
#
#     def connect_to_device(self, event):
#         """Подключается к выбранному COM-порту."""
#         selected_port = self.port_listbox.get(self.port_listbox.curselection())
#         try:
#             self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
#             self.data_display.config(state='normal')
#             self.data_display.insert(tk.END, "Успешно подключено к " + selected_port + "\n")
#             self.data_display.config(state='disabled')
#             self.start_time = time.time()  # Запоминаем время начала записи
#             self.start_time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")  # Запоминаем время начала записи в строковом формате
#             self.read_data_thread = threading.Thread(target=self.read_data)
#             self.read_data_thread.daemon = True
#             self.read_data_thread.start()
#
#             # Запуск потока для обновления графика
#             self.update_plot_thread = threading.Thread(target=self.update_plot_thread)
#             self.update_plot_thread.daemon = True
#             self.update_plot_thread.start()
#
#         except serial.SerialException as e:
#             messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))
#
#     def disconnect_from_device(self):
#         """Отключается от текущего COM-порта."""
#         if self.serial_port and self.serial_port.is_open:
#             self.serial_port.close()
#             self.data_display.config(state='normal')
#             self.data_display.insert(tk.END, "Отключено от порта\n")
#             self.data_display.config(state='disabled')
#             if self.read_data_thread and self.read_data_thread.is_alive():
#                 self.read_data_thread.join(timeout=1)
#             if self.update_plot_thread and self.update_plot_thread.is_alive():
#                 self.update_plot_thread.join(timeout=1)
#
#     def update_data_type(self):
#         """Обновляет тип данных на основе выбора пользователя."""
#         if self.data_type_var.get():
#             self.data_type = 'R'
#         else:
#             self.data_type = 'C'
#         self.attempts = 0  # Сброс счетчика попыток при смене типа данных
#
#     def read_data(self):
#         print("функция работает")
#         self.serial_port.dtr = True
#         self.serial_port.rts = False
#
#         """Читает данные из COM-порта и обновляет отображение данных и график."""
#         while self.serial_port and self.serial_port.is_open:
#             try:
#                 data1 = self.serial_port.readline().decode('utf-8').strip()
#                 data2 = self.serial_port.readline().decode('utf-8').strip()
#                 print("Это чтение с порта: ", data1, data2)
#                 current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")  # Текущее время с миллисекундами
#                 formatted_data1 = f"{current_time} - {data1}"
#                 formatted_data2 = f"{current_time} - {data2}"
#                 self.root.after(0, self.update_data_display, formatted_data1)
#                 self.root.after(0, self.update_data_display, formatted_data2)
#
#                 if self.is_recording and self.file_path:
#                     self.write_to_file(formatted_data1)
#                     self.write_to_file(formatted_data2)
#
#                 # Парсинг данных
#                 if self.data_type == 'R':
#                     r1_value = None
#                     r2_value = None
#                     r1_index = data1.find('1R')
#                     r2_index = data2.find('2R')
#
#                     if r1_index != -1:
#                         r1_str = data1[r1_index + 2:]  # Берем строку, начиная с символа после '1R'
#                         r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
#                         r1_value_str = r1_str[:r1_end_index]
#                         try:
#                             r1_value = float(r1_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных R1: {r1_value_str}")
#
#                     if r2_index != -1:
#                         r2_str = data2[r2_index + 2:]  # Берем строку, начиная с символа после '2R'
#                         r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
#                         r2_value_str = r2_str[:r2_end_index]
#                         try:
#                             r2_value = float(r2_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных R2: {r2_value_str}")
#
#                     if r1_value is not None:
#                         self.data_r1.append((current_time, r1_value))
#                         print(f"Добавлено значение R1: {current_time}, {r1_value}")  # Отладочное сообщение
#                     if r2_value is not None:
#                         self.data_r2.append((current_time, r2_value))
#                         print(f"Добавлено значение R2: {current_time}, {r2_value}")  # Отладочное сообщение
#
#                 elif self.data_type == 'C':
#                     c1_value = None
#                     c2_value = None
#                     c1_index = data1.find('1C')
#                     c2_index = data2.find('2C')
#
#                     if c1_index != -1:
#                         c1_str = data1[c1_index + 2:]  # Берем строку, начиная с символа после '1C'
#                         c1_end_index = c1_str.find(' ') if ' ' in c1_str else len(c1_str)
#                         c1_value_str = c1_str[:c1_end_index]
#                         try:
#                             c1_value = float(c1_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных C1: {c1_value_str}")
#
#                     if c2_index != -1:
#                         c2_str = data2[c2_index + 2:]  # Берем строку, начиная с символа после '2C'
#                         c2_end_index = c2_str.find(' ') if ' ' in c2_str else len(c2_str)
#                         c2_value_str = c2_str[:c2_end_index]
#                         try:
#                             c2_value = float(c2_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных C2: {c2_value_str}")
#
#                     if c1_value is not None:
#                         self.data_c1.append((current_time, c1_value))
#                         print(f"Добавлено значение C1: {current_time}, {c1_value}")  # Отладочное сообщение
#                     if c2_value is not None:
#                         self.data_c2.append((current_time, c2_value))
#                         print(f"Добавлено значение C2: {current_time}, {c2_value}")  # Отладочное сообщение
#
#             except serial.SerialException as e:
#                 messagebox.showerror("Ошибка", "Ошибка чтения данных: " + str(e))
#             except ValueError as e:
#                 messagebox.showerror("Ошибка", "Ошибка парсинга данных: " + str(e))
#             time.sleep(0.1)  # Пауза между чтениями данных
#
#     def update_data_display(self, data):
#         """Обновляет отображение данных в текстовом поле."""
#         self.data_display.config(state='normal')
#         self.data_display.insert(tk.END, data + "\n")
#         self.data_display.config(state='disabled')
#         self.data_display.see(tk.END)
#
#     def write_to_file(self, data):
#         """Записывает данные в CSV файл."""
#         try:
#             with open(self.file_path, "a", newline='') as file:
#                 writer = csv.writer(file, delimiter=',')
#                 current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")  # Текущее время с миллисекундами
#
#                 if self.data_type == 'R':
#                     r1_value = None
#                     r2_value = None
#                     r1_index = data.find('1R')
#                     r2_index = data.find('2R')
#
#                     if r1_index != -1:
#                         r1_str = data[r1_index + 2:]  # Берем строку, начиная с символа после '1R'
#                         r1_end_index = r1_str.find(' ') if ' ' in r1_str else len(r1_str)
#                         r1_value_str = r1_str[:r1_end_index]
#                         try:
#                             r1_value = float(r1_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных R1: {r1_value_str}")
#
#                     if r2_index != -1:
#                         r2_str = data[r2_index + 2:]  # Берем строку, начиная с символа после '2R'
#                         r2_end_index = r2_str.find(' ') if ' ' in r2_str else len(r2_str)
#                         r2_value_str = r2_str[:r2_end_index]
#                         try:
#                             r2_value = float(r2_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных R2: {r2_value_str}")
#
#                     # Записываем данные в три колонки: время, R1, R2
#                     writer.writerow([current_time, r1_value if r1_value is not None else '',
#                                      r2_value if r2_value is not None else ''])
#
#                 elif self.data_type == 'C':
#                     c1_value = None
#                     c2_value = None
#                     c1_index = data.find('1C')
#                     c2_index = data.find('2C')
#
#                     if c1_index != -1:
#                         c1_str = data[c1_index + 2:]  # Берем строку, начиная с символа после '1C'
#                         c1_end_index = c1_str.find(' ') if ' ' in c1_str else len(c1_str)
#                         c1_value_str = c1_str[:c1_end_index]
#                         try:
#                             c1_value = float(c1_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных C1: {c1_value_str}")
#
#                     if c2_index != -1:
#                         c2_str = data[c2_index + 2:]  # Берем строку, начиная с символа после '2C'
#                         c2_end_index = c2_str.find(' ') if ' ' in c2_str else len(c2_str)
#                         c2_value_str = c2_str[:c2_end_index]
#                         try:
#                             c2_value = float(c2_value_str)
#                         except ValueError:
#                             messagebox.showerror("Ошибка", f"Ошибка парсинга данных C2: {c2_value_str}")
#
#                     # Записываем данные в три колонки: время, C1, C2
#                     writer.writerow([current_time, c1_value if c1_value is not None else '',
#                                      c2_value if c2_value is not None else ''])
#         except Exception as e:
#             messagebox.showerror("Ошибка", f"Ошибка записи данных в файл: {str(e)}")
#
#     def choose_file(self):
#         """Открывает диалоговое окно для выбора файла для сохранения данных."""
#         self.file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
#         if self.file_path:
#             messagebox.showinfo("Информация", f"Файл для сохранения данных выбран: {self.file_path}")
#
#     def start_recording(self):
#         """Начинает запись данных."""
#         if not self.is_recording:
#             self.is_recording = True
#             messagebox.showinfo("Информация", "Запись данных начата.")
#
#     def stop_recording(self):
#         """Завершает запись данных."""
#         if self.is_recording:
#             self.is_recording = False
#             messagebox.showinfo("Информация", "Запись данных завершена.")
#
#     def open_plot_window(self):
#         """Открывает окно для отображения графика данных."""
#         self.fig, self.ax = plt.subplots()
#         self.ax.set_xlabel('Время (секунды)')
#         self.ax.set_ylabel('Значение')
#         self.ax.set_title('График данных')
#         self.ax.grid(True)  # Добавление сетки
#
#         if self.data_type == 'R':
#             self.line_r1, = self.ax.plot([], [], label='R1')
#             self.line_r2, = self.ax.plot([], [], label='R2')
#         elif self.data_type == 'C':
#             self.line_c1, = self.ax.plot([], [], label='C1')
#             self.line_c2, = self.ax.plot([], [], label='C2')
#
#         self.ax.legend()
#
#         self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
#         self.canvas.draw()
#         self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
#
#         toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
#         toolbar.update()
#         self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
#
#         self.ax.set_ylim(bottom=0.00001, top=9999)
#         self.ax.set_xlim(left=0)
#
#     def update_plot_type(self, plot_type):
#         """Обновляет тип отображаемого графика."""
#         self.ax.clear()
#         self.ax.set_xlabel('Время (секунды)')
#         self.ax.set_ylabel('Значение')
#         self.ax.set_title('График данных')
#         self.ax.grid(True)
#
#         if self.data_type == 'R':
#             if plot_type == 'R1':
#                 self.ax.plot(self.times_r1, self.values_r1, label='R1')
#             elif plot_type == 'R2':
#                 self.ax.plot(self.times_r2, self.values_r2, label='R2')
#             elif plot_type == 'both':
#                 self.ax.plot(self.times_r1, self.values_r1, label='R1')
#                 self.ax.plot(self.times_r2, self.values_r2, label='R2')
#         elif self.data_type == 'C':
#             if plot_type == 'R1':
#                 self.ax.plot(self.times_c1, self.values_c1, label='C1')
#             elif plot_type == 'R2':
#                 self.ax.plot(self.times_c2, self.values_c2, label='C2')
#             elif plot_type == 'both':
#                 self.ax.plot(self.times_c1, self.values_c1, label='C1')
#                 self.ax.plot(self.times_c2, self.values_c2, label='C2')
#
#         self.ax.legend()
#         self.canvas.draw()
#
#     def convert_time_to_seconds(self, time_str):
#         """Преобразует строку времени в секунды от начала записи."""
#         time_format = "%H:%M:%S.%f"
#         time_obj = datetime.datetime.strptime(time_str, time_format)
#         print(time_obj)
#         start_time_obj = datetime.datetime.strptime(self.start_time_str, time_format)
#         delta = time_obj - start_time_obj
#         print(delta)
#         return delta.total_seconds()
#
#     def close_app(self):
#         """Закрывает приложение, закрывая все потоки и порты."""
#         if self.serial_port and self.serial_port.is_open:
#             self.serial_port.close()
#         if self.read_data_thread and self.read_data_thread.is_alive():
#             self.read_data_thread.join(timeout=1)
#         self.root.destroy()
#
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = TermexApp(root)
#
#     def on_closing():
#         if messagebox.askokcancel("Выход", "Закрыть программу?"):
#             app.close_app()
#
#     root.protocol("WM_DELETE_WINDOW", on_closing)
#     root.mainloop()
