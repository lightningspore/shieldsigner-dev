# SPDX-License-Identifier: MIT
"""Cooperative adapter from app screen configs and buttons to real native LVGL.

No wallet/controller flow lives here. Screen names/configs stay the upstream
screen-library contract; unsupported builders raise instead of drawing fallbacks.
Key codes match firmware/lvgl-app/python/runtime.py and native navigation.cpp.
"""
import json
import time
from seedsigner_port.buttons import ButtonInput

KEYS = {'KEY_UP':17, 'KEY_DOWN':18, 'KEY_LEFT':20, 'KEY_RIGHT':19,
        'KEY_PRESS':10, 'KEY1':49, 'KEY2':50, 'KEY3':51}

class ScreenSession:
    def __init__(self, backend=None, buttons=None, clock=None, sleep=None):
        if backend is None:
            import ui
            backend = ui
        self.backend = backend
        self.backend.init()
        self.buttons = buttons if buttons is not None else ButtonInput()
        self.clock = clock if clock is not None else time.ticks_ms
        self.sleep = sleep if sleep is not None else time.sleep_ms
        self.current = None

    def show(self, builder, config):
        if not isinstance(config, dict):
            raise TypeError('Screen config must be a dict')
        self.backend.render(builder, json.dumps(config))
        # A held key belongs to the preceding screen. It must be released before
        # it can select an action on the new screen, including on startup.
        self.buttons.reset_input()
        self.current = builder

    def poll(self):
        if self.current is None:
            raise RuntimeError('Show a screen before polling')
        self.backend.tick()
        key = self.buttons.poll()
        if key == 1000:
            return 1000  # Existing ButtonInput override contract, handled by View.
        if key is not None:
            code = KEYS[key]
            # Debounce/repeat is owned by ButtonInput. Emit one complete native
            # pulse per accepted event so LVGL does not add a second repeat clock.
            self.backend.key(code, True)
            self.backend.key(code, False)
        return self.backend.event()

    def wait(self, timeout_ms=None):
        if timeout_ms is not None and (timeout_ms < 0 or timeout_ms > 0x7fffffff):
            raise ValueError('Timeout outside wrap-safe interval')
        start = self.clock()
        while True:
            event = self.poll()
            if event is not None:
                return event
            if timeout_ms is not None and ((self.clock()-start)&0xffffffff) >= timeout_ms:
                return None
            self.sleep(5)

    def run(self, builder, config, timeout_ms=None):
        self.show(builder, config)
        return self.wait(timeout_ms)
