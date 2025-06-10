import unittest
import os
import tempfile

from virtual_steering_wheel.joystick.arduino_state import LIMITS, ArduinoStateV1, ArduinoStateV2

class TestArduinoState(unittest.TestCase):

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.ERROR_DELTA = 0.001
        self.PRESSED = 0
        self.UNPRESSED = 1

    def get_numeric_range(self, state, func_name):
        f1 = getattr(state, func_name)
        m, M = f1().split(';')
        return int(m), int(M)

    # ======================================================================== #
    # CONFIGURATIONS
    def test_default_constructor(self):
        state = ArduinoStateV2()
        filename = os.path.expanduser('~/.joystic_configuration')
        name_config = state.get_config()
        self.assertEqual(filename, name_config)

    def test_constructor_with_filename(self):
        path = 'configuration_for_test.txt'
        state = ArduinoStateV2(path)
        name_config = state.get_config()
        self.assertEqual(path, name_config)
    
    def test_default_configuration_dumps(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False)
            fp.write(b'Hello world!')
            fp.close()
            state = ArduinoStateV2(fp.name)
            state.dump_config()
            expcted_lines = ['0;1023\n', '0;1023\n', '0;1023\n']
            with open(fp.name) as f:
                lines = f.readlines()
                self.assertEqual(lines, expcted_lines)
        finally:
            os.remove(fp.name)

    def test_configuration_dumps_min_max(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False)
            fp.write(b'Hello world!')
            fp.close()
            state = ArduinoStateV2(fp.name)
            state.set_range_steer(-999, 1234)
            state.set_range_throttle(23, 1002)
            state.set_range_break(13, 314)
            state.dump_config()
            expcted_lines = ['-999;1234\n', '23;1002\n', '13;314\n']
            with open(fp.name) as f:
                lines = f.readlines()
                self.assertEqual(lines, expcted_lines)
        finally:
            os.remove(fp.name)

    def test_configuration_dumps_single_update(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False)
            fp.write(b'Hello world!')
            fp.close()
            state = ArduinoStateV2(fp.name)
            state.set_min_steer(-999)
            state.set_max_steer(1234)
            state.set_min_throttle(23)
            state.set_max_throttle(1002)
            state.set_min_break(13)
            state.set_max_break(314)
            state.dump_config()
            expcted_lines = ['-999;1234\n', '23;1002\n', '13;314\n']
            with open(fp.name) as f:
                lines = f.readlines()
                self.assertEqual(lines, expcted_lines)
        finally:
            os.remove(fp.name)

    def test_configuration_load(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False)
            state = ArduinoStateV2(fp.name)
            loaded_state = ArduinoStateV2(fp.name)
            fp.write(b'Hello world!')
            fp.close()
            state.set_range_steer(-999, 1234)
            state.set_range_throttle(23, 1002)
            state.set_range_break(13, 314)
            state.dump_config()
            loaded_state.load_config()
            for func_name in [
                'get_steer_range',
                'get_throttle_range',
                'get_break_range',
            ]:
                f1, f2 = getattr(state, func_name), getattr(loaded_state, func_name)
                v1, v2 = f1(), f2()
            self.assertEqual(v1, v2)
        finally:
            os.remove(fp.name)

    def test_configuration_load_file_not_found(self):
        with tempfile.NamedTemporaryFile() as fp:
            state = ArduinoStateV2(fp.name + 'asdfghjkasdfghjkasdfghjk')
            self.assertEqual(state.get_break_range(), '0;1023')
            state.load_config()
            self.assertEqual(state.get_break_range(), '0;1023')
        
    # ======================================================================== #
    # STEERING
    def test_update_steering_left(self):
        state = ArduinoStateV2()
        state.update(0, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), 0)
        self.assertEqual(state.get_steer(), -1.0)

    def test_update_steering_right(self):
        state = ArduinoStateV2()
        state.update(1023, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), 1023)
        self.assertEqual(state.get_steer(), 1.0)

    def test_update_steering_center(self):
        state = ArduinoStateV2()
        m, M = self.get_numeric_range(state, 'get_steer_range')
        state.update((m + M) // 2, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), (m + M) // 2)
        self.assertAlmostEquals(state.get_steer(), 0.0, delta=self.ERROR_DELTA)

    def test_update_steering_left_shifted_range_below_min(self):
        state = ArduinoStateV2()
        state.set_range_steer(3, 999)
        state.update(0, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), 0)
        self.assertEqual(state.get_steer(), -1.0)

    def test_update_steering_right_shifted_range_above_max(self):
        state = ArduinoStateV2()
        state.set_range_steer(3, 999)
        state.update(1024, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), 1024)
        self.assertEqual(state.get_steer(), 1.0)

    def test_update_steering_center_shifted_range(self):
        state = ArduinoStateV2()
        state.set_range_steer(3, 999)
        m, M = self.get_numeric_range(state, 'get_steer_range')
        state.update((m + M) // 2, 0, 0, 1, 1)
        self.assertEqual(state.get_raw_steer(), (m + M) // 2)
        self.assertAlmostEquals(state.get_steer(), 0.0, delta=self.ERROR_DELTA)

    # ======================================================================== #
    # THROTTLE
    def test_update_throttle_middle(self):
        state = ArduinoStateV2()
        m, M = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, (m + M) / 2, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), (m + M) // 2)
        self.assertAlmostEqual(state.get_throttle(), 0.5, delta=self.ERROR_DELTA)

    def test_update_throttle_above_max(self):
        state = ArduinoStateV2()
        _, M = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, M + 10, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), M + 10)
        self.assertAlmostEqual(state.get_throttle(), 1.0, delta=self.ERROR_DELTA)

    def test_update_throttle_below_max(self):
        state = ArduinoStateV2()
        m, _ = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, m - 10, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), m - 10)
        self.assertAlmostEqual(state.get_throttle(), 0.0, delta=self.ERROR_DELTA)

    def test_update_throttle_middle_shifted_range(self):
        state = ArduinoStateV2()
        state.set_range_throttle(22, 876)
        m, M = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, (m + M) / 2, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), (m + M) // 2)
        self.assertAlmostEqual(state.get_throttle(), 0.5, delta=self.ERROR_DELTA)

    def test_update_throttle_above_max_shifted_range(self):
        state = ArduinoStateV2()
        state.set_range_throttle(22, 876)
        _, M = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, M + 10, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), M + 10)
        self.assertAlmostEqual(state.get_throttle(), 1.0, delta=self.ERROR_DELTA)

    def test_update_throttle_below_max_shifted_range(self):
        state = ArduinoStateV2()
        state.set_range_throttle(22, 876)
        m, _ = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, m - 10, 0, 1, 1)
        self.assertEqual(state.get_raw_throttle(), m - 10)
        self.assertAlmostEqual(state.get_throttle(), 0.0, delta=self.ERROR_DELTA)

    # ======================================================================== #
    # BREAK
    def test_update_break_middle(self):
        state = ArduinoStateV2()
        m, M = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, (m + M) / 2, 1, 1)
        self.assertEqual(state.get_raw_break(), (m + M) // 2)
        self.assertAlmostEqual(state.get_break(), -0.5, delta=self.ERROR_DELTA)

    def test_update_break_above_max(self):
        state = ArduinoStateV2()
        _, M = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, M + 10, 1, 1)
        self.assertEqual(state.get_raw_break(), M + 10)
        self.assertAlmostEqual(state.get_break(), -1.0, delta=self.ERROR_DELTA)

    def test_update_break_below_max(self):
        state = ArduinoStateV2()
        m, _ = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, m - 10, 1, 1)
        self.assertEqual(state.get_raw_break(), m - 10)
        self.assertAlmostEqual(state.get_break(), 0.0, delta=self.ERROR_DELTA)

    def test_update_break_middle_shifted_range(self):
        state = ArduinoStateV2()
        m, M = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, (m + M) / 2, 1, 1)
        self.assertEqual(state.get_raw_break(), (m + M) // 2)
        self.assertAlmostEqual(state.get_break(), -0.5, delta=self.ERROR_DELTA)

    def test_update_break_above_max_shifted_range(self):
        state = ArduinoStateV2()
        _, M = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, M + 10, 1, 1)
        self.assertEqual(state.get_raw_break(), M + 10)
        self.assertAlmostEqual(state.get_break(), -1.0, delta=self.ERROR_DELTA)

    def test_update_break_below_max_shifted_range(self):
        state = ArduinoStateV2()
        m, _ = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, m - 10, 1, 1)
        self.assertEqual(state.get_raw_break(), m - 10)
        self.assertAlmostEqual(state.get_break(), 0.0, delta=self.ERROR_DELTA)

    # ======================================================================== #
    # ACCELERATION
    def test_update_acceleration_middle(self):
        state = ArduinoStateV2()
        m, M = self.get_numeric_range(state, 'get_break_range')
        state.update(0, 0, (m + M) / 2, 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), -0.5, delta=self.ERROR_DELTA)

    def test_update_acceleration_between_limits(self):
        state = ArduinoStateV2()
        state.update(0, 0, LIMITS.LIMIT_ACC, 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), 0.0, delta=self.ERROR_DELTA)
        state.update(0, 0, -LIMITS.LIMIT_ACC, 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), 0.0, delta=self.ERROR_DELTA)

    def test_update_acceleration_above_max(self):
        state = ArduinoStateV2()
        _, M = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, M + 10, 0, 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), 1.0, delta=self.ERROR_DELTA)

    def test_update_acceleration_throttle_and_break_down_break_between_limits(self):
        state = ArduinoStateV2()
        mb, Mb = self.get_numeric_range(state, 'get_break_range')
        ma, Ma = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, 1 / (Ma - ma), 1 / (Mb - mb), 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), 0.0, delta=self.ERROR_DELTA)

    def test_update_acceleration_throttle_and_break_down_break_wins(self):
        state = ArduinoStateV2()
        _, Mb = self.get_numeric_range(state, 'get_break_range')
        _, Ma = self.get_numeric_range(state, 'get_throttle_range')
        state.update(0, Ma, Mb, 1, 1)
        self.assertAlmostEqual(state.get_acceleration(), -1.0, delta=self.ERROR_DELTA)

    # ======================================================================== #
    # GEAR UP
    def test_update_gear_up(self):
        state = ArduinoStateV2()
        self.assertFalse(state.is_gear_up_pressed())
        # -------
        state.update(0, 0, 0, self.PRESSED, self.UNPRESSED)
        self.assertTrue(state.is_gear_up_changed())
        self.assertTrue(state.is_gear_up_pressed())
        # -------
        state.update(0, 0, 0, self.PRESSED, self.UNPRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertTrue(state.is_gear_up_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.UNPRESSED)
        self.assertTrue(state.is_gear_up_changed())
        self.assertFalse(state.is_gear_up_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.UNPRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertFalse(state.is_gear_up_pressed())

    # ======================================================================== #
    # GEAR DOWN
    def test_update_gear_down(self):
        state = ArduinoStateV2()
        self.assertFalse(state.is_gear_up_pressed())
        self.assertFalse(state.is_gear_down_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.PRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertTrue(state.is_gear_down_changed())
        self.assertTrue(state.is_gear_down_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.PRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertFalse(state.is_gear_down_changed())
        self.assertTrue(state.is_gear_down_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.UNPRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertTrue(state.is_gear_down_changed())
        self.assertFalse(state.is_gear_down_pressed())
        # -------
        state.update(0, 0, 0, self.UNPRESSED, self.UNPRESSED)
        self.assertFalse(state.is_gear_up_changed())
        self.assertFalse(state.is_gear_down_changed())
        self.assertFalse(state.is_gear_down_pressed())

    # ======================================================================== #
    # UPDATE with input line
        state = ArduinoStateV2()
        events_expect = [
            (b'1023;0;1021;1;0;1;1', 'S:1.00(1023.00);T:1.00(1021.00);B:-0.00(0.00);A:1.00;Gu:False;Gd:True;L:False;R:False'),
            (b'0;1023;1021;1;1;1;1', 'S:-1.00(0.00);T:1.00(1021.00);B:-1.00(1023.00);A:-1.00;Gu:False;Gd:False;L:False;R:False')
        ]
        for line, expect in events_expect:
            state.update_from_line(line)
            self.assertEqual(str(state), expect)

    # ======================================================================== #
    # UPDATE version 1 with input line
        state = ArduinoStateV1()
        events_expect = [
            (b'1023;0;1021;1;0', 'S:1.00(1023.00);T:1.00(1021.00);B:-0.00(0.00);A:1.00;Gu:False;Gd:True;L:False;R:False'),
            (b'0;1023;1021;1;1', 'S:-1.00(0.00);T:1.00(1021.00);B:-1.00(1023.00);A:-1.00;Gu:False;Gd:False;L:False;R:False')
        ]
        for line, expect in events_expect:
            state.update_from_line(line)
            self.assertEqual(str(state), expect)

if __name__ == '__main__':
    unittest.main()