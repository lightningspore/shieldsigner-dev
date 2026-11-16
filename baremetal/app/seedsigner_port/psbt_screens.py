# SPDX-License-Identifier: MIT
"""PSBT-only facade for existing native screens; original Views own decisions."""

from seedsigner_port.psbt_screen_defaults import DEFAULTS
from seedsigner_port.decode_platform import FeatureUnavailable

NAMES = set(DEFAULTS)
_CACHE = {}


def ngettext(one, many, count):
    # The actual frozen catalog is English; other locales are rejected upstream.
    return one if count == 1 else many


class NativeScreen:
    def __init__(self, **kwargs):
        self.args = kwargs

    def display(self):
        from seedsigner_port.renderer import Renderer

        return Renderer.get_instance().run_screen(type(self), self.args)


def configuration(screen_class, passed, translate=None):
    from seedsigner_port.screen_contracts import configuration as base_configuration
    from seedsigner_port.psbt_contracts import configure

    name = screen_class if isinstance(screen_class, str) else screen_class.__name__
    if name not in NAMES:
        raise FeatureUnavailable('Native PSBT screen unavailable: ' + name)
    args = DEFAULTS[name].copy()
    args.update(passed)
    builder, cfg = base_configuration('ButtonListScreen', args, translate)
    return configure(name, args, cfg)


def __getattr__(name):
    if name not in NAMES:
        raise AttributeError(name)
    if name not in _CACHE:
        _CACHE[name] = type(name, (NativeScreen,), {})
    return _CACHE[name]
