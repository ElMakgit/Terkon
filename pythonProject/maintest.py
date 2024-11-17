import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.filedialog import asksaveasfilename
import numpy as np

# Global list to store random numbers
random_numbers = []
recording = False  # Flag to indicate if we are recording

# Coefficients for the polynomial
coefficients = [0, 1]  # Default coefficients for a linear polynomial

def save_file():
    filename = asksaveasfilename(defaultextension=".txt",
                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                 title="Сохранить файл как...")
    if not filename:  # If the user cancels the save dialog
        return
    with open(filename, 'w') as file:
        for number in random_numbers:
            file.write(f"{number}\n")
    messagebox.showinfo("Успех", f"Файл сохранен как: {filename}")

def start_recording():
    global recording
    recording = True  # Start recording
    random_numbers.clear()  # Clear any previous numbers
    x_data.clear()  # Clear x_data for new recording
    y1_data.clear()  # Clear y1_data for new recording
    y2_data.clear()  # Clear y2_data for new recording
    messagebox.showinfo("Запись", "Начата запись случайных чисел.")

def stop_recording():
    global recording
    recording = False  # Stop recording
    messagebox.showinfo("Запись", "Запись случайных чисел остановлена.")

def calculate_temperature(resistance):
    """Calculate temperature based on the polynomial coefficients."""
    return sum(coef * (resistance ** i) for i, coef in enumerate(coefficients))

def update_labels():
    if recording:
        resistance = random.uniform(0, 1000)  # Simulated resistance value
        temperature = calculate_temperature(resistance)  # Calculate temperature

        label1.config(text=f"Сопротивление: {resistance:.2f}")
        label2.config(text=f"Температура: {temperature:.2f}")

        random_numbers.append((resistance, temperature))

        # Update x_data and y_data for plotting
        x_data.append(len(x_data) + 1)  # Increment x-axis
        y1_data.append(resistance)  # Add new resistance value
        y2_data.append(temperature)  # Add new temperature value

        # Clear the previous scatter points and plot new ones
        ax.cla()  # Clear the axes
        ax.grid(True)  # Re-enable grid
        ax.set_ylim(-1000.0000, 1000.9999)  # Set y limits
        ax.set_xlabel("Секунды")
        ax.set_ylabel("Значения")

        # Plot the points and connect them with lines
        ax.plot(x_data, y1_data, label='Сопротивление', color='blue', marker='o')
        ax.plot(x_data, y2_data, label='Температура', color='orange', marker='o')

        # Annotate each point with its coordinates
        for i in range(len(x_data)):
            ax.text(x_data[i], y1_data[i] + 50, f'({x_data[i]}, {y1_data[i]:.2f})',
                    fontsize=8, ha='center', color='blue')
            ax.text(x_data[i], y2_data[i] + 50, f'({x_data[i]}, {y2_data[i]:.2f})',
                    fontsize=8, ha='center', color='orange')

        ax.legend()
        ax.relim()  # Recalculate limits
        ax.autoscale_view()  # Autoscale the view
        canvas.draw()  # Redraw the canvas

    app.after(1000, update_labels)  # Call this function every second

def resize_canvas(event):
    width = app.winfo_width()
    height = app.winfo_height()
    canvas .get_tk_widget().config(width=width - 20, height=height - 320)

def update_y_scale(value):
    scale_value = float(value)
    ax.set_ylim(-scale_value, scale_value)
    ax.set_yticks([-scale_value, -scale_value / 2, 0, scale_value / 2, scale_value])
    canvas.draw()

class DraggableZoomPan:
    def __init__(self, ax):
        self.ax = ax
        self.press = None
        self.cid_press = ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_scroll = ax.figure.canvas.mpl_connect('scroll_event', self.on_scroll)

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        self.press = event.xdata, event.ydata

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax:
            return
        dx = event.xdata - self.press[0]
        dy = event.ydata - self.press[1]
        self.ax.set_xlim(self.ax.get_xlim()[0] - dx, self.ax.get_xlim()[1] - dx)
        self.ax.set_ylim(self.ax.get_ylim()[0] - dy, self.ax.get_ylim()[1] - dy)
        self.press = event.xdata, event.ydata
        self.ax.figure.canvas.draw()

    def on_release(self, event):
        self.press = None

    def on_scroll(self, event):
        scale_factor = 1.1 if event.button == 'up' else 0.9
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_center = event.xdata
        y_center = event.ydata

        new_xlim = [(x - x_center) * scale_factor + x_center for x in xlim]
        new_ylim = [(y - y_center) * scale_factor + y_center for y in ylim]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.ax.figure.canvas.draw()

# Create a Tkinter window
app = tk.Tk()
app.title("Теркон")
app.geometry('1000x800')
messagebox.showwarning(title="Внимание", message="Программа создана студентами КГУ из ФФМИ, распространение запрещено")

# Create a Matplotlib figure
fig, ax = plt.subplots(figsize=(4, 3))
ax.set_ylim(-1000.0000, 1000.9999)
ax.set_xlabel("Секунды")
ax.set_ylabel("Значения")

# Разметка местоположения
ax.grid(True)  # Enable grid

# Data lists for plotting
x_data = []
y1_data = []
y2_data = []

# Подключение графика в окно приложения
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().place(x=10, y=300)

# Кнопки для записи сохранения и сохранения
main_btn = tk.Button(text='Запись', width=20, height=1, command=start_recording)
main_btn.pack(side=tk.LEFT, anchor=tk.N)

stop_btn = tk.Button(text='Прервать запись', width=20, height=1, command=stop_recording)
stop_btn.pack(side=tk.LEFT, anchor=tk.N)

print_btn = tk.Button(text='Сохранить', width=20, height=1, command=save_file)
print_btn.pack(side=tk.LEFT, anchor=tk.N)

# Строки для вывода значений на экран
label1 = tk.Label(app, text="Сопротивление: R1", anchor="nw", justify="left", font=("Arial", 16))
label1.place(x=0, y=30)
label2 = tk.Label(app, text="Температура: R2", anchor="nw", justify="left", font=("Arial", 16))
label2.place(x=200, y=30)

def input_coefficients():
    global coefficients
    coeffs = simpledialog.askstring("Коэффициенты", "Введите коэффициенты полинома через запятую:")
    if coeffs:
        coefficients = [float(coef) for coef in coeffs.split(',')]
        messagebox.showinfo("Успех", "Коэффициенты обновлены.")

# Add a button to input coefficients
coeff_btn = tk.Button(text='Ввести коэффициенты', width=20, height=1, command=input_coefficients)
coeff_btn.pack(side=tk.LEFT, anchor=tk.N)

# Initialize coefficients with default values (e.g., for a linear polynomial)
coefficients = [0, 1]  # Example: y = 0 + 1*x (linear relationship)

# Adding a scale slider for Y-axis
y_scale_values = [0.0001, 0.001, 0.1, 0.5, 2, 10, 50, 200, 1000, 5000, 9999]
y_scale_var = tk.StringVar(value=str(y_scale_values[4]))
# scale = tk.Scale(app, from_=0, to=len(y_scale_values) - 1, orient=tk.HORIZONTAL,
#                  label="Масштаб", length=200, command=lambda val: update_y_scale(y_scale_values[int(val)]))
# scale.pack(side=tk.RIGHT, anchor=tk.N)
#
# # Set initial scale
# update_y_scale(y_scale_values[4])

# Bind resize event to resize_canvas functionpyinstaller -
#
app.bind("<Configure>", resize_canvas)

# Handle window close event
def on_closing():
    app.quit()
    app.destroy()  # This will destroy the window and release resources

app.protocol("WM_DELETE_WINDOW", on_closing)

# Start updating labels
update_labels()

# Initialize the draggable and zoomable functionality
draggable_zoom_pan = DraggableZoomPan(ax)

# Start the Tkinter main loop
app.mainloop()