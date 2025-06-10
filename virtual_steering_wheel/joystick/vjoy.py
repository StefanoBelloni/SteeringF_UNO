import serial
import vgamepad as vg
from pyautogui import keyDown, keyUp

from virtual_steering_wheel.joystick.arduino_state import ArduinoStateV1, ArduinoStateV2

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

class VirtualJoysticSimple:
    """
    Minimal Joystic with two buttons
    """
    def __init__(self, arduino_input, state_class=ArduinoStateV1, game_pad_class=vg.VX360Gamepad, filenameconfig=None):
        self._arduino_input = arduino_input
        self._gamepad = game_pad_class()
        self._state_class = state_class
        self._state = self._state_class(filename=filenameconfig)

    def _print_ranges_joystick(self):
        print(str(self))
    
    def __str__(self):
        return (
            f"[INFO] Joystick name: {self.name()}\n"
            f"[INFO] Range to center STEERING is [{self._state.get_steer_range()}]\n"
            f"[INFO] Range to center THROTTLE is [{self._state.get_throttle_range()}]\n"
            f"[INFO] Range to center BREAK    is [{self._state.get_break_range()}]"
        )

    def _print_info_joystic(self, canSave=True):
        self._arduino_input.read_all()
        self._print_ranges_joystick()
        print(f"[INFO] fire RIGHT to conclude ... ")
        if canSave: print(f"[INFO]      LEFT to SAVE calibration... ")
        while True:
            state = read_serial(self._arduino_input, self._state)
            print("[INFO]", state, end='              \r')
            if state.is_gear_up_pressed():
                break
            if canSave and state.is_gear_down_pressed():
                print("[INFO] saving configuration: ", state.get_config())
                state.dump_config()
                break
        print("[INFO] ", '=' * 90)
        print("[INFO] |  VIRTUAL JOYSTICK RUNNING")
        print("[INFO] ", '=' * 90)

    def _exec_calibration(self, direction, callback, getter):
        self._arduino_input.read_all()
        print(f"[INFO] command -> {direction} and FIRE")
        stateTmp = self._state_class()
        while True:
            stateTmp = read_serial(self._arduino_input, stateTmp)
            print("[INFO]", stateTmp, end='              \r')
            if stateTmp.is_gear_up_pressed():
                func_get = getattr(stateTmp, getter)
                v = func_get()
                print(f"\n[INFO] Value for {direction} is {v}")
                callback(v)
                while stateTmp.is_gear_up_pressed():
                    self._arduino_input.read_all()
                    stateTmp = read_serial(self._arduino_input, stateTmp)
                break

    def _execute_update(self):
        self._update_gear_state()
        self._update_joystic_state()

    def _update_joystic_state(self):
        self._gamepad.left_joystick_float(
            x_value_float=self._state.get_steer(), 
            y_value_float=self._state.get_acceleration())
        self._gamepad.update()

    def _update_gear_state(self):
        if self._state.is_gear_up_changed():
            if self._state.is_gear_up_pressed():
                self._gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                self._gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        elif self._state.is_gear_down_changed():
            if self._state.is_gear_down_pressed():
                self._gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            else:
                self._gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    
    def calibrate(self):
        print(f"[INFO]   === START CALIBRATION ===   ")
        for direction, callback, getter in [
            ('LEFT         ', self._state.set_min_steer,    "get_raw_steer"),
            ('RIGHT        ', self._state.set_max_steer,    "get_raw_steer"),
            ('NO THROTTLE  ', self._state.set_min_throttle, "get_raw_throttle"),
            ('FULL THROTTLE', self._state.set_max_throttle, "get_raw_throttle"),
            ('NO BREAK     ', self._state.set_min_break,    "get_raw_break"),
            ('FULL BREAK   ', self._state.set_max_break,    "get_raw_break"),
        ]:
            self._exec_calibration(direction, callback, getter)
        self._print_info_joystic()
        print(f"[INFO]   === CALIBRATION DONE ===   ")
    
    def load_configuration(self):
        print(f"[INFO] reading configuration ", self._state.get_config())
        self._state.load_config()
        self._print_info_joystic(canSave=False)
    
    def update(self):
        self._state = read_serial(self._arduino_input, self._state)
        self._execute_update()
    
    def name(self):
        return "SIMPLE_JOYSTICK"

class VirtualJoysticGP4(VirtualJoysticSimple):
    """
    Class to initialize a Steering Wheel with 4 buttons for GP4

    This class binds two extra buttons to the input from keyboard 'x' and 'c'
    used to rotate the head of the driver to left or right.

    """

    def __init__(self, arduino_input, game_pad_class=vg.VX360Gamepad, filenameconfig=None):
        super().__init__(arduino_input, ArduinoStateV2, game_pad_class=game_pad_class, filenameconfig=filenameconfig)

    def _execute_update(self):
        self._update_gear_state()
        self._update_extra_buttons()
        self._update_joystic_state()

    def _update_extra_buttons(self):
        """ On linux only GAMEPAD_A and GAMEPAD_B seems to be working: 
        in GP4 key 'x', 'c' are used to look left/right: 
        simulate these key press with the 2 extra buttons.
        """
        if self._state.is_btn_right_changed():
            if self._state.is_btn_right_pressed(): keyDown('c')
            else:                                  keyUp('c')
        elif self._state.is_btn_left_changed():
            if self._state.is_btn_left_pressed(): keyDown('x')
            else:                                 keyUp('x')

    def name(self):
        return "GP4_JOYSTICK"

def get_joystick_from_driver_version(arduino_input, filename=None, game_pad_class=vg.VX360Gamepad, timeout=0):
    # at the moment arduino starts sending data without comunicating the version:
    # this can just be extracted from the form of the input.
    attempts = 0
    for _ in range(timeout + 1):
        _ = arduino_input.read_all()
        check_line = arduino_input.readline()
        tokens = check_line.decode('ascii').strip().split(';')
        if len(tokens) == 5:
            return VirtualJoysticSimple(arduino_input, ArduinoStateV1, game_pad_class=game_pad_class, filenameconfig=filename)
        elif len(tokens) == 7:
            return VirtualJoysticGP4(arduino_input, game_pad_class=game_pad_class, filenameconfig=filename)
        else:
            if attempts > timeout:
                break
        attempts += 1
    raise RuntimeError(f"[ERROR] invalid message from serial input: {check_line}")

