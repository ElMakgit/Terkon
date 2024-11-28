import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import datetime

class RealTimePlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("График в реальном времени")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.serial_port = None
        self.data_r1 = []
        self.data_r2 = []
        self.times = []
        self.is_running = False
        self.plot_r1 = True
        self.plot_r2 = True

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill="both")

        self.main_frame = ttk.Frame(self.notebook)
        self.graph_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.main_frame, text='Главная')
        self.notebook.add(self.graph_frame, text='График')

        self.create_main_frame()
        self.create_graph_frame()

    def create_main_frame(self):
        self.port_listbox = tk.Listbox(self.main_frame)
        self.port_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.data_text = tk.Text(self.main_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.separator = ttk.Separator(self.main_frame, orient=tk.VERTICAL)
        self.separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.connect_button = ttk.Button(self.control_frame, text="Подключиться", command=self.connect_selected_port)
        self.connect_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.disconnect_button = ttk.Button(self.control_frame, text="Отключиться", command=self.disconnect_port)
        self.disconnect_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_button = ttk.Button(self.control_frame, text="Сохранить данные", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.update_port_list()

    def create_graph_frame(self):
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.graph_control_frame = ttk.Frame(self.graph_frame)
        self.graph_control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.toggle_r1_button = ttk.Button(self.graph_control_frame, text="Переключить R1", command=self.toggle_r1)
        self.toggle_r1_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_r2_button = ttk.Button(self.graph_control_frame, text="Переключить R2", command=self.toggle_r2)
        self.toggle_r2_button.pack(side=tk.LEFT, padx=5, pady=5)

    def update_port_list(self):
        self.port_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_listbox.insert(tk.END, port.device)

    def connect_selected_port(self):
        selected_port = self.port_listbox.get(self.port_listbox.curselection())
        if selected_port:
            try:
                self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                self.is_running = True
                threading.Thread(target=self.read_data).start()
                messagebox.showinfo("Успех", f"Успешно подключено к {selected_port}")
            except serial.SerialException as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть порт {selected_port}: {e}")

    def disconnect_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.is_running = False
            self.serial_port.close()
            self.serial_port = None

    def read_data(self):
        while self.is_running:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                if "R1(" in line and "R2(" in line:
                    r1_value = float(line.split("R1(")[1].split(")")[0])
                    r2_value = float(line.split("R2(")[1].split(")")[0])
                    self.data_r1.append(r1_value)
                    self.data_r2.append(r2_value)
                    self.times.append(datetime.datetime.now())
                    self.update_data_display(r1_value, r2_value)
                    self.update_graph()
            except Exception as e:
                print(f"Ошибка чтения данных: {e}")

    def update_data_display(self, r1_value, r2_value):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data_text.config(state=tk.NORMAL)
        self.data_text.insert(tk.END, f"{current_time} R1({r1_value}) R2({r2_value})\n")
        self.data_text.see(tk.END)
        self.data_text.config(state=tk.DISABLED)

    def update_graph(self):
        self.ax.clear()
        if self.plot_r1:
            self.ax.plot(self.times, self.data_r1, label='R1')
        if self.plot_r2:
            self.ax.plot(self.times, self.data_r2, label='R2')
        self.ax.legend()
        self.canvas.draw()

    def save_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w") as file:
                for i in range(len(self.times)):
                    file.write(f"{self.times[i]} R1({self.data_r1[i]}) R2({self.data_r2[i]})\n")

    def toggle_r1(self):
        self.plot_r1 = not self.plot_r1
        self.update_graph()

    def toggle_r2(self):
        self.plot_r2 = not self.plot_r2
        self.update_graph()

    def on_closing(self):
        self.disconnect_port()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimePlotApp(root)
    root.mainloop()
