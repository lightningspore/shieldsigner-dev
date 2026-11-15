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
    def __init__(self, backend=None, buttons=None, clock=None, sleep=None, service=None):
        if backend is None:
            import ui
            backend = ui
        self.service = service
        self.backend = backend
        self.backend.init()
        self.buttons = buttons if buttons is not None else ButtonInput()
        self.clock = clock if clock is not None else time.ticks_ms
        self.sleep = sleep if sleep is not None else time.sleep_ms
        self.current = None
        self._button_count = None

    def show(self, builder, config):
        if not isinstance(config, dict):
            raise TypeError('Screen config must be a dict')
        self.backend.render(builder, json.dumps(config))
        # A held key belongs to the preceding screen. It must be released before
        # it can select an action on the new screen, including on startup.
        self.buttons.reset_input()
        self.current = builder
        self._button_count = None

    def poll(self):
        if self.current is None:
            raise RuntimeError('Show a screen before polling')
        if self.service is not None:self.service()
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

    def show_screen(self, screen_class, arguments, translate=None):
        from seedsigner_port.screen_contracts import configuration
        builder,config=configuration(screen_class,arguments,translate)
        self.show(builder,config)
        self._button_count=len(config.get('button_list',[]))
        self._screen_name=screen_class if isinstance(screen_class,str) else screen_class.__name__

    def screen_result(self, event):
        from seedsigner_port.screen_contracts import result
        if self._button_count is None:
            raise RuntimeError("Show an adapted app screen before interpreting its result")
        return result(event,self._button_count,self._screen_name)

    def run_screen(self, screen_class, arguments, timeout_ms=None, translate=None):
        self.show_screen(screen_class,arguments,translate)
        event=self.wait(timeout_ms)
        return None if event is None else self.screen_result(event)
