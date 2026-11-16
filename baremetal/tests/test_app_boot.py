# SPDX-License-Identifier: MIT
"""Foreground entry ownership: exceptions must release camera and screen."""

import importlib, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from seedsigner_port import boot


class BootTest(unittest.TestCase):
    def execute(self, error=None, stop_error=None):
        events = []

        class Camera:
            def stop_video_stream_mode(self):
                events.append('stop')
                if stop_error:
                    raise stop_error

        class Controller:
            camera = Camera()

            @classmethod
            def get_instance(cls):
                return cls()

            def start(self):
                events.append('start')
                if error:
                    raise error

        class Renderer:
            session = types.SimpleNamespace(current='public_screen')

            @classmethod
            def get_instance(cls):
                return cls()

            def display_blank_screen(self):
                events.append('blank')

        modules = {
            'seedsigner_port.controller': types.SimpleNamespace(Controller=Controller),
            'seedsigner_port.renderer': types.SimpleNamespace(Renderer=Renderer),
        }
        with patch.dict(sys.modules, modules):
            try:
                boot.run()
            finally:
                self.assertEqual(events, ['start', 'stop', 'blank'])
                self.assertFalse(boot.running)

    def setUp(self):
        importlib.reload(boot)

    def test_returned(self):
        self.execute()
        self.assertEqual(boot.starts, 1)
        self.assertEqual(boot.last_exit, 'returned')

    def test_interrupt(self):
        with self.assertRaises(KeyboardInterrupt):
            self.execute(KeyboardInterrupt())
        self.assertEqual(boot.last_exit, 'KeyboardInterrupt')

    def test_stop_failure_still_blanks(self):
        with self.assertRaisesRegex(RuntimeError, 'stop failed'):
            self.execute(stop_error=RuntimeError('stop failed'))
        self.assertEqual(boot.last_exit, 'RuntimeError')

    def test_duplicate_entry_rejected(self):
        boot.running = True
        with self.assertRaisesRegex(RuntimeError, 'already running'):
            boot.run()
        self.assertEqual(boot.starts, 0)
