import serial
import vgamepad as vg
from pyautogui import keyDown, keyUp

from virtual_steering_wheel.joystick.arduino_state import ArduinoState

debug = False

def read_serial(arduino: serial.Serial, state):
    line = arduino.readline()
    try: 
        state.update_from_line(line)
        if debug: print("[DEBUG]", line, ' -> ', state, end='                  \r')
    except Exception as e: 
        if debug: print("[DEBUG] input from arduino: ", line.decode('ascii').strip().split(';'), "exception -> ", e)
        # print(traceback.format_exc())
        return state
    return state

def updateJoystick(gamepad, state:ArduinoState):
    if state.is_gear_up_changed():
        if state.is_gear_up_pressed():
            gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        else:
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    elif state.is_gear_down_changed():
        if state.is_gear_down_pressed():
            gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        else:
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

    # ======================================================================== #
    if state.is_btn_right_changed():
        if state.is_btn_right_pressed():
            keyDown('c')
        else:
            keyUp('c')
    elif state.is_btn_left_changed():
        if state.is_btn_left_pressed():
            keyDown('x')
        else:
            keyUp('x')
    # ======================================================================== #
    gamepad.left_joystick_float(
        x_value_float=state.get_steer(), 
        y_value_float=state.get_acceleration())
    gamepad.update()

def debug_ranges(arduino: serial.Serial, state: ArduinoState):
    print(f"[INFO] Range to center STEERING is [{state.get_steer_range()}]")
    print(f"[INFO] Range to center THROTTLE is [{state.get_throttle_range()}]")
    print(f"[INFO] Range to center BREAK    is [{state.get_break_range()}]")

def debug_joystick(arduino, state, canSave=True):
    arduino.read_all()
    debug_ranges(arduino, state)
    print(f"[INFO] fire (RIGHT) to conclude ... ")
    if canSave: print(f"[INFO] left (LEFT) to SAVE calibration... ")
    while True:
        state = read_serial(arduino, state)
        print(state, end='              \r')
        if state.is_gear_up_pressed():
            break
        if canSave and state.is_gear_down_pressed():
            state.dump_config()
            break

def exec_calibration(arduino, direction, callback, getter):
    arduino.read_all()
    print(f"[INFO] Steer all {direction} and fire")
    stateTmp = ArduinoState()
    while True:
        stateTmp = read_serial(arduino, stateTmp)
        print(stateTmp, end='              \r')
        if stateTmp.is_gear_up_pressed():
            func_get = getattr(stateTmp, getter)
            v = func_get()
            print(f"\n[INFO] Value for {direction} is {v}\n")
            callback(v)
            while stateTmp.is_gear_up_pressed():
                arduino.read_all()
                stateTmp = read_serial(arduino, stateTmp)
            break


def calibrate(arduino: serial.Serial, state: ArduinoState):
    print(f"   === START CALIBRATION ===   ")
    for direction, callback, getter in [
        ('left', state.set_min_steer, "get_raw_steer"),
        ('right', state.set_max_steer, "get_raw_steer"),
        ('no gas', state.set_min_throttle, "get_raw_throttle"),
        ('full gas', state.set_max_throttle, "get_raw_throttle"),
        ('no break', state.set_min_break, "get_raw_break"),
        ('full break', state.set_max_break, "get_raw_break"),
        ]:
        exec_calibration(arduino, direction, callback, getter)
    debug_joystick(arduino, state)
    print(f"   === CALIBRATION DONE ===   ")


def run(port):
    try:
        arduino = serial.Serial(port=port, baudrate=9600)
        gamepad = vg.VX360Gamepad()
        state = ArduinoState()
        c = input("Do you want to calibrate the Joystick? Enter y(es)/n(o): ")
        if c.startswith('y'):
            calibrate(arduino, state)
        else:
            print(f"   === SKIPPING CALIBRATION ===   ")
            print(f"[INFO] reading configuration")
            state.load_config()
            debug_joystick(arduino, state, canSave=False)
        arduino.read_all()
        while True:
            state = read_serial(arduino, state)
            updateJoystick(gamepad, state)
            # time.sleep(0.01)
    except KeyboardInterrupt:
        print(f"   === JOYSTIC DISCONNECTED ===   ")
    except Exception as e:
        print(f"[ERROR] {e}")

