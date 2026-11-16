# SPDX-License-Identifier: MIT
"""Cooperative SeedSigner button input for MicroPython.

Key names and10/225/250ms timings follow the installed SeedSigner hardware
contract. No OS threads/GPIO handles; inject a mask reader and clock for tests.
Buttons already held at construction or reset are ignored until released.
"""

import time

NAMES = ('KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT', 'KEY_PRESS', 'KEY1', 'KEY2', 'KEY3')


class ButtonInput:
    def __init__(self, read_mask=None, clock=None, service=None):
        if read_mask is None:
            import display

            read_mask = display.buttons
        self._read = read_mask
        self._clock = clock if clock is not None else time.ticks_ms
        self._service = service
        self.override_ind = False
        self.reset_input()

    def reset_input(self):
        now = self._clock()
        self._raw = self._read() & 255
        self._stable = self._raw
        self._blocked = self._raw
        self._pending = 0
        self._since = [now] * 8
        self._last = [now] * 8
        self._delay = [225] * 8

    @staticmethod
    def _elapsed(now, before):
        return (now - before) & 0xFFFFFFFF

    def _update(self):
        now = self._clock()
        raw = self._read() & 255
        for index in range(8):
            bit = 1 << index
            if (raw ^ self._raw) & bit:
                self._since[index] = now
            if (raw ^ self._stable) & bit and self._elapsed(now, self._since[index]) >= 10:
                if raw & bit:
                    self._stable |= bit
                    if not self._blocked & bit:
                        self._pending |= bit
                else:
                    self._stable &= ~bit
                    self._blocked &= ~bit
                    self._pending &= ~bit
        self._raw = raw
        return now

    def poll(self, keys=None):
        now = self._update()
        if self.override_ind:
            self.override_ind = False
            return 1000
        if keys is None:
            keys = NAMES
        for key in keys:
            index = NAMES.index(key)
            bit = 1 << index
            if not self._stable & bit or self._blocked & bit:
                continue
            if self._pending & bit:
                self._pending &= ~bit
                self._last[index] = now
                self._delay[index] = 225
                return key
            if self._elapsed(now, self._last[index]) >= self._delay[index]:
                self._last[index] = now
                self._delay[index] = 250
                return key
        return None

    def wait_for(self, keys=None):
        while True:
            if self._service is not None:
                self._service()
            key = self.poll(keys)
            if key is not None:
                return key
            time.sleep_ms(5)

    def trigger_override(self):
        self.override_ind = True
        return True

    def is_pressed(self, key):
        return bool(self._read() & (1 << NAMES.index(key)))

    def check_for_low(self, key=None, keys=None):
        self._update()
        if keys is None:
            keys = NAMES if key is None else (key,)
        for name in keys:
            bit = 1 << NAMES.index(name)
            if self._stable & bit and not self._blocked & bit:
                return True
        return False
