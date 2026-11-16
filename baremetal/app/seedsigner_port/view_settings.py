# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original settings Views; unported OS/hardware utilities stay unavailable.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable


def _make_SettingsMenuView():

    class SettingsMenuView(_dependency('seedsigner.views.view', 'View')):
        ADVANCED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Advanced',
            right_icon_name=_dependency(
                'seedsigner.gui.components', 'SeedSignerIconConstants'
            ).CHEVRON_RIGHT,
        )
        HARDWARE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Hardware',
            right_icon_name=_dependency(
                'seedsigner.gui.components', 'SeedSignerIconConstants'
            ).CHEVRON_RIGHT,
        )
        IO_TEST = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I/O test')
        SCARD_TEST = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Test Smartcard')
        LIST_READERS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'List card readers'
        )
        NFC_TEST = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Test NFC Scan')
        DONATE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Donate')
        RESTART_PCSC = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Restart PCSC')
        BATTERY_INFO = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Battery info')
        SYSTEM_INFO = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('System info')
        MEMORY_INFO = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Memory info')
        TEST_HARDENING = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Test hardening'
        )
        LOAD_BACKUP_FILES = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Load Backup Files',
            right_icon_name=_dependency(
                'seedsigner.gui.components', 'SeedSignerIconConstants'
            ).CHEVRON_RIGHT,
        )
        VERSION = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Version')

        def __init__(
            self,
            visibility=_dependency(
                'seedsigner.models.settings', 'SettingsConstants'
            ).VISIBILITY__GENERAL,
            selected_attr=None,
            selected_button_option=None,
            initial_scroll=0,
        ):
            super().__init__()
            self.visibility = visibility
            self.selected_attr = selected_attr
            self.selected_button_option = selected_button_option
            self.initial_scroll = initial_scroll

        def run(self):
            settings_entries = _dependency(
                'seedsigner.models.settings', 'SettingsDefinition'
            ).get_settings_entries(visibility=self.visibility)
            button_data = [
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(e.display_name)
                for e in settings_entries
            ]
            advanced_destination = None
            hardware_destination = None
            selected_button = 0
            if self.selected_attr:
                for i, entry in enumerate(settings_entries):
                    if entry.attr_name == self.selected_attr:
                        selected_button = i
                        break
            if (
                self.visibility
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).VISIBILITY__GENERAL
            ):
                title = _dependency('gettext', 'gettext')('Settings')
                button_data.append(self.ADVANCED)
                button_data.append(self.HARDWARE)
                advanced_destination = _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__ADVANCED
                    },
                )
                hardware_destination = _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__HARDWARE
                    },
                )
                if (
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).SETTING__SMARTCARD_SUPPORT
                    )
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).OPTION__ENABLED
                ):
                    button_data.append(self.RESTART_PCSC)
                button_data.append(self.DONATE)
                button_data.append(self.VERSION)
            elif (
                self.visibility
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).VISIBILITY__ADVANCED
            ):
                title = _dependency('gettext', 'gettext')('Advanced')
                button_data.append(self.LOAD_BACKUP_FILES)
                button_data.append(self.TEST_HARDENING)
                button_data.append(self.HARDWARE)
                hardware_destination = _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__HARDWARE
                    },
                )
            elif (
                self.visibility
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).VISIBILITY__HARDWARE
            ):
                title = 'Hardware'
                button_data.append(self.SYSTEM_INFO)
                button_data.append(self.MEMORY_INFO)
                button_data.append(self.BATTERY_INFO)
                button_data.append(self.IO_TEST)
                if (
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).SETTING__SMARTCARD_SUPPORT
                    )
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).OPTION__ENABLED
                ):
                    button_data.append(self.LIST_READERS)
                    button_data.append(self.SCARD_TEST)
                    button_data.append(self.NFC_TEST)
            elif (
                self.visibility
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).VISIBILITY__DEVELOPER
            ):
                title = _dependency('gettext', 'gettext')('Dev Options')
            selected_button = 0
            if self.selected_button_option:
                selected_button = button_data.index(self.selected_button_option)
            elif self.selected_attr:
                for i, entry in enumerate(settings_entries):
                    if entry.attr_name == self.selected_attr:
                        selected_button = i
                        break
            selected_menu_num = self.run_screen(
                _dependency('seedsigner_port.settings_screens', 'SettingsButtonListScreen'),
                title=title,
                is_button_text_centered=False,
                button_data=button_data,
                selected_button=selected_button,
                scroll_y_initial_offset=self.initial_scroll,
            )
            initial_scroll = self.screen.scroll_y
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if (
                    self.visibility
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__GENERAL
                ):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'MainMenuView')
                    )
                elif (
                    self.visibility
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__ADVANCED
                ):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('SettingsMenuView')
                    )
                elif (
                    self.visibility
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__HARDWARE
                ):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('SettingsMenuView')
                    )
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('SettingsMenuView'),
                        view_args={
                            'visibility': _dependency(
                                'seedsigner.models.settings', 'SettingsConstants'
                            ).VISIBILITY__ADVANCED
                        },
                    )
            if button_data[selected_menu_num] == self.ADVANCED:
                return advanced_destination
            elif button_data[selected_menu_num] == self.HARDWARE:
                return hardware_destination
            elif button_data[selected_menu_num] == self.LOAD_BACKUP_FILES:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('LoadBackupFilesSettingsView')
                )
            elif button_data[selected_menu_num] == self.TEST_HARDENING:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('HardeningTestView')
                )
            elif button_data[selected_menu_num] == self.IO_TEST:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('IOTestView')
                )
            elif button_data[selected_menu_num] == self.SCARD_TEST:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SCARDTestView')
                )
            elif button_data[selected_menu_num] == self.LIST_READERS:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SCardReaderTestView')
                )
            elif button_data[selected_menu_num] == self.NFC_TEST:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('NFCTestView')
                )
            elif button_data[selected_menu_num] == self.RESTART_PCSC:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('RestartPCSCView')
                )
            elif button_data[selected_menu_num] == self.DONATE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('DonateView')
                )
            elif button_data[selected_menu_num] == self.VERSION:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('VersionView')
                )
            elif button_data[selected_menu_num] == self.BATTERY_INFO:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('BatteryInfoView')
                )
            elif button_data[selected_menu_num] == self.SYSTEM_INFO:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SystemInfoView')
                )
            elif button_data[selected_menu_num] == self.MEMORY_INFO:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('MemoryInfoView')
                )
            elif (
                settings_entries[selected_menu_num].attr_name
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__ENCRYPTION_ITER
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingPBKDF2IterationsView'),
                    view_args=dict(
                        attr_name=settings_entries[selected_menu_num].attr_name,
                        parent_initial_scroll=initial_scroll,
                    ),
                )
            elif (
                settings_entries[selected_menu_num].attr_name
                == _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__LOCALE
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('LocaleSelectionView')
                )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsEntryUpdateSelectionView'),
                    view_args=dict(
                        attr_name=settings_entries[selected_menu_num].attr_name,
                        parent_initial_scroll=initial_scroll,
                    ),
                )

    return SettingsMenuView


def _make_LoadBackupFilesSettingsView():

    class LoadBackupFilesSettingsView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            settings_entries = [
                _dependency('seedsigner.models.settings', 'SettingsDefinition').get_settings_entry(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__BITBOX_BACKUP
                ),
                _dependency('seedsigner.models.settings', 'SettingsDefinition').get_settings_entry(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__PASSPORT_BACKUP
                ),
                _dependency('seedsigner.models.settings', 'SettingsDefinition').get_settings_entry(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__TAPSIGNER_BACKUP
                ),
            ]
            button_data = [
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(entry.display_name)
                for entry in settings_entries
            ]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner_port.settings_screens', 'SettingsButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Load Backup Files'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__ADVANCED
                    },
                )
            selected_entry = settings_entries[selected_menu_num]
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsEntryUpdateSelectionView'),
                view_args={
                    'attr_name': selected_entry.attr_name,
                    'parent_initial_scroll': 0,
                    'blocking_view': _resolve('LoadBackupFilesSettingsView'),
                },
            )

    return LoadBackupFilesSettingsView


def _make_SettingPBKDF2IterationsView():

    class SettingPBKDF2IterationsView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, attr_name, parent_initial_scroll=0):
            super().__init__()
            self.settings_entry = _dependency(
                'seedsigner.models.settings', 'SettingsDefinition'
            ).get_settings_entry(attr_name)
            self.initial_scroll = parent_initial_scroll
            self.initial_value = str(self.settings.get_value(self.settings_entry.attr_name))

        def run(self):
            ret_value = (
                _dependency('seedsigner_port.settings_screens', None)
                .SettingPBFDK2IterationsScreen(initial_value=self.initial_value)
                .display()
            )
            min_value = self.settings_entry.min_value
            max_value = self.settings_entry.max_value
            if ret_value == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView')
                )
            try:
                iter_value = int(ret_value)
            except (TypeError, ValueError):
                iter_value = None
            if iter_value is None or not min_value <= iter_value <= max_value:
                _dependency('seedsigner.gui.screens', 'WarningScreen')(
                    title='PBKDF2 Iterations Error',
                    show_back_button=False,
                    status_headline='out of range'.format(),
                    text='Value must be between {0} and {1}'.format(min_value, max_value),
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Try Again')
                    ],
                ).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingPBKDF2IterationsView'),
                    view_args=dict(
                        attr_name=self.settings_entry.attr_name,
                        parent_initial_scroll=self.initial_scroll,
                    ),
                    skip_current_view=True,
                )
            self.settings.set_value(attr_name=self.settings_entry.attr_name, value=iter_value)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView'),
                view_args={
                    'visibility': self.settings_entry.visibility,
                    'selected_attr': self.settings_entry.attr_name,
                    'initial_scroll': self.initial_scroll,
                },
            )

    return SettingPBKDF2IterationsView


def _make_LocaleSelectionView():

    class LocaleSelectionView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            cur_language_code = self.settings.get_value(
                _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__LOCALE
            )
            selected_button = 0
            button_data = []
            for i, (language_code, display_name) in enumerate(
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).get_detected_languages()
            ):
                button_data.append(
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        button_label=display_name,
                        return_data=language_code,
                        font_name=_dependency(
                            'seedsigner.gui.components', 'GUIConstants'
                        ).get_button_font_name(language_code),
                        font_size=_dependency(
                            'seedsigner.gui.components', 'GUIConstants'
                        ).get_button_font_size(language_code),
                    )
                )
                if language_code == cur_language_code:
                    selected_button = i
            selected_menu_num = self.run_screen(
                _dependency(
                    'seedsigner_port.settings_screens', None
                ).SettingsEntryUpdateSelectionScreen,
                display_name=_dependency('gettext', 'gettext')(
                    _dependency('seedsigner.models.settings', 'SettingsDefinition')
                    .get_settings_entry(
                        attr_name=_dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).SETTING__LOCALE
                    )
                    .display_name
                ),
                button_data=button_data,
                selected_button=selected_button,
                checked_buttons=[selected_button],
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView')
                )
            self.settings.set_value(
                _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__LOCALE,
                button_data[selected_menu_num].return_data,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView')
            )

    return LocaleSelectionView


def _make_SettingsEntryUpdateSelectionView():

    class SettingsEntryUpdateSelectionView(_dependency('seedsigner.views.view', 'View')):
        """
        Handles changes to all selection-type settings (Multiselect, SELECT_1,
        Enabled/Disabled, etc).
        """

        def __init__(
            self,
            attr_name,
            parent_initial_scroll=0,
            selected_button=None,
            blocking_view=None,
            unblocking_view=None,
        ):
            super().__init__()
            self.settings_entry = _dependency(
                'seedsigner.models.settings', 'SettingsDefinition'
            ).get_settings_entry(attr_name)
            self.selected_button = selected_button
            self.parent_initial_scroll = parent_initial_scroll
            self.blocking_view = blocking_view
            self.unblocking_view = unblocking_view

        def run(self):
            initial_value = self.settings.get_value(self.settings_entry.attr_name)
            button_data = []
            checked_buttons = []
            if not self.settings_entry.selection_options:
                button_data.append(
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        _dependency('gettext', 'gettext')('No options available')
                    )
                )
                self.selected_button = 0
            else:
                for i, value in enumerate(self.settings_entry.selection_options):
                    if type(value) == tuple:
                        value, display_name = value
                    else:
                        display_name = value
                    button_data.append(
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(display_name)
                    )
                    if (
                        type(initial_value) == list
                        and value in initial_value
                        or value == initial_value
                    ):
                        checked_buttons.append(i)
                        if self.selected_button is None:
                            self.selected_button = i
                if self.selected_button is None:
                    self.selected_button = 0
            ret_value = self.run_screen(
                _dependency(
                    'seedsigner_port.settings_screens', None
                ).SettingsEntryUpdateSelectionScreen,
                display_name=self.settings_entry.display_name,
                help_text=self.settings_entry.help_text,
                button_data=button_data,
                selected_button=self.selected_button,
                checked_buttons=checked_buttons,
                settings_entry_type=self.settings_entry.type,
            )
            destination = None
            settings_menu_view_destination = _dependency(
                'seedsigner_port.navigation', 'Destination'
            )(
                _resolve('SettingsMenuView'),
                view_args={
                    'visibility': self.settings_entry.visibility,
                    'selected_attr': self.settings_entry.attr_name,
                    'initial_scroll': self.parent_initial_scroll,
                },
            )
            if ret_value == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if (
                    self.settings_entry.type
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).TYPE__MULTISELECT
                ):
                    if not initial_value:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('SettingsSelectionRequiredWarningView'),
                            view_args={'attr_name': self.settings_entry.attr_name},
                        )
                if self.blocking_view:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        self.blocking_view, clear_history=True
                    )
                return settings_menu_view_destination
            value = self.settings_entry.get_selection_option_value(ret_value)
            if (
                self.settings_entry.type
                == _dependency('seedsigner.models.settings', 'SettingsConstants').TYPE__FREE_ENTRY
            ):
                updated_value = ret_value
                destination = settings_menu_view_destination
            elif (
                self.settings_entry.type
                == _dependency('seedsigner.models.settings', 'SettingsConstants').TYPE__MULTISELECT
            ):
                updated_value = list(initial_value)
                if ret_value not in checked_buttons:
                    updated_value.append(value)
                else:
                    updated_value.remove(value)
            elif value == initial_value and (not self.blocking_view):
                return settings_menu_view_destination
            else:
                updated_value = value
            self.settings.set_value(attr_name=self.settings_entry.attr_name, value=updated_value)
            if (
                self.settings_entry.attr_name
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__DISPLAY_CONFIGURATION
            ):
                self.renderer.initialize_display()
            elif (
                self.settings_entry.attr_name
                == _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__DISPLAY_COLOR_INVERTED
            ):
                self.renderer.disp.set_color_inversion(
                    updated_value
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).OPTION__ENABLED
                )
            if destination:
                return destination
            if self.blocking_view:
                current_value = self.settings.get_value(self.settings_entry.attr_name)
                if current_value == initial_value:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        self.blocking_view, clear_history=True
                    )
                elif self.unblocking_view:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        self.unblocking_view, clear_history=True
                    )
            self.selected_button = ret_value
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsEntryUpdateSelectionView'),
                view_args=dict(
                    attr_name=self.settings_entry.attr_name,
                    parent_initial_scroll=self.parent_initial_scroll,
                    selected_button=self.selected_button,
                    blocking_view=self.blocking_view,
                    unblocking_view=self.unblocking_view,
                ),
                skip_current_view=True,
            )

    return SettingsEntryUpdateSelectionView


def _make_SettingsSelectionRequiredWarningView():

    class SettingsSelectionRequiredWarningView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, attr_name):
            super().__init__()
            self.settings_entry = _dependency(
                'seedsigner.models.settings', 'SettingsDefinition'
            ).get_settings_entry(attr_name)

        def run(self):
            title = _dependency('gettext', 'gettext')('Selection Required')
            text = _dependency('gettext', 'gettext')(
                'At least one option must be selected for "{}".'
            ).format(self.settings_entry.display_name)
            button_text = _dependency('gettext', 'gettext')('Return to setting')
            self.run_screen(
                _dependency('seedsigner.gui.screens.screen', 'WarningScreen'),
                title=title,
                status_headline=None,
                text=text,
                button_data=[
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(button_text)
                ],
                show_back_button=False,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsEntryUpdateSelectionView'),
                view_args=dict(attr_name=self.settings_entry.attr_name),
            )

    return SettingsSelectionRequiredWarningView


def _make_SettingsIngestSettingsQRView():

    class SettingsIngestSettingsQRView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, data):
            super().__init__()
            self.config_name, self.settings_update_dict = _dependency(
                'seedsigner.models.settings', 'Settings'
            ).parse_settingsqr(data)
            self.changes_display_driver = (
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__DISPLAY_CONFIGURATION
                in self.settings_update_dict
                and self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__DISPLAY_CONFIGURATION
                )
                != self.settings_update_dict[
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__DISPLAY_CONFIGURATION
                ]
            )
            self.changes_color_inverted = (
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__DISPLAY_COLOR_INVERTED
                in self.settings_update_dict
                and self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__DISPLAY_COLOR_INVERTED
                )
                != self.settings_update_dict[
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__DISPLAY_COLOR_INVERTED
                ]
            )

        def _apply_settings(self):
            """
            Applies the parsed SettingsQR values. Only called after the user confirms
            on the review screen so a scanned QR never mutates settings on its own.
            """
            self.settings.update(self.settings_update_dict)
            if self.changes_display_driver:
                self.renderer.initialize_display()
            elif self.changes_color_inverted:
                self.renderer.disp.set_color_inversion(
                    self.settings_update_dict[
                        _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).SETTING__DISPLAY_COLOR_INVERTED
                    ]
                    == _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).OPTION__ENABLED
                )
            if (
                _dependency('seedsigner.hardware.microsd', 'MicroSD').get_instance().is_inserted
                and self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__PERSISTENT_SETTINGS
                )
                == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED
            ):
                self.status_message = _dependency('gettext', 'gettext')(
                    'Persistent Settings enabled. Settings saved to SD card.'
                )
            else:
                self.status_message = _dependency('gettext', 'gettext')(
                    'Settings updated in temporary memory'
                )

        def run(self):
            button_idx = self.run_screen(
                _dependency('seedsigner.gui.screens.settings_screens', 'SettingsQRReviewScreen'),
                title=_dependency('gettext', 'gettext')('Settings QR'),
                config_name=self.config_name,
            )
            if button_idx != 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'MainMenuView')
                )
            self._apply_settings()
            self.run_screen(
                _dependency(
                    'seedsigner.gui.screens.settings_screens', 'SettingsQRConfirmationScreen'
                ),
                title=_dependency('gettext', 'gettext')('Settings QR'),
                config_name=self.config_name,
                status_message=self.status_message,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView')
            )

    return SettingsIngestSettingsQRView


def _make_IOTestView():

    class IOTestView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.run_screen(_dependency('seedsigner_port.settings_screens', None).IOTestScreen)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView')
            )

    return IOTestView


def _make_SCardReaderTestView():

    class SCardReaderTestView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            try:
                available_readers = _dependency('smartcard.System', 'readers')()
                if available_readers:
                    available_readers_text = '\n'.join(
                        (str(item)[:-5] for item in available_readers)
                    )
                    print(available_readers_text)
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'),
                        title='Found Readers:',
                        status_headline=None,
                        text=available_readers_text,
                        show_back_button=False,
                    )
                else:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title='Failure',
                        status_headline=None,
                        text='No Smartcard readers found...'.format(),
                        show_back_button=True,
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
            except _dependency('smartcard.Exceptions', 'ListReadersException'):
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='PCSC Failure',
                    status_headline=None,
                    text='Unable to list readers (A restart may help, possibly faulty reader)'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            except _dependency('smartcard.pcsc.PCSCExceptions', 'EstablishContextException'):
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='PCSC Failure',
                    status_headline=None,
                    text='Unable to establish PCSC context(A restart may help, possibly faulty reader)'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'BackStackView')
            )

    return SCardReaderTestView


def _make_SCARDTestView():

    class SCARDTestView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.loading_screen = _dependency(
                'seedsigner.gui.screens.screen', 'LoadingScreenThread'
            )(text='Scanning for Smart Card')
            self.loading_screen.start()
            try:
                cardservice = None
                for attempt in range(5):
                    try:
                        cardrequest = _dependency('smartcard.CardRequest', 'CardRequest')(
                            timeout=2, cardType=_dependency('smartcard.CardType', 'AnyCardType')()
                        )
                        cardservice = cardrequest.waitforcard()
                        break
                    except _dependency('smartcard.Exceptions', 'CardRequestTimeoutException'):
                        if attempt < 4:
                            _dependency('time', None).sleep(0.5)
                if cardservice is None:
                    self.loading_screen.stop()
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title='Failure',
                        status_headline=None,
                        text='No Smartcard detected...'.format(),
                        show_back_button=True,
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                self.loading_screen.stop()
                cardservice.connection.connect()
                card_atr = _dependency('smartcard.util', 'toHexString')(
                    cardservice.connection.getATR()
                )
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'),
                    title='Found SmartCard',
                    status_headline=None,
                    text=card_atr,
                    show_back_button=False,
                )
            except _dependency('smartcard.Exceptions', 'ListReadersException'):
                self.loading_screen.stop()
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='PCSC Failure',
                    status_headline=None,
                    text='Unable to list readers (A restart may help, possibly faulty reader)'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            except _dependency('smartcard.pcsc.PCSCExceptions', 'EstablishContextException'):
                self.loading_screen.stop()
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='PCSC Failure',
                    status_headline=None,
                    text='Unable to establish PCSC context(A restart may help, possibly faulty reader)'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'BackStackView')
            )

    return SCARDTestView


def _make_NFCTestView():

    class NFCTestView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.loading_screen = _dependency(
                'seedsigner.gui.screens.screen', 'LoadingScreenThread'
            )(text='Scanning for NFC Tag')
            self.loading_screen.start()
            _dependency('os', None).system('ifdnfc-activate no')
            _dependency('time', None).sleep(0.2)
            context = _dependency('nfc', None).init()
            nfcdevice = _dependency('nfc', None).open(context)
            if nfcdevice is None:
                self.loading_screen.stop()
                print('ERROR: Unable to open NFC device.')
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='NFC Failure',
                    status_headline=None,
                    text='ERROR: Unable to open NFC device. \n(May not be connected)'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if _dependency('nfc', None).initiator_init(nfcdevice) < 0:
                self.loading_screen.stop()
                print('ERROR: Unable to init NFC device.')
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='NFC Failure',
                    status_headline=None,
                    text='ERROR: Unable to init NFC device.'.format(),
                    show_back_button=True,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            print('NFC reader: %s opened' % _dependency('nfc', None).device_get_name(nfcdevice))
            nfcmodulation = _dependency('nfc', None).modulation()
            nfcmodulation.nmt = _dependency('nfc', None).NMT_ISO14443A
            nfcmodulation.nbr = _dependency('nfc', None).NBR_847
            nt = _dependency('nfc', None).target()
            ret = _dependency('nfc', None).initiator_poll_target(
                nfcdevice, nfcmodulation, 1, 100, 1, nt
            )
            self.loading_screen.stop()
            if ret and nt.nti.nai.szUidLen:
                print('The following (NFC) ISO14443A tag was found:')
                print('    ATQA (SENS_RES): ', end='')
                _dependency('nfc', None).print_hex(nt.nti.nai.abtAtqa, 2)
                id = 1
                if nt.nti.nai.abtUid[0] == 8:
                    id = 3
                print('       UID (NFCID%d): ' % id, end='')
                _dependency('nfc', None).print_hex(nt.nti.nai.abtUid, nt.nti.nai.szUidLen)
                foundtext = (
                    'UID:\n'
                    + _dependency('binascii', None).hexlify(nt.nti.nai.abtUid).decode()[:14]
                )
                print('      SAK (SEL_RES): ', end='')
                print(nt.nti.nai.btSak)
                if nt.nti.nai.szAtsLen:
                    print('          ATS (ATR): ', end='')
                    _dependency('nfc', None).print_hex(nt.nti.nai.abtAts, nt.nti.nai.szAtsLen)
                    foundtext = (
                        foundtext
                        + '\nATR:\n'
                        + _dependency('binascii', None).hexlify(nt.nti.nai.abtAts).decode()[:28]
                    )
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'),
                    title='Found NFC Tag',
                    status_headline=None,
                    text=foundtext,
                    show_back_button=False,
                )
            elif ret:
                print('Warning: IFD-NFC Conflict.')
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='NFC Conflict',
                    status_headline=None,
                    text="Can't scan when IFD-NFC Active".format(),
                    show_back_button=True,
                )
            else:
                print('Warning: No NFC Tag Detected.')
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title='Warning',
                    status_headline=None,
                    text='Warning: No NFC Tag Detected.'.format(),
                    show_back_button=True,
                )
            _dependency('nfc', None).close(nfcdevice)
            _dependency('nfc', None).exit(context)
            scinterface = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__SMARTCARD_INTERFACES
            )
            if 'pn532' in scinterface:
                _dependency('os', None).system('ifdnfc-activate yes')
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView')
            )

    return NFCTestView


def _make_RestartPCSCView():

    class RestartPCSCView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.loading_screen = _dependency(
                'seedsigner.gui.screens.screen', 'LoadingScreenThread'
            )(text='Restarting PCSC')
            self.loading_screen.start()
            if self.settings.is_seedsigner_os():
                _dependency('os', None).system('/etc/init.d/S01pcscd stop')
                _dependency('time', None).sleep(1)
                _dependency('os', None).system('/etc/init.d/S01pcscd start')
            else:
                _dependency('os', None).system('sudo service pcscd stop')
                _dependency('time', None).sleep(1)
                _dependency('os', None).system('sudo service pcscd start')
            try:
                pcsc_ctx = _dependency('smartcard.pcsc', 'PCSCContext').instance()
                try:
                    pcsc_ctx.releaseContext()
                except FeatureUnavailable:
                    raise
                except Exception:
                    pass
                pcsc_ctx.establishContext()
            except FeatureUnavailable:
                raise
            except Exception:
                try:
                    hresult, hcontext = _dependency('smartcard.scard', 'SCardEstablishContext')(
                        _dependency('smartcard.scard', 'SCARD_SCOPE_USER')
                    )
                    if hresult == _dependency('smartcard.scard', 'SCARD_S_SUCCESS'):
                        _dependency('smartcard.scard', 'SCardReleaseContext')(hcontext)
                        _dependency('smartcard.scard', 'SCardEstablishContext')(
                            _dependency('smartcard.scard', 'SCARD_SCOPE_USER')
                        )
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    print('Failed to reset pyscard context: {0}'.format(e))
            try:
                if getattr(self.controller, 'Satochip_Connector', None):
                    try:
                        self.controller.Satochip_Connector.card_disconnect()
                    except FeatureUnavailable:
                        raise
                    except Exception:
                        pass
                    self.controller.Satochip_Connector = None
            except FeatureUnavailable:
                raise
            except Exception:
                pass
            self.loading_screen.stop()
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView')
            )

    return RestartPCSCView


def _make_DonateView():

    class DonateView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.run_screen(_dependency('seedsigner_port.settings_screens', None).DonateScreen)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView')
            )

    return DonateView


def _make_BatteryInfoView():

    class BatteryInfoView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            if (
                not _dependency('seedsigner.hardware.battery_hat', 'BatteryHat')
                .get_instance()
                .is_enabled()
            ):
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('Battery Info'),
                    status_icon_size=0,
                    status_headline=None,
                    text=_dependency('gettext', 'gettext')(
                        'No compatible battery monitor detected'
                    ),
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                            _dependency('gettext', 'gettext')('Back')
                        )
                    ],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__HARDWARE
                    },
                )
            self.run_screen(_dependency('seedsigner_port.settings_screens', None).BatteryInfoScreen)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView'),
                view_args={
                    'visibility': _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__HARDWARE
                },
            )

    return BatteryInfoView


def _make_SystemInfoView():

    class SystemInfoView(_dependency('seedsigner.views.view', 'View')):
        def _read_text_file(self, path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    value = file.read().strip().replace('\x00', '')
                return value or None
            except FeatureUnavailable:
                raise
            except Exception:
                return None

        def _get_system_serial(self):
            try:
                with open('/proc/cpuinfo', 'r', encoding='utf-8') as file:
                    for line in file:
                        if line.startswith('Serial'):
                            serial = line.split(':', 1)[-1].strip()
                            return serial or _dependency('gettext', 'gettext')('Unavailable')
            except FeatureUnavailable:
                raise
            except Exception:
                pass
            return _dependency('gettext', 'gettext')('Unavailable')

        def _get_microsd_serial(self):
            mount_device = None
            try:
                with open('/proc/mounts', 'r', encoding='utf-8') as file:
                    for line in file:
                        parts = line.split()
                        if (
                            len(parts) >= 2
                            and parts[1]
                            == _dependency('seedsigner.hardware.microsd', 'MicroSD').MOUNT_POINT
                        ):
                            mount_device = parts[0]
                            break
            except FeatureUnavailable:
                raise
            except Exception:
                return _dependency('gettext', 'gettext')('Unavailable')
            if not mount_device:
                return _dependency('gettext', 'gettext')('Unavailable')
            block_device = _dependency('os', None).path.basename(mount_device)
            parent_device = _dependency('re', None).sub('p?\\d+$', '', block_device)
            serial_path = '/sys/class/block/{0}/device/serial'.format(parent_device)
            serial = self._read_text_file(serial_path)
            return serial if serial else _dependency('gettext', 'gettext')('Unavailable')

        def _get_platform_info(self):
            profile = _dependency('seedsigner.models.settings', 'Settings').RUNTIME_PROFILE
            platform_map = {
                'desktop': 'Desktop',
                'rpi_26': 'Raspberry Pi',
                'rpi_40': 'Raspberry Pi',
                'luckfox_22': 'Luckfox Pico',
                'luckfox_40': 'Luckfox Pico',
                'luckfox_pi': 'Luckfox Pico',
                'lc_lafrite': 'Libre Computer',
            }
            platform_name = platform_map.get(profile, 'Unknown')
            if profile == 'desktop':
                os_name = _dependency('platform', None).system().strip()
                if os_name:
                    return (platform_name, os_name)
                return (platform_name, _dependency('gettext', 'gettext')('Unavailable'))
            variant = self._read_text_file('/proc/device-tree/model')
            if not variant:
                try:
                    hardware_config = _dependency(
                        'seedsigner.models.settings', 'Settings'
                    ).get_platform_default_hardware_config()
                    if hardware_config:
                        variant = _dependency(
                            'seedsigner.hardware.io_config', 'get_hardware_profile_label'
                        )(hardware_config)
                except FeatureUnavailable:
                    raise
                except Exception:
                    pass
            if not variant:
                variant = _dependency('gettext', 'gettext')('Unavailable')
            return (platform_name, variant)

        def _format_build(self, os_release, prefix):
            branch = os_release.get(prefix + 'BRANCH')
            commit = os_release.get(prefix + 'COMMIT')
            date = os_release.get(prefix + 'DATE')
            if not any([branch, commit, date]):
                return ''
            short_commit = commit[:7] if commit and commit != 'unknown' else commit or '?'
            return '{0} {1} {2}'.format(branch or '?', short_commit, date or '').strip()

        def run(self):
            platform_name, platform_variant = self._get_platform_info()
            os_release = _dependency('seedsigner.helpers.seedsigner_os', 'get_os_release')()
            self.run_screen(
                _dependency('seedsigner_port.settings_screens', None).SystemInfoScreen,
                system_serial=self._get_system_serial(),
                microsd_serial=self._get_microsd_serial(),
                platform_name=platform_name,
                platform_variant=platform_variant,
                firmware_version=_dependency('seedsigner.controller', 'Controller').VERSION,
                source_location=_dependency('gettext', 'gettext')('MicroSD')
                if _dependency('seedsigner.helpers.seedsigner_os', 'is_running_from_microsd')()
                else _dependency('gettext', 'gettext')('Internal'),
                os_build=self._format_build(os_release, 'SEEDSIGNER_OS_'),
                app_build=self._format_build(os_release, 'SEEDSIGNER_APP_'),
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView'),
                view_args={
                    'visibility': _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__HARDWARE
                },
            )

    return SystemInfoView


def _make_MemoryInfoView():

    class MemoryInfoView(_dependency('seedsigner.views.view', 'View')):
        """Live RAM headroom, mainly for the memory-constrained Luckfox Pico boards.

        All probing lives in helpers.system_memory and all polling in the screen's
        update thread, so this View stays a thin route.
        """

        def run(self):
            self.run_screen(_dependency('seedsigner_port.settings_screens', None).MemoryInfoScreen)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView'),
                view_args={
                    'visibility': _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).VISIBILITY__HARDWARE
                },
            )

    return MemoryInfoView


def _make_HardeningTestView():

    class HardeningTestView(_dependency('seedsigner.views.view', 'View')):
        """Report the runtime hardening self-checks.

        Shown on BOTH variants: on an unhardened image the point is to make the
        open surfaces obvious, so this must not hide itself there.
        """

        _GLYPHS = {'pass': '[ok]', 'fail': '[!!]', 'n/a': '[--]'}

        def __init__(self, page_num=0, paged_info=None):
            super().__init__()
            self.page_num = page_num
            self.paged_info = paged_info

        def _build_report(self):
            results = _dependency('seedsigner.helpers', 'hardening').run_checks()
            criticals = [
                r
                for r in results
                if r.severity == _dependency('seedsigner.helpers', 'hardening').SEVERITY_CRITICAL
            ]
            failed = [r for r in criticals if r.failed]
            unknown = [
                r
                for r in criticals
                if r.state == _dependency('seedsigner.helpers', 'hardening').STATE_NA
            ]
            if failed:
                verdict = _dependency('gettext', 'gettext')(
                    'NOT HARDENED: {count} of {total} exposed'
                ).format(count=len(failed), total=len(criticals))
            elif unknown:
                verdict = _dependency('gettext', 'gettext')(
                    'Hardened ({count} unverifiable)'
                ).format(count=len(unknown))
            else:
                verdict = _dependency('gettext', 'gettext')('Hardened: all checks passed')
            result_lines = [
                '{glyph} {label}: {detail}'.format(
                    glyph=self._GLYPHS.get(result.state, '[--]'),
                    label=result.label,
                    detail=result.detail,
                ).rstrip(': ')
                for result in results
            ]
            return chr(10).join([verdict, ''] + result_lines)

        def run(self):
            if self.paged_info is None:
                width, height = _dependency(
                    'seedsigner_port.settings_screens', None
                ).HardeningTestScreen.get_paging_dimensions()
                self.paged_info = _dependency(
                    'seedsigner.gui.components', 'reflow_text_into_pages'
                )(text=self._build_report(), width=width, height=height)
            selected_menu_num = self.run_screen(
                _dependency('seedsigner_port.settings_screens', None).HardeningTestScreen,
                page_num=self.page_num,
                paged_info=self.paged_info,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if self.page_num >= len(self.paged_info) - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('SettingsMenuView'),
                    view_args={
                        'visibility': _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).VISIBILITY__ADVANCED
                    },
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('HardeningTestView'),
                view_args=dict(page_num=self.page_num + 1, paged_info=self.paged_info),
            )

    return HardeningTestView


def _make_VersionView():

    class VersionView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            version_fork = _dependency('seedsigner.helpers.version', 'Version').get_version_fork()
            short_commit_hash = _dependency(
                'seedsigner.helpers.version', 'Version'
            ).get_short_commit_hash()
            if _dependency('seedsigner.helpers.version', 'Version').is_release_image():
                version_fork = None
                short_commit_hash = None
            self.run_screen(
                _dependency('seedsigner_port.settings_screens', None).VersionScreen,
                version_name=_dependency(
                    'seedsigner.helpers.version', 'Version'
                ).get_version_name(),
                version_fork=version_fork,
                version_timestamp=_dependency(
                    'seedsigner.helpers.version', 'Version'
                ).get_version_timestamp(),
                short_commit_hash=short_commit_hash,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('SettingsMenuView')
            )

    return VersionView


_FACTORIES = {
    'SettingsMenuView': _make_SettingsMenuView,
    'LoadBackupFilesSettingsView': _make_LoadBackupFilesSettingsView,
    'SettingPBKDF2IterationsView': _make_SettingPBKDF2IterationsView,
    'LocaleSelectionView': _make_LocaleSelectionView,
    'SettingsEntryUpdateSelectionView': _make_SettingsEntryUpdateSelectionView,
    'SettingsSelectionRequiredWarningView': _make_SettingsSelectionRequiredWarningView,
    'SettingsIngestSettingsQRView': _make_SettingsIngestSettingsQRView,
    'IOTestView': _make_IOTestView,
    'SCardReaderTestView': _make_SCardReaderTestView,
    'SCARDTestView': _make_SCARDTestView,
    'NFCTestView': _make_NFCTestView,
    'RestartPCSCView': _make_RestartPCSCView,
    'DonateView': _make_DonateView,
    'BatteryInfoView': _make_BatteryInfoView,
    'SystemInfoView': _make_SystemInfoView,
    'MemoryInfoView': _make_MemoryInfoView,
    'HardeningTestView': _make_HardeningTestView,
    'VersionView': _make_VersionView,
}
_SUPPORTED = (
    'SettingsMenuView',
    'LoadBackupFilesSettingsView',
    'LocaleSelectionView',
    'SettingsEntryUpdateSelectionView',
    'SettingsSelectionRequiredWarningView',
)
_CACHE = {}


def _resolve(name):
    if name not in _FACTORIES:
        raise AttributeError(name)
    if name not in _SUPPORTED:
        raise FeatureUnavailable('Native settings feature unavailable: ' + name)
    if name not in _CACHE:
        _CACHE[name] = _FACTORIES[name]()
    return _CACHE[name]


def __getattr__(name):
    return _resolve(name)
