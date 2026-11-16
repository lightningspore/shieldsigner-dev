# SPDX-License-Identifier: MIT
"""Explicit current native bench capabilities; no Linux or storage emulation."""

from seedsigner_port.settings_schema import SettingsConstants as C, SettingsDefinition as D


class UnsupportedSettingsAction(NotImplementedError):
    pass


class NativeSettingsPlatform:
    def defaults(self):
        return {
            C.SETTING__PERSISTENT_SETTINGS: C.OPTION__DISABLED,
            C.SETTING__SMARTCARD_INTERFACES: [],
            C.SETTING__LOCALE: C.LOCALE__ENGLISH,
            C.SETTING__WORDLIST_LANGUAGE: C.WORDLIST_LANGUAGE__ENGLISH,
            C.SETTING__DISPLAY_CONFIGURATION: C.DISPLAY_CONFIGURATION__ST7789__240x240,
            C.SETTING__DISPLAY_COLOR_INVERTED: C.OPTION__DISABLED,
            C.SETTING__CAMERA_DEVICE: C.CAMERA_DEVICE__0,
            C.SETTING__CAMERA_ROTATION: 270,
            # No baremetal smartcard stack (out of current scope): routes
            # gated on these settings could only raise FeatureUnavailable.
            C.SETTING__SMARTCARD_SUPPORT: C.OPTION__DISABLED,
            C.SETTING__SATOCHIP_SUPPORT: C.OPTION__DISABLED,
            C.SETTING__KEYCARD_SUPPORT: C.OPTION__DISABLED,
            C.SETTING__SPECTER_DIY_SUPPORT: C.OPTION__DISABLED,
        }

    def check(self, key, value):
        # These are presently fixed capabilities, not successful driver actions.
        fixed = self.defaults()
        if key in fixed and value != fixed[key]:
            raise UnsupportedSettingsAction('Native setting action unavailable: ' + key)

    def default_value(self, key):
        fixed = self.defaults()
        if key in fixed:
            return fixed[key]
        return D.get_settings_entry(key).default_value

    def save(self, data):
        if data[C.SETTING__PERSISTENT_SETTINGS] != C.OPTION__DISABLED:
            raise UnsupportedSettingsAction(
                'Settings persistence has no native storage service yet'
            )
        # Disabled means RAM only. No write or deferred worker is represented.

    def load_locale(self, data):
        if data[C.SETTING__LOCALE] != C.LOCALE__ENGLISH:
            raise UnsupportedSettingsAction('Only frozen English assets are available')
