from serial import Serial
import time

def SendConfirmation(device_port):
    try:
        ser = Serial(device_port, 9600)
        serial_init = True
    except Exception as e:
        print("Error with connection:", e)
        return False
    
    time.sleep(1)

    if serial_init:
        ser.write(b"send hello world from pc\n")
        return True
    else:
        return False

while True:
    if SendConfirmation("COM6"):
        
        try:
            ser = Serial("COM6", 9600)
            serial_init = True
        except Exception as e:
            print("Error with connection:", e)
            serial_init = False

        time.sleep(1)

        if serial_init:
                while True:
                    data = ser.readline().strip()  # Remove leading/trailing whitespace and newline characters
                    if data:
                        data_str = data.decode()  # Decode bytes to string
                        print(data_str)
                        if "END" not in data_str:
                            print(data_str)
                        else:
                            print("Received 'END'. Closing file.")
                            break