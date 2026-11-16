# SPDX-License-Identifier: MIT
"""Foreground services backed by actual native APIs; no OS/thread emulation."""

import ui
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.gui_constants import GUIConstants
from seedsigner_port import clock


class NativeIdleWipe(BaseException):
    pass


class CameraConnectionError(Exception):
    pass


class ScreensaverScreen:
    def __init__(self, buttons=None):
        self.buttons = buttons

    @property
    def is_running(self):
        return bool(ui.overlays(4))

    def start(self):
        ui.overlays(1)

    def stop(self):
        ui.overlays(2)


class InfoToast:
    def __init__(self, label_text, activation_delay=0, duration=3):
        if activation_delay:
            raise FeatureUnavailable('Delayed toast scheduling unavailable')
        self.label_text = label_text
        self.duration = duration

    def start(self):
        ui.toast(
            self.label_text,
            '',
            int(GUIConstants.INFO_COLOR[1:], 16),
            0xFFFFFF,
            int(self.duration * 1000),
        )

    def stop(self):
        ui.overlays(5)

    def is_alive(self):
        return bool(ui.overlays(6))

    def toggle_renderer_lock(self):
        raise FeatureUnavailable('Toast suspension/resumption not ported')


def is_testing_build_enabled():
    return False  # This image contains no factory-test application flag.


def open_exposures():
    return ['USB Python console', 'unqualified entropy']
