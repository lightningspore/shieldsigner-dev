# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from seedsigner_port.buttons import ButtonInput
from seedsigner_port.native_ui import ScreenSession


class Backend:
    def __init__(self):
        self.keys = []
        self.ticks = 0
        self.events = []
        self.screens = []
        self.fail = False

    def init(self):
        pass

    def render(self, name, config):
        if self.fail:
            raise RuntimeError('unsupported')
        self.screens.append((name, json.loads(config)))

    def tick(self):
        self.ticks += 1

    def key(self, key, down):
        self.keys.append((key, down))

    def event(self):
        return self.events.pop(0) if self.events else None


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.mask = 0
        self.backend = Backend()
        self.buttons = ButtonInput(lambda: self.mask, lambda: self.now)

        def sleep(ms):
            self.now = (self.now + ms) & 0xFFFFFFFF

        self.session = ScreenSession(self.backend, self.buttons, lambda: self.now, sleep)

    def test_config_errors_and_service_without_input(self):
        with self.assertRaises(RuntimeError):
            self.session.poll()
        with self.assertRaises(TypeError):
            self.session.show('x', '{}')
        self.session.show('main_menu_screen', {'title': 'Quoted "é"'})
        self.assertEqual(self.backend.screens[0][1]['title'], 'Quoted "é"')
        self.assertIsNone(self.session.poll())
        self.assertEqual(self.backend.ticks, 1)
        self.backend.fail = True
        with self.assertRaises(RuntimeError):
            self.session.show('unsupported', {})
        self.assertEqual(self.session.current, 'main_menu_screen')

    def test_debounced_pulses_and_held_screen_transition(self):
        self.session.show('main_menu_screen', {})
        self.mask = 8
        self.session.poll()
        self.now = 10
        self.session.poll()
        self.assertEqual(self.backend.keys, [(19, True), (19, False)])
        self.session.show('main_menu_screen', {})
        self.now = 500
        self.session.poll()
        self.assertEqual(len(self.backend.keys), 2)
        self.mask = 0
        self.session.poll()
        self.now = 510
        self.session.poll()
        self.mask = 16
        self.now = 520
        self.session.poll()
        self.now = 530
        self.session.poll()
        self.assertEqual(self.backend.keys[-2:], [(10, True), (10, False)])

    def test_timeout_wrap_and_event_override(self):
        self.session.show('main_menu_screen', {})
        self.now = 0xFFFFFFF8
        self.assertIsNone(self.session.wait(20))
        self.assertEqual(self.now, 12)
        self.backend.events = [(1, 3, '')]
        self.assertEqual(self.session.wait(0), (1, 3, ''))
        self.buttons.trigger_override()
        self.assertEqual(self.session.poll(), 1000)
        with self.assertRaises(ValueError):
            self.session.wait(0x80000000)

    def test_app_screen_dispatch_and_result_validation(self):
        self.backend.events = [(1, 1, '')]
        self.assertEqual(
            self.session.run_screen('ButtonListScreen', {'button_data': ['A', 'B']}, 0), 1
        )
        self.assertEqual(self.backend.screens[-1][0], 'button_list_screen')
        self.assertEqual(self.session.screen_result((1, 1000, '')), 1000)
        with self.assertRaises(ValueError):
            self.session.screen_result((1, 2, ''))
        self.session.show('main_menu_screen', {})
        with self.assertRaises(RuntimeError):
            self.session.screen_result((1, 0, ''))
