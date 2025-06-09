import os
import traceback


class LIMITS:
    LIMIT_ACC = 0.4

class _RangeAnalogInput:
    def __init__(self):
        self._min = 0
        self._max = 1023

    @property
    def min(self): return self._min
    @property
    def max(self): return self._max
    
    def load_from_csv_line(self, line): 
        m, M = line.strip().split(';')
        self.set_min(m)
        self.set_max(M)
    def load_from_csv_file(self, f): 
        m, M = f.readline().strip().split(';')
        self.set_min(m)
        self.set_max(M)
    def dump_to_file(self, f): f.write(str(self) + '\n')
    def set_min(self, value): self._min = int(value)
    def set_max(self, value): self._max = int(value)
    def set(self, min_value, max_value): self._min, self._max = int(min_value), int(max_value)

    def __str__(self): return str(self._min) + ';' + str(self._max)

class _AnalogState:
    def __init__(self):
        self._steer = 0
        self._throttle = 0
        self._break = 0

        self._range_steer = _RangeAnalogInput()
        self._range_throttle = _RangeAnalogInput()
        self._range_break = _RangeAnalogInput()
    
    @property
    def steer_raw(self): return self._steer
    @property
    def steer(self): return self._center_value(self._range_steer.min, self._range_steer.max, self._steer)
    @steer.setter
    def steer(self, value): self._steer = value

    @property
    def throttle_row(self): return self._throttle
    @property
    def throttle(self): return self._normalize_value(self._range_throttle.min, self._range_throttle.max, self._throttle)
    @throttle.setter
    def throttle(self, value): self._throttle = value

    @property
    def breakpedal_raw(self): return self._break
    @property
    def breakpedal(self): return -self._normalize_value(self._range_break.min, self._range_break.max, self._break)
    @breakpedal.setter
    def breakpedal(self, value): self._break = value

    @property
    def range_steer(self): return self._range_steer
    @property
    def range_throttle(self): return self._range_throttle
    @property
    def range_break(self): return self._range_break

    @property
    def acceleration(self):
        break_value = self.breakpedal
        if break_value < -LIMITS.LIMIT_ACC:
            return break_value
        throttle = self.throttle
        if throttle > LIMITS.LIMIT_ACC:
            return throttle
        return 0.0

    def dump_config(self, filename):
        with open(filename, 'w') as f:
            for range in [self._range_steer, self._range_throttle, self._range_break]:
                range.dump_to_file(f)

    def load_config(self, filename):
        if not os.path.exists(filename):
            print("™[WARNING] no configuration found! it is advisable to calibrate the joystic")
            return
        with open(filename) as f:
            self._range_steer.load_from_csv_file(f)
            self._range_throttle.load_from_csv_file(f)
            self._range_break.load_from_csv_file(f)

    def update(self, steer, throttle, break_value):
        self._steer = int(steer)
        self._throttle = int(throttle)
        self._break = int(break_value)

    def _center_value(self, min_, max_, x):
        return max(min(1.0, 2 * (x - min_) / (max_ - min_) - 1), -1.0)
    
    def _normalize_value(self, min_, max_, x):
        return max(min(1.0, (x-min_)/(max_-min_)), 0.0)


class _StateFullButton:
    def __init__(self):
        self._previous_value = 1
        self._current_value = 1 
        self._is_pressed = False
        self._has_changed = False

    def update(self, value):
        self._previous_value = self._current_value
        self._current_value = int(value)

        if self._is_pressed and self._previous_value == 0 and self._current_value == 1:
            self._has_changed = True
            self._is_pressed = False
        elif not self._is_pressed and self._previous_value == 1 and self._current_value == 0:
            self._has_changed = True
            self._is_pressed = True
        else:
            self._has_changed = False
    
    @property
    def has_change(self): return self._has_changed
    @property
    def is_pressed(self): return self._is_pressed


class _ArduinoState:
    def __init__(self, filename=None):
        self._filename = os.path.expanduser('~/.joystic_configuration') if filename is None else filename
        self._currentAnalogState = _AnalogState()
        self._gear_up = _StateFullButton()
        self._gear_down = _StateFullButton()
        self._btn_left = _StateFullButton()
        self._btn_right = _StateFullButton()

    # ======================================================================== #
    # CONFIGURATIONS
    def get_config(self): return self._filename

    def dump_config(self): self._currentAnalogState.dump_config(self.get_config())

    def load_config(self): self._currentAnalogState.load_config(self.get_config())

    # ======================================================================== #
    # CALIBRATION
    def set_min_steer(self, value):    self._currentAnalogState.range_steer.set_min(value)
    def set_max_steer(self, value):    self._currentAnalogState.range_steer.set_max(value)
    def set_min_throttle(self, value): self._currentAnalogState.range_throttle.set_min(value)
    def set_max_throttle(self, value): self._currentAnalogState.range_throttle.set_max(value)
    def set_min_break(self, value):    self._currentAnalogState.range_break.set_min(value)
    def set_max_break(self, value):    self._currentAnalogState.range_break.set_max(value)

    def set_range_steer(self, min_value, max_value):    self._currentAnalogState.range_steer.set(min_value, max_value)
    def set_range_throttle(self, min_value, max_value): self._currentAnalogState.range_throttle.set(min_value, max_value)
    def set_range_break(self, min_value, max_value):    self._currentAnalogState.range_break.set(min_value, max_value)

    # ======================================================================== #
    # UPDATE
    def update(self, steer, throttle, break_value, gear_up, gear_down, right_btn=1, left_btn=1):
        self._currentAnalogState.update(steer, throttle, break_value)
        self._gear_up.update(gear_up)
        self._gear_down.update(gear_down)
        self._btn_right.update(right_btn)
        self._btn_left.update(left_btn)

    def update_from_line(self, line):
        steer, break_value, throttle_value, gear_up, gear_down, right_btn, left_btn = line.decode('ascii').strip().split(';')
        self.update(steer, throttle_value, break_value, gear_up, gear_down, right_btn, left_btn)
    

    # ======================================================================== #
    # GETTER VALUES
    #   -- analog inputs --
    def get_steer(self):        return self._currentAnalogState.steer
    def get_raw_steer(self):    return self._currentAnalogState.steer_raw
    def get_throttle(self):     return self._currentAnalogState.throttle
    def get_raw_throttle(self): return self._currentAnalogState.throttle_row
    def get_break(self):        return self._currentAnalogState.breakpedal
    def get_raw_break(self):    return self._currentAnalogState.breakpedal_raw
    def get_acceleration(self): return self._currentAnalogState.acceleration

    def get_steer_range(self):    return str(self._currentAnalogState.range_steer)
    def get_throttle_range(self): return str(self._currentAnalogState.range_throttle)
    def get_break_range(self):    return str(self._currentAnalogState.range_break)

    #   -- buttons --
    def is_gear_up_changed(self): return self._gear_up.has_change
    def is_gear_up_pressed(self): return self._gear_up.is_pressed

    def is_gear_down_changed(self): return self._gear_down.has_change
    def is_gear_down_pressed(self): return self._gear_down.is_pressed

    def is_btn_right_changed(self): return self._btn_right.has_change
    def is_btn_right_pressed(self): return self._btn_right.is_pressed

    def is_btn_left_changed(self): return self._btn_left.has_change
    def is_btn_left_pressed(self): return self._btn_left.is_pressed

    def __str__(self):
        return (f'S:{self.get_steer():.2f}({self.get_raw_steer():.2f});' + 
                f'T:{self.get_throttle():.2f}({self.get_raw_throttle():.2f});' + 
                f'B:{self.get_break():.2f}({self.get_raw_break():.2f});' + 
                f'A:{self.get_acceleration():.2f};' + 
                f'Gu:{self.is_gear_up_pressed()};' + 
                f'Gd:{self.is_gear_down_pressed()};'
                f'L:{self.is_btn_left_pressed()};' + 
                f'R:{self.is_btn_right_pressed()}'
            )

class ArduinoStateV1(_ArduinoState):
    def update_from_line(self, line):
        steer, break_value, throttle_value, gear_up, gear_down = line.decode('ascii').strip().split(';')
        return super().update_from_line(steer, break_value, throttle_value, gear_up, gear_down)

class ArduinoStateV2(_ArduinoState):
    def update_from_line(self, line):
        return super().update_from_line(line)
