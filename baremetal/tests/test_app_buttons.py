# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'app_buttons', Path(__file__).resolve().parents[1] / 'app/seedsigner_port/buttons.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ButtonsTest(unittest.TestCase):
    def setUp(self):
        self.mask = 0
        self.now = 0
        self.input = module.ButtonInput(lambda: self.mask, lambda: self.now)

    def at(self, ms, mask=None, keys=None):
        self.now = ms
        if mask is not None:
            self.mask = mask
        return self.input.poll(keys)

    def test_debounce_and_repeats(self):
        self.assertIsNone(self.at(0, 1))
        self.assertIsNone(self.at(9))
        self.assertEqual(self.at(10), 'KEY_UP')
        self.assertIsNone(self.at(234))
        self.assertEqual(self.at(235), 'KEY_UP')
        self.assertIsNone(self.at(484))
        self.assertEqual(self.at(485), 'KEY_UP')

    def test_contact_bounce_restarts_debounce(self):
        self.at(0, 1)
        self.at(7, 0)
        self.at(9, 1)
        self.assertIsNone(self.at(18))
        self.assertEqual(self.at(19), 'KEY_UP')

    def test_release_cancels_repeat_and_allows_fresh_press(self):
        self.at(0, 1)
        self.at(10)
        self.at(20, 0)
        self.at(30)
        self.assertIsNone(self.at(500))
        self.at(501, 1)
        self.assertEqual(self.at(511), 'KEY_UP')

    def test_key_held_at_start_is_blocked_until_stable_release(self):
        self.mask = 64
        self.input.reset_input()
        self.assertIsNone(self.at(1000))
        self.at(1001, 0)
        self.at(1008, 64)
        self.assertIsNone(self.at(1100))
        self.at(1101, 0)
        self.at(1111)
        self.at(1112, 64)
        self.assertEqual(self.at(1122), 'KEY2')

    def test_priority_subsets_and_override(self):
        self.at(0, 3)
        self.assertEqual(self.at(10, keys=('KEY_DOWN', 'KEY_UP')), 'KEY_DOWN')
        self.assertEqual(self.at(10, keys=('KEY_UP',)), 'KEY_UP')
        self.input.trigger_override()
        self.assertEqual(self.at(11), 1000)

    def test_tick_wraparound(self):
        self.now = 0xFFFFFFF0
        self.input.reset_input()
        self.at(0xFFFFFFF8, 1)
        self.assertIsNone(self.at(1))
        self.assertEqual(self.at(2), 'KEY_UP')

    def test_reading_level_does_not_consume_event_and_reset_blocks_hold(self):
        self.at(0, 16)
        self.now = 10
        self.assertTrue(self.input.check_for_low('KEY_PRESS'))
        self.assertTrue(self.input.is_pressed('KEY_PRESS'))
        self.assertEqual(self.at(10), 'KEY_PRESS')
        self.input.reset_input()
        self.assertIsNone(self.at(1000))
