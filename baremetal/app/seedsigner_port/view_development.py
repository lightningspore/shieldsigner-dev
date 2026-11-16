# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated from pinned original source; optional class bases resolve only on use.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination


def _make_DeveloperOSWarningView():

    class DeveloperOSWarningView(_dependency('seedsigner.views.view', 'View')):
        """Warn that the running image is not hardened for production use.

        Names what is actually open rather than just asserting "development build",
        so the message stays true as hardening evolves and a partially-hardened
        image says exactly what slipped. Kept terse: this is a 240x240 screen and a
        wall of text gets dismissed unread.
        """

        def run(self):
            exposures = _dependency('seedsigner.helpers', 'hardening').open_exposures()
            if exposures:
                text = (
                    _dependency('gettext', 'gettext')('Open: {items}.').format(
                        items=', '.join(exposures)
                    )
                    + ' '
                    + _dependency('gettext', 'gettext')(
                        'Usually means a development build. Do not use real seeds.'
                    )
                )
            else:
                text = _dependency('gettext', 'gettext')(
                    'Development build. Do not use real seeds.'
                )
            self.run_screen(
                _dependency('seedsigner.gui.screens.screen', 'WarningScreen'),
                title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
                    'Unhardened Build'
                ),
                status_headline=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
                    'Not secure!'
                ),
                text=text,
                button_data=[
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
                            'I Understand'
                        )
                    )
                ],
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(None)

        def __init__(self):
            self.__post_init__()

    return DeveloperOSWarningView


_FACTORIES = {'DeveloperOSWarningView': _make_DeveloperOSWarningView}
_CACHE = {}


def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:
            raise AttributeError(name)
        _CACHE[name] = _FACTORIES[name]()
    return _CACHE[name]


def __getattr__(name):
    return _resolve(name)
