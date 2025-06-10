import tempfile
import unittest

from virtual_steering_wheel.joystick.vjoy import get_joystick_from_driver_version

class GamePadMock:
    def press_button(self, **kwargs): pass
    def release_button(self, **kwargs): pass
    def left_joystick_float(self, **kwargs): pass
    def right_joystick_float(self, **kwargs): pass
    def update(self): pass

class SerialMock:
    def __init__(self, buffered=None, lines=None):
        self._buffered = ['trash_1', 'trash_2'] if buffered is None else buffered
        self._lines = [] if lines is None else lines
        
    def read_all(self):
        return self._buffered

    def readline(self):
        line = self._lines.pop(0)
        # print(f"[INFO] sending line as serial: ", line, '                             ')
        return line
    
    def append_line(self, line):
        self._lines.append(line)

class TestVirtualJoystick(unittest.TestCase):

    def test_create_joystick(self):
        arduino_v1 = SerialMock(lines=[b'432;42;43;0;1'])
        arduino_v2 = SerialMock(lines=[b'432;42;43;0;1;0;1'])
        arduino_invalid = SerialMock(lines=[b'432;42;1'] * 10)
        joystic_v1 = get_joystick_from_driver_version(arduino_v1, game_pad_class=GamePadMock)
        joystic_v2 = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        self.assertEqual(joystic_v1.name(), 'SIMPLE_JOYSTICK')
        self.assertEqual(joystic_v2.name(), 'GP4_JOYSTICK') 
        self.assertRaises(RuntimeError, get_joystick_from_driver_version, arduino_invalid, game_pad_class=GamePadMock)
    
    def _get_calibration_sequence(self):
        return [
            b'first_message;42;43;0;1;0;1',
            # ------------------------ #
            # Steer
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;0;1;1;1',
            b'1000;2  ;12;1;1;1;1',
            b'1000;2  ;12;0;1;1;1',
            # ------------------------ #
            b'9   ;2  ;12;1;1;1;1',
            # ------------------------ #
            # Throttle
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;0;0;1;1',
            b'9   ;2  ;244;1;1;1;1',
            b'9   ;2  ;244;0;0;1;1',
            # ------------------------ #
            b'9   ;2  ;12;1;1;1;1',
            # ------------------------ #
            # Break
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;0;1;1;1',
            b'9   ;512;12;1;1;1;1',
            b'9   ;512;12;0;1;1;1',
            # ------------------------ #
            b'9   ;2  ;12;1;1;1;1',
            # ------------------------ #
        ]

    def _get_play_sequence(self):
        return [
            # ------------------------ #
            # Steer
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;0;1;1;1',
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;1;0;1;1',
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;1;1;0;1',
            b'9   ;2  ;12;1;1;1;1',
            b'9   ;2  ;12;1;1;1;0',
            b'9   ;2  ;12;1;1;1;1',
            # ------------------------ #
        ]
    
    def _get_v1_calibration_sequence(self):
        sequence = []
        for row in self._get_calibration_sequence():
            sequence.append(row[:-4])
        return sequence

    def _get_v1_play_sequence(self):
        sequence = []
        for row in self._get_play_sequence():
            sequence.append(row[:-4])
        return sequence

    def test_calibrate_v2(self):
        arduino_v2 = SerialMock(lines=self._get_calibration_sequence())
        joystick = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        # ------------------------ #
        # finish calibration
        arduino_v2.append_line(b'9   ;2  ;12;0;1;1;1')
        joystick.calibrate()

    def test_calibrate_v2_save_config(self):
        with tempfile.NamedTemporaryFile() as fp:
            arduino_v2 = SerialMock(lines=self._get_calibration_sequence())
            # ------------------------ #
            # finish calibration
            arduino_v2.append_line(b'9   ;2  ;12;1;0;1;1')
            joystick = get_joystick_from_driver_version(arduino_v2, filename=fp.name, game_pad_class=GamePadMock)
            joystick.calibrate()
            expected_joystick_info = """[INFO] Joystick name: GP4_JOYSTICK
[INFO] Range to center STEERING is [9;1000]
[INFO] Range to center THROTTLE is [12;244]
[INFO] Range to center BREAK    is [2;512]"""
            self.assertEqual(str(joystick), expected_joystick_info)

            arduino_restored = SerialMock(lines=[b'432;42;43;0;1;0;1'])
            # left: no effect
            arduino_restored.append_line(b'9   ;2  ;12;1;0;1;1')
            # right: conclude
            arduino_restored.append_line(b'9   ;2  ;12;0;1;1;1')
            joystick_restored = get_joystick_from_driver_version(arduino_restored, filename=fp.name, game_pad_class=GamePadMock)
            joystick_restored.load_configuration()
            self.assertEqual(str(joystick_restored), expected_joystick_info)

    def test_joystick_update_with_invalid_input(self):
        arduino_v2 = SerialMock(lines=self._get_calibration_sequence() + [b'9   ;2  ;12;0;1;1;1', b'this is not a valid input'])
        joystick = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        joystick.calibrate()
        joystick.update()

    def test_joystick_update_with_valid_inputs(self):
        arduino_v2 = SerialMock(lines=self._get_calibration_sequence())
        # finish calibration
        arduino_v2.append_line(b'9   ;2  ;12;0;1;1;1')
        # play sequence 
        for line in self._get_play_sequence():
            arduino_v2.append_line(line)
        joystick = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        joystick.calibrate()
        for _ in range(len(self._get_play_sequence())):
            joystick.update()

    def test_calibrate_v1(self):
        arduino_v1 = SerialMock(lines=self._get_v1_calibration_sequence())
        joystick = get_joystick_from_driver_version(arduino_v1, game_pad_class=GamePadMock)
        # ------------------------ #
        # finish calibration
        arduino_v1.append_line(b'9   ;2  ;12;0;1')
        joystick.calibrate()

    def test_joystick_v1_update_with_invalid_input(self):
        arduino_v2 = SerialMock(lines=self._get_v1_calibration_sequence() + [b'9   ;2  ;12;0;1'] + self._get_play_sequence())
        joystick = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        joystick.calibrate()
        joystick.update()

    def test_joystick_v1_update_with_valid_input(self):
        arduino_v2 = SerialMock(lines=self._get_v1_calibration_sequence() + [b'9   ;2  ;12;0;1'] + self._get_v1_play_sequence())
        joystick = get_joystick_from_driver_version(arduino_v2, game_pad_class=GamePadMock)
        joystick.calibrate()
        joystick.update()

if __name__ == '__main__':
    unittest.main()