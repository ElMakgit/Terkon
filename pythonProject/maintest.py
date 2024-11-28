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
        self.root.geometry("800x600")
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

        # Галочки для выбора типа данных
        self.data_type_var = BooleanVar()
        self.data_type_r = tk.Radiobutton(self.main_frame, text="Тип данных R", variable=self.data_type_var, value=True, command=self.update_data_type)
        self.data_type_r.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
        self.data_type_c = tk.Radiobutton(self.main_frame, text="Тип данных C", variable=self.data_type_var, value=False, command=self.update_data_type)
        self.data_type_c.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
        self.data_type_var.set(True)  # По умолчанию выбран тип данных R

        # Метки для отображения текущих значений данных
        self.r1_label = tk.Label(self.main_frame, text="R1: ")
        self.r1_label.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)
        self.r2_label = tk.Label(self.main_frame, text="R2: ")
        self.r2_label.pack(side=tk.BOTTOM, anchor='e', padx=5, pady=5)

        # Вкладка для графика
        self.plot_frame = tk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="График")
        self.serial_port = None
        self.start_time = None
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
        self.update_port_list()


    def update_port_list(self):
        self.port_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_listbox.insert(tk.END, port.device)
        self.root.after(5000, self.update_port_list)  # Обновление списка портов каждые 5 секунд

    def connect_to_device(self, event):
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
        except serial.SerialException as e:
            messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))

    def disconnect_from_device(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Отключено от порта\n")
            self.data_display.config(state='disabled')
            if self.read_data_thread and self.read_data_thread.is_alive():
                self.read_data_thread.join(timeout=1)

    def update_data_type(self):
        if self.data_type_var.get():
            self.data_type = 'R'
        else:
            self.data_type = 'C'
        self.attempts = 0  # Сброс счетчика попыток при смене типа данных

    def read_data(self):
        while self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.readline().decode('utf-8').strip()
                current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")  # Текущее время с миллисекундами
                formatted_data = f"{current_time} - {data}"
                self.root.after(0, self.update_data_display, formatted_data)
                print("данные получены")
                print(data)
                print(current_time)
                print(formatted_data)

                if self.is_recording and self.file_path:
                    self.write_to_file(formatted_data)

                # Парсинг данных
                if self.data_type == 'R':
                    if '1R' not in data and '2R' not in data:
                        self.attempts += 1
                        if self.attempts >= self.max_attempts:
                            messagebox.showerror("Ошибка", "Неверный тип данных. Ожидаются данные типа R.")
                            self.disconnect_from_device()
                            self.data_type_var.set(False)
                            self.data_type = 'C'
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

                    print(r1_value, r2_value)

                    if r1_value is not None:
                        self.data_r1.append((current_time, r1_value))
                    if r2_value is not None:
                        self.data_r2.append((current_time, r2_value))

                    # Обновление меток с текущими значениями
                    if r1_value is not None:
                        self.r1_label.config(text=f"R1: {r1_value}")
                    if r2_value is not None:
                        self.r2_label.config(text=f"R2: {r2_value}")

                elif self.data_type == 'C':
                    if '1C' not in data and '2C' not in data:
                        self.attempts += 1
                        if self.attempts >= self.max_attempts:
                            messagebox.showerror("Ошибка", "Неверный тип данных. Ожидаются данные типа C.")
                            self.disconnect_from_device()
                            self.data_type_var.set(True)
                            self.data_type = 'R'
                            return
                        continue
                    else:
                        self.attempts = 0  # Сброс счетчика попыток при успешном получении данных

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

                    print(c1_value, c2_value)

                    if c1_value is not None:
                        self.data_c1.append((current_time, c1_value))
                    if c2_value is not None:
                        self.data_c2.append((current_time, c2_value))

                    # Обновление меток с текущими значениями
                    if c1_value is not None:
                        self.r1_label.config(text=f"C1: {c1_value}")
                    if c2_value is not None:
                        self.r2_label.config(text=f"C2: {c2_value}")

                # Обновление графика в реальном времени
                if hasattr(self, 'line_r1') and hasattr(self, 'line_r2'):
                    self.root.after(0, self.update_plot)

            except serial.SerialException as e:
                messagebox.showerror("Ошибка", "Ошибка чтения данных: " + str(e))
            except ValueError as e:
                messagebox.showerror("Ошибка", "Ошибка парсинга данных: " + str(e))
            time.sleep(0.1)  # Пауза между чтениями данных

    def update_data_display(self, data):
        self.data_display.config(state='normal')
        self.data_display.insert(tk.END, data + "\n")
        self.data_display.config(state='disabled')
        self.data_display.see(tk.END)

    def write_to_file(self, data):
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
        self.file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if self.file_path:
            messagebox.showinfo("Информация", f"Файл для сохранения данных выбран: {self.file_path}")

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            messagebox.showinfo("Информация", "Запись данных начата.")

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            messagebox.showinfo("Информация", "Запись данных завершена.")

    def open_plot_window(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Время')
        self.ax.set_ylabel('Значение')
        self.ax.set_title('График данных')
        self.ax.grid(True)  # Добавление сетки

        plot_frame = tk.Frame(self.plot_frame)
        plot_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.show_r1_button = tk.Button(plot_frame, text="Показать R1", command=lambda: self.update_plot_type('R1'))
        self.show_r1_button.pack(side=tk.LEFT, padx=2)

        self.show_r2_button = tk.Button(plot_frame, text="Показать R2", command=lambda: self.update_plot_type('R2'))
        self.show_r2_button.pack(side=tk.LEFT, padx=2)

        self.show_both_button = tk.Button(plot_frame, text="Показать R1 и R2", command=lambda: self.update_plot_type('both'))
        self.show_both_button.pack(side=tk.LEFT, padx=2)

        if self.data_type == 'R':
            self.times_r1 = [entry[0] for entry in self.data_r1]
            self.values_r1 = [entry[1] for entry in self.data_r1]
            self.times_r2 = [entry[0] for entry in self.data_r2]
            self.values_r2 = [entry[1] for entry in self.data_r2]

            self.line_r1, = self.ax.plot(self.times_r1, self.values_r1, label='R1')
            self.line_r2, = self.ax.plot(self.times_r2, self.values_r2, label='R2')
        elif self.data_type == 'C':
            self.times_c1 = [entry[0] for entry in self.data_c1]
            self.values_c1 = [entry[1] for entry in self.data_c1]
            self.times_c2 = [entry[0] for entry in self.data_c2]
            self.values_c2 = [entry[1] for entry in self.data_c2]

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
        self.ax.clear()
        self.ax.set_xlabel('Время')
        self.ax.set_ylabel('Значение')
        self.ax.set_title('График данных')
        self.ax.grid(True)

        if self.data_type == 'R':
            if plot_type == 'R1':
                self.ax.plot(self.times_r1, self.values_r1, label='R1')
            elif plot_type == 'R2':
                self.ax.plot(self.times_r2, self.values_r2, label='R2')
            elif plot_type == 'both':
                self.ax.plot(self.times_r1, self.values_r1, label='R1')
                self.ax.plot(self.times_r2, self.values_r2, label='R2')
        elif self.data_type == 'C':
            if plot_type == 'R1':
                self.ax.plot(self.times_c1, self.values_c1, label='C1')
            elif plot_type == 'R2':
                self.ax.plot(self.times_c2, self.values_c2, label='C2')
            elif plot_type == 'both':
                self.ax.plot(self.times_c1, self.values_c1, label='C1')
                self.ax.plot(self.times_c2, self.values_c2, label='C2')

        self.ax.legend()
        self.canvas.draw()

    def update_plot(self):
        if self.data_type == 'R':
            self.line_r1.set_xdata([entry[0] for entry in self.data_r1])
            self.line_r1.set_ydata([entry[1] for entry in self.data_r1])
            self.line_r2.set_xdata([entry[0] for entry in self.data_r2])
            self.line_r2.set_ydata([entry[1] for entry in self.data_r2])
        elif self.data_type == 'C':
            self.line_c1.set_xdata([entry[0] for entry in self.data_c1])
            self.line_c1.set_ydata([entry[1] for entry in self.data_c1])
            self.line_c2.set_xdata([entry[0] for entry in self.data_c2])
            self.line_c2.set_ydata([entry[1] for entry in self.data_c2])

        # Обновление пределов осей
        if self.data_type == 'R':
            self.ax.set_xlim(left=0, right=max(max(self.times_r1), max(self.times_r2)))
            self.ax.set_ylim(bottom=0.00001, top=max(max(self.values_r1), max(self.values_r2)))
        elif self.data_type == 'C':
            self.ax.set_xlim(left=0, right=max(max(self.times_c1), max(self.times_c2)))
            self.ax.set_ylim(bottom=0.00001, top=max(max(self.values_c1), max(self.values_c2)))

        self.canvas.draw()

    def close_app(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.read_data_thread and self.read_data_thread.is_alive():
            self.read_data_thread.join(timeout=1)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TermexApp(root)

    def on_closing():
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            app.close_app()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
