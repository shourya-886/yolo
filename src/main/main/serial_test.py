import serial
import time

ser = serial.Serial('/dev/arduino', 115200)
# Give the serial connection a moment to initialize
time.sleep(2) 

print(ser.name)

for n in range(1, 10):
    # Properly encode the f-string to bytes and include the newline
    message = f'hello{n}\n'
    ser.write(message.encode('utf-8'))
    print(f"Sent: {message.strip()}")
    time.sleep(0.5) # Optional: add a delay so the Arduino can keep up