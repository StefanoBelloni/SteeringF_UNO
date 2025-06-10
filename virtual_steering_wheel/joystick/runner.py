import serial
from virtual_steering_wheel.joystick.vjoy import get_joystick_from_driver_version

def execute(port):
    try:
        arduino = serial.Serial(port=port, baudrate=9600)
        joystick = None
        while joystick is None:
            try:
                joystick = get_joystick_from_driver_version(arduino_input=arduino, timeout=30)
            except RuntimeError as e:
                continue_try = input("[WARNING] no valid data could be read: retry? [y]es/[n]o")
                if continue_try.startswith('y'): continue
                else: raise e

        c = input("[QUESTION] Do you want to calibrate the Joystick? Enter y(es)/n(o): ")
        if c.startswith('y'):
            joystick.calibrate()
        else:
            print(f"[INFO]   === SKIPPING CALIBRATION ===   ")
            joystick.load_configuration()
        arduino.read_all()

        while True: joystick.update()

    except KeyboardInterrupt:
        print(f"\n[INFO]   === JOYSTIC DISCONNECTED ===   ")
    except Exception as e:
        print(f"[ERROR] {e}")