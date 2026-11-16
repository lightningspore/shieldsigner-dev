# SPDX-License-Identifier: MIT
"""Original QR cadence/brightness/exit decisions; native pixels are separate gates."""

import json, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from seedsigner_port.qr_display import _Frames, part_bytes, QRDisplayScreen
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.settings_schema import SettingsConstants as C


class Encoder:
    def __init__(self, parts):
        self.parts = parts
        self.index = 0
        self.restarts = 0
        self.sent = []

    def seq_len(self):
        return len(self.parts)

    def next_part(self):
        value = self.parts[self.index % len(self.parts)]
        self.index += 1
        self.sent.append(value)
        return value

    def restart(self):
        self.index = 0
        self.restarts += 1


class FrameTests(unittest.TestCase):
    def test_source_one_sixth_second_hold_restart_and_order(self):
        encoder = Encoder(['p1of3 A', 'p2of3 B', 'p3of3 C'])
        frames = _Frames(encoder, 0)
        self.assertEqual(frames.first, b'p1of3 A')
        self.assertIsNone(frames.due(166, False))
        self.assertEqual(frames.due(167, False), b'p2of3 B')
        self.assertIsNone(frames.due(334, True))
        self.assertIsNone(frames.due(501, True))
        self.assertEqual(encoder.sent, ['p1of3 A', 'p2of3 B'])
        self.assertEqual(frames.due(668, False), b'p1of3 A')
        self.assertEqual(encoder.restarts, 1)
        self.assertEqual(frames.due(835, False), b'p2of3 B')

    def test_static_qr_does_not_advance(self):
        encoder = Encoder([b'PUBLIC\0\xff'])
        frames = _Frames(encoder, 0)
        for now in (1000, 2000, 100000):
            self.assertIsNone(frames.due(now, False))
        self.assertEqual(len(encoder.sent), 1)

    def test_payload_boundary_counts_utf8_bytes_and_preserves_binary(self):
        self.assertEqual(part_bytes(bytearray(b'PUBLIC\0\xff')), b'PUBLIC\0\xff')
        self.assertEqual(part_bytes('é'), 'é'.encode())
        for bad in ('', b'', b'x' * 513, 'é' * 257):
            with self.assertRaises(ValueError):
                part_bytes(bad)
        with self.assertRaises(TypeError):
            part_bytes(42)


class Clock:
    def __init__(self):
        self.now = 0

    def ticks(self):
        return self.now

    def sleep(self, amount):
        self.now += amount


class Buttons:
    def reset_input(self):
        pass

    def poll(self):
        return None


class Backend:
    def __init__(self, clock, events, tip=lambda now: False):
        self.clock = clock
        self.events = list(events)
        self.tip = tip
        self.frames = []
        self.blanks = 0
        self.exit_key = 10

    def init(self):
        pass

    def render(self, builder, encoded):
        self.builder = builder
        self.config = json.loads(encoded)

    def tick(self):
        pass

    def event(self):
        if self.events and self.clock.now >= self.events[0][0]:
            _, event = self.events.pop(0)
            if isinstance(event, BaseException):
                raise event
            return event

    def qr_frame(self, data):
        self.frames.append((self.clock.now, bytes(data)))

    def qr_tip_active(self):
        return self.tip(self.clock.now)

    def qr_exit_key(self):
        return self.exit_key

    def blank(self):
        self.blanks += 1


class DisplayTests(unittest.TestCase):
    def run_display(self, encoder, backend, cancel=False):
        clock = backend.clock
        settings = types.SimpleNamespace(
            values={C.SETTING__QR_BRIGHTNESS: 62, C.SETTING__QR_BRIGHTNESS_TIPS: C.OPTION__ENABLED},
            writes=[],
        )
        settings.get_value = lambda key: settings.values[key]
        settings.set_value = lambda key, value, save=False: settings.writes.append(
            (key, value, save)
        )
        renderer = types.SimpleNamespace(backend=backend)
        renderer.session = ScreenSession(
            backend=backend, buttons=Buttons(), clock=clock.ticks, sleep=clock.sleep
        )

        def blank():
            backend.blank()
            renderer.session.current = None

        renderer.display_blank_screen = blank
        modules = {
            'seedsigner_port.renderer': types.SimpleNamespace(
                Renderer=types.SimpleNamespace(get_instance=lambda: renderer)
            ),
            'seedsigner_port.settings_store': types.SimpleNamespace(
                Settings=types.SimpleNamespace(get_instance=lambda: settings), SettingsConstants=C
            ),
        }
        with patch.dict(sys.modules, modules):
            result = QRDisplayScreen(encoder, cancel_on_back=cancel).display()
        return result, settings

    def test_original_animated_cadence_and_native_tip_hold(self):
        clock = Clock()
        backend = Backend(clock, [(850, (1, 1000, ''))], lambda now: 200 <= now < 600)
        result, settings = self.run_display(Encoder(['A', 'B', 'C']), backend)
        self.assertIsNone(result)
        self.assertEqual([data for _, data in backend.frames], [b'B', b'A'])
        # Polling every5ms rounds the original1/6second boundary upward.
        self.assertEqual([at for at, _ in backend.frames], [170, 680])
        self.assertEqual(backend.blanks, 1)

    def test_brightness_persisted_once_and_actual_left_cancel(self):
        clock = Clock()
        backend = Backend(clock, [(0, (4, 31, '')), (5, (1, 1000, ''))])
        backend.exit_key = 20
        result, settings = self.run_display(Encoder([b'PUBLIC']), backend, True)
        self.assertEqual(result, 1000)
        self.assertEqual(settings.writes, [(C.SETTING__QR_BRIGHTNESS, 31, False)])
        self.assertEqual(backend.config['qr_mode'], 'byte')
        self.assertEqual(backend.blanks, 1)

    def test_keyboard_interrupt_releases_native_screen(self):
        clock = Clock()
        backend = Backend(clock, [(170, KeyboardInterrupt())])
        with self.assertRaises(KeyboardInterrupt):
            self.run_display(Encoder(['A', 'B']), backend)
        self.assertEqual(backend.blanks, 1)
