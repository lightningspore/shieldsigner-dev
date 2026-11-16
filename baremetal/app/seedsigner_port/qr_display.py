# SPDX-License-Identifier: MIT
"""Original QR output cadence over the existing native host-push QR screen.

Foreground port of firmware/lvgl-app/python/qr_output.py and the source
QRDisplayThread: no PIL rendering, transport subprocess or background thread.
"""

import time

# Original QRDisplayThread sleeps5/30seconds; native tick resolution is1ms.
_FRAME_INTERVAL_MS = 1000 / 6
_MAX_FRAME_BYTES = 512


def part_bytes(part):
    if isinstance(part, str):
        part = part.encode('utf-8')
    elif isinstance(part, (bytes, bytearray)):
        part = bytes(part)
    else:
        raise TypeError('QR encoder must return text or bytes')
    if not part or len(part) > _MAX_FRAME_BYTES:
        raise ValueError('QR payload outside reviewed512-byte bound')
    return part


def _elapsed(now, then):
    # Real MicroPython ticks_diff knows its ticks period; the fallback supports
    # monotonically sampled host fixture clocks without requiring a fake utime.
    if hasattr(time, 'ticks_diff'):
        return time.ticks_diff(now, then)
    return (now - then) & 0xFFFFFFFF


class _Frames:
    """Original next/hold/restart decisions, separated from widget/input I/O."""

    def __init__(self, encoder, now):
        self.encoder = encoder
        self.animated = encoder.seq_len() > 1
        first = encoder.next_part()
        self.binary = isinstance(first, (bytes, bytearray))
        self.first = part_bytes(first)
        self.previous = now
        self.tip_was_active = False

    def due(self, now, tip_active):
        if not self.animated or _elapsed(now, self.previous) < _FRAME_INTERVAL_MS:
            return None
        self.previous = now
        if self.tip_was_active and not tip_active:
            self.encoder.restart()
        self.tip_was_active = bool(tip_active)
        if not tip_active:
            return part_bytes(self.encoder.next_part())
        return None


class QRDisplayScreen:
    def __init__(self, qr_encoder, cancel_on_back=False, **kwargs):
        self.encoder = qr_encoder
        self.cancel_on_back = cancel_on_back
        if kwargs:
            from seedsigner_port.decode_platform import FeatureUnavailable

            raise FeatureUnavailable('QR screen arguments not reviewed')

    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.settings_store import Settings, SettingsConstants as C
        from seedsigner_port.localization import gettext as _

        renderer = Renderer.get_instance()
        settings = Settings.get_instance()
        brightness = settings.get_value(C.SETTING__QR_BRIGHTNESS)
        frames = _Frames(self.encoder, renderer.session.clock())
        cfg = {
            'qr_data': frames.first.hex(),
            'data_encoding': 'hex',
            'qr_mode': 'byte' if frames.binary else 'auto',
            'border': 2,
            'initial_brightness': brightness,
            'density_control': False,
            'show_brightness_tips': settings.get_value(C.SETTING__QR_BRIGHTNESS_TIPS)
            == C.OPTION__ENABLED,
            'brighter_text': _('Brighter'),
            'darker_text': _('Darker'),
        }
        try:
            renderer.session.show('qr_display_screen', cfg)
            while True:
                event = renderer.session.poll()
                if event is not None:
                    if event == 1000:
                        exit_key = 0
                    elif event[0] == 4:
                        if not 31 <= event[1] <= 255:
                            raise ValueError('Invalid native QR brightness')
                        brightness = event[1]
                        continue
                    elif event[0] == 1 and event[1] == 1000:
                        exit_key = renderer.backend.qr_exit_key()
                    else:
                        raise ValueError('Unexpected native QR event')
                    # Source saves brightness once on a normal key exit, not on
                    # interruption/error. Preserve its special left cancellation.
                    settings.set_value(C.SETTING__QR_BRIGHTNESS, brightness, save=False)
                    return 1000 if self.cancel_on_back and exit_key == 20 else None
                if frames.animated:
                    data = frames.due(renderer.session.clock(), renderer.backend.qr_tip_active())
                    if data is not None:
                        renderer.backend.qr_frame(data)
                renderer.session.sleep(5)
        finally:
            # Original native host's qr_output finally clears the owning root.
            renderer.display_blank_screen()
