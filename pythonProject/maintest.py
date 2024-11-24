import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

class TermexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Преобразователь сигналов ТС и ТП прецизионные ТЕРКОН")
        self.root.geometry("800x600")
        messagebox.showwarning("Внимание", "Программа создана ElMak")

        # Создаем панель для разделения окон
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
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
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.save_button = tk.Button(self.button_frame, text="Выбрать файл для сохранения", command=self.choose_file)
        self.save_button.pack(side=tk.LEFT, padx=2)

        self.start_record_button = tk.Button(self.button_frame, text="Начать запись", command=self.start_recording)
        self.start_record_button.pack(side=tk.LEFT, padx=2)

        self.stop_record_button = tk.Button(self.button_frame, text="Закончить запись", command=self.stop_recording)
        self.stop_record_button.pack(side=tk.LEFT, padx=2)

        self.plot_button = tk.Button(self.button_frame, text="График", command=self.open_plot_window)
        self.plot_button.pack(side=tk.LEFT, padx=2)

        self.serial_port = None
        self.start_time = None
        self.file_path = None
        self.data_r1 = []
        self.data_r2 = []
        self.is_recording = False

        self.update_port_list()

    def update_port_list(self):
        self.port_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_listbox.insert(tk.END, port.device)
        self.root.after(1000, self.update_port_list)  # Обновление списка портов каждую секунду

    def connect_to_device(self, event):
        selected_port = self.port_listbox.get(self.port_listbox.curselection())
        try:
            self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Успешно подключено к " + selected_port + "\n")
            self.data_display.config(state='disabled')
            self.start_time = time.time()  # Запоминаем время начала записи
            self.read_data()
        except serial.SerialException as e:
            messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))

    def read_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.readline().decode('utf-8').strip()
                elapsed_time = int(time.time() - self.start_time)  # Время в секундах с начала записи
                formatted_data = f"{elapsed_time}сек - {data}"
                self.data_display.config(state='normal')
                self.data_display.insert(tk.END, formatted_data + "\n")
                self.data_display.config(state='disabled')
                self.data_display.see(tk.END)

                if self.is_recording and self.file_path:
                    self.write_to_file(formatted_data)

                # Парсинг данных
                r1_value = None
                r2_value = None
                parts = data.split()
                for part in parts:
                    if part.startswith('R1:'):
                        r1_value = float(part.split(':')[1])
                    elif part.startswith('R2:'):
                        r2_value = float(part.split(':')[1])

                if r1_value is not None:
                    self.data_r1.append((elapsed_time, r1_value))
                    print(f"R1: {elapsed_time}сек - {r1_value}")  # Отладочное сообщение
                if r2_value is not None:
                    self.data_r2.append((elapsed_time, r2_value))
                    print(f"R2: {elapsed_time}сек - {r2_value}")  # Отладочное сообщение

                # Обновление графика в реальном времени
                if hasattr(self, 'line_r1') and hasattr(self, 'line_r2'):
                    self.update_plot()

            except serial.SerialException as e:
                messagebox.showerror("Ошибка", "Ошибка чтения данных: " + str(e))
            except ValueError as e:
                messagebox.showerror("Ошибка", "Ошибка парсинга данных: " + str(e))
            self.root.after(1000, self.read_data)  # Обновление данных каждую секунду

    def write_to_file(self, data):
        with open(self.file_path, "a") as file:
            file.write(data + "\n")

    def choose_file(self):
        self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
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
        plot_window = tk.Toplevel(self.root)
        plot_window.title("График данных")
        plot_window.geometry("800x600")

        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Время (сек)')
        self.ax.set_ylabel('Значение')
        self.ax.set_title('График данных')
        self.ax.grid(True)  # Добавление сетки

        self.times_r1 = [entry[0] for entry in self.data_r1]
        self.values_r1 = [entry[1] for entry in self.data_r1]
        self.times_r2 = [entry[0] for entry in self.data_r2]
        self.values_r2 = [entry[1] for entry in self.data_r2]

        self.line_r1, = self.ax.plot(self.times_r1, self.values_r1, label='R1')
        self.line_r2, = self.ax.plot(self.times_r2, self.values_r2, label='R2')
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.zoom_scale = tk.Scale(plot_window, from_=-3, to=3, resolution=0.1, orient=tk.HORIZONTAL, label="Zoom", command=self.update_zoom)
        self.zoom_scale.set(0)
        self.zoom_scale.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.load_data_button = tk.Button(plot_window, text="Загрузить данные из файла", command=self.load_data_from_file)
        self.load_data_button.pack(side=tk.BOTTOM, anchor='center', pady=5)

    def update_plot(self):
        self.line_r1.set_xdata([entry[0] for entry in self.data_r1])
        self.line_r1.set_ydata([entry[1] for entry in self.data_r1])
        self.line_r2.set_xdata([entry[0] for entry in self.data_r2])
        self.line_r2.set_ydata([entry[1] for entry in self.data_r2])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def update_zoom(self, value):
        zoom_level = 10 ** float(value)
        self.ax.set_ylim(self.ax.get_ylim()[0] * zoom_level, self.ax.get_ylim()[1] * zoom_level)
        self.canvas.draw()

    def load_data_from_file(self):
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            self.data_r1 = []
            self.data_r2 = []
            with open(file_path, "r") as file:
                for line in file:
                    parts = line.split()
                    if len(parts) >= 3:
                        time_value = int(parts[0].replace('сек', ''))
                        r1_value = float(parts[1].split(':')[1])
                        r2_value = float(parts[2].split(':')[1])
                        self.data_r1.append((time_value, r1_value))
                        self.data_r2.append((time_value, r2_value))
            self.update_plot()

    def close_app(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TermexApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
