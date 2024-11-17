from tkinter import *
from tkinter import messagebox, ttk
import serial.tools.list_ports
import serial
from serial.serialutil import STOPBITS_ONE

def receive_usb_data(label):
  ports = list(serial.tools.list_ports.comports())
  port_found = False
  for port in ports:
    if "Arduino" in port.description: # Пример, подставьте свою логику проверки
      port_found = True
      port = port.device
      break

  if not port_found:
    print("Port not found")
    return

  baudrate = 9600
  try:
    ser = serial.Serial(port, baudrate=baudrate, stopbits=STOPBITS_ONE)
    flag = True
    while flag:
      try:
        data = ser.readline().decode('utf-8', errors='replace').rstrip()
        if data:
          print(data)
          label.config(text=data)
          app.update() #обновление интерфейса
      except Exception as e:
        print(f"Error reading data: {e}")
        label.config(text=f"Error reading data: {e}")
        app.update() #обновление интерфейса

      if app.winfo_exists() == 0: # Проверка на закрытие основного окна
        flag = False
        ser.close()
        break

  except serial.SerialException as e:
    print(f'Error of connection: {e}')
    label.config(text=f'Error of connection: {e}')
    app.update() #обновление интерфейса

def on_button_click():
  settings_window = Toplevel() # Используем Toplevel для создания дочернего окна
  settings_window.title("Настройки")
  label = Label(settings_window, text="Это настройки, но тут пока ничего нет")
  label.pack()
  settings_window.resizable(False, False) # Запрещаем изменение размера


app = Tk()
app.title("Теркон")
app.geometry('500x600')

messagebox.showwarning(title="Внимание",
            message="Программа создана студентами КГУ из ФФМИ, распространение запрещено")

# Увеличим кнопки
main_btn = Button(
  text='Главная',
  width=15,
  height=2
)
main_btn.pack(side=TOP, anchor=E)

sett_btn = Button(
  text='Настройки',
  width=15,
  height=2,
  command=on_button_click
)
sett_btn.pack(side=TOP, anchor=E)

stop_btn = Button(
  text='Стоп',
  width=15,
  height=2,
  command=app.quit
)
stop_btn.pack(side=TOP, anchor=E)

# Добавление элемента для вывода данных из порта
output_label = Label(app, text="", anchor="nw", justify="left", wraplength=400)
output_label.place(x=10, y=10) # Расположение в левом верхнем углу


app.after(100, receive_usb_data, output_label) # Запуск функции receive_usb_data


app.mainloop()