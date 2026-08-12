import serial

ser = serial.Serial("COM20", 115200, timeout=1)  # 把 COM3 改成你的端口

while True:
    data = ser.read(64)
    if data:
        print(data.hex(" "))
