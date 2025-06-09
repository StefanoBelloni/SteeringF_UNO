import serial
from vjoy import get_joystick_from_driver_version

def execute(port, serial=None):
    try:
        arduino = serial.Serial(port=port, baudrate=9600) if serial is None else serial
        joystick = get_joystick_from_driver_version(arduino_input=arduino)
        c = input("[QUESTION] Do you want to calibrate the Joystick? Enter y(es)/n(o): ")
        if c.startswith('y'):
            joystick.calibrate()
        else:
            print(f"[INFO]   === SKIPPING CALIBRATION ===   ")
            joystick.load_configuration()
        arduino.read_all()

        while True: joystick.update()

    except KeyboardInterrupt:
        print(f"[INFO]   === JOYSTIC DISCONNECTED ===   ")
    except Exception as e:
        print(f"[ERROR] {e}")