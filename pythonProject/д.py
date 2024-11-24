import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports

class TermexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Преобразователь сигналов ТС и ТП прецизионные ТЕРКОН")
        self.root.geometry("600x400")

        self.port_label = tk.Label(root, text="COM-порт:")
        self.port_label.pack()

        self.port_input = tk.Entry(root)
        self.port_input.pack()

        self.connect_button = tk.Button(root, text="Подключиться", command=self.connect_to_device)
        self.connect_button.pack()

        self.data_label = tk.Label(root, text="Данные:")
        self.data_label.pack()

        self.data_display = tk.Text(root, state='disabled', height=10, width=70)
        self.data_display.pack()

        self.serial_port = None

    def connect_to_device(self):
        port = self.port_input.get()
        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.data_display.config(state='normal')
            self.data_display.insert(tk.END, "Успешно подключено к " + port + "\n")
            self.data_display.config(state='disabled')
            self.read_data()
        except serial.SerialException as e:
            messagebox.showerror("Ошибка", "Ошибка подключения: " + str(e))

    def read_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.readline().decode('utf-8').strip()
                self.data_display.config(state='normal')
                self.data_display.insert(tk.END, data + "\n")
                self.data_display.config(state='disabled')
                self.data_display.see(tk.END)
            except serial.SerialException as e:
                messagebox.showerror("Ошибка", "Ошибка чтения данных: " + str(e))
            self.root.after(1000, self.read_data)  # Обновление данных каждую секунду

    def close_app(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TermexApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
