import serial.tools.list_ports
import serial

ports = serial.tools.list_ports.comports()

for port in ports:
    print(f'Порт) {port.device}')

port = "COM3"
baudrate = 9600

ser = serial.Serial(port, baudrate=baudrate, stopbits=1)
print(b'Doom game for microwave')
while True:
    ser.write(b'Doom game for microwave')
    print('Done')

ser.close()