# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated from pinned original source; optional class bases resolve only on use.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination
def _make_BackStackView():

    class BackStackView:
        """
        Empty class that just signals to the Controller to pop the most recent View off
        the back_stack.
    """
        pass
    return BackStackView

def _make_View():

    class View:

        def _initialize(self):
            """
        Whether the View is a regular class initialized by __init__() or a dataclass
        initialized by __post_init__(), this method will be called to set up the View's
        instance variables.
        """
            self.controller = _dependency('seedsigner.controller', 'Controller').get_instance()
            self.settings = _dependency('seedsigner.models.settings', 'Settings').get_instance()
            self.renderer = _dependency('seedsigner.gui', 'Renderer').get_instance()
            self.canvas_width = self.renderer.canvas_width
            self.canvas_height = self.renderer.canvas_height
            self.screen = None
            self._redirect = None
            self.is_screensaver_allowed = True

        def __init__(self):
            self._initialize()

        def __post_init__(self):
            self._initialize()

        @property
        def has_redirect(self):
            if not hasattr(self, '_redirect'):
                raise Exception('{0} did not call super().__init__()'.format(self.__class__.__name__))
            return self._redirect is not None

        def set_redirect(self, destination):
            """
        Enables early `__init__()` / `__post_init__()` logic to redirect away from the
        current View.

        Set a redirect Destination and then immediately `return` to exit `__init__()` or
        `__post_init__()`. When the `Destination.run()` is called, it will see the redirect
        and immediately return that new Destination to the Controller without running
        the View's `run()`.
        """
            destination.skip_current_view = True
            self._redirect = destination

        def get_redirect(self):
            return self._redirect

        def run_screen(self, Screen_cls, **kwargs):
            """
            Instantiates the provided Screen_cls and runs its interactive display.
            Returns the user's input upon completion.
        """
            self.screen = Screen_cls(**kwargs)
            return self.screen.display()

        def run(self, **kwargs):
            raise Exception('Must implement in the child class')
    return View

def _make_MainMenuView():

    class MainMenuView(_resolve('View')):
        SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').SCAN)
        SEEDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Seeds', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').SEEDS)
        TOOLS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Tools', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').TOOLS)
        SETTINGS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Settings', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').SETTINGS)
        IO_TEST = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I/O Test')
        TEST_SMARTCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Test Smartcard')
        FLASH_APPLET = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Flash Applet')

        def run(self):
            controller = _dependency('seedsigner.controller', 'Controller').get_instance()
            if _dependency('seedsigner.models.settings', 'Settings').is_seedsigner_os():
                _dependency('seedsigner.helpers.seedsigner_os', 'signal_app_alive')()
                if _dependency('seedsigner.models.settings', 'Settings').RUNTIME_PROFILE in _resolve('PowerOptionsView').LUCKFOX_PROFILES and (not getattr(controller, 'boot_failover_cleared', False)):
                    controller.boot_failover_cleared = True
                    try:
                        _dependency('subprocess', 'run')(['devmem', '0xFF020218', '32', '0'], stdout=_dependency('subprocess', 'DEVNULL'), stderr=_dependency('subprocess', 'DEVNULL'), check=False)
                    except FeatureUnavailable:
                        raise
                    except Exception:
                        pass
            controller.storage.discard_pending_slip39_shares()
            _dependency('seedsigner.views.resign_views', 'clear_signing_keys')(controller)
            controller.psbt_from_microsd = False
            controller.psbt_microsd_save_path = None
            controller.psbt_microsd_seed_warning_shown = False
            if controller.auto_wiped:
                controller.auto_wiped = False
                controller.activate_toast(_dependency('seedsigner.gui.toast', 'InfoToast')(label_text=_dependency('gettext', 'gettext')('Data wiped after inactivity')))
            if _dependency('seedsigner.helpers.seedsigner_os', 'is_testing_build_enabled')():
                button_data = [self.IO_TEST, self.TEST_SMARTCARD, self.FLASH_APPLET, self.SETTINGS]
                title = _dependency('gettext', 'gettext')('Testing')
            else:
                button_data = [self.SCAN, self.SEEDS, self.TOOLS, self.SETTINGS]
                title = _dependency('gettext', 'gettext')('Home')
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'MainMenuScreen'), title=title, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__POWER_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PowerOptionsView'))
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__DISPLAY_TOGGLE'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'))
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__REBOOT_TO_LOADER'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('RebootToLoaderView'))
            if button_data[selected_menu_num] == self.SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanView'))
            elif button_data[selected_menu_num] == self.SEEDS:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedsMenuView'))
            elif button_data[selected_menu_num] == self.TOOLS:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsMenuView'))
            elif button_data[selected_menu_num] == self.SETTINGS:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'SettingsMenuView'))
            elif button_data[selected_menu_num] == self.IO_TEST:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'IOTestView'))
            elif button_data[selected_menu_num] == self.TEST_SMARTCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'SCARDTestView'))
            elif button_data[selected_menu_num] == self.FLASH_APPLET:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.smartcard_views', 'ToolsDIYInstallAppletView'))
    return MainMenuView

def _make_PowerOptionsView():

    class PowerOptionsView(_resolve('View')):
        RESET = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Restart', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').RESTART)
        POWER_OFF = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Power off', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').POWER)
        REBOOT_LOADER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Reboot to flash mode', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        LUCKFOX_PROFILES = ('luckfox_22', 'luckfox_40', 'luckfox_pi')

        def run(self):
            button_data = [self.RESET, self.POWER_OFF]
            if _dependency('seedsigner.models.settings', 'Settings').RUNTIME_PROFILE in self.LUCKFOX_PROFILES:
                button_data.append(self.REBOOT_LOADER)
            screen_cls = _dependency('seedsigner.gui.screens.screen', 'LargeButtonScreen') if len(button_data) <= 2 else _dependency('seedsigner.gui.screens.screen', 'ButtonListScreen')
            selected_menu_num = self.run_screen(screen_cls, title=_dependency('gettext', 'gettext')('Reset / Power'), show_back_button=True, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('BackStackView'))
            elif button_data[selected_menu_num] == self.RESET:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('RestartView'))
            elif button_data[selected_menu_num] == self.POWER_OFF:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PowerOffView'))
            elif button_data[selected_menu_num] == self.REBOOT_LOADER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('RebootToLoaderView'))
    return PowerOptionsView

def _make_RestartView():

    class RestartView(_resolve('View')):

        def run(self):
            _dependency('seedsigner.models.settings', 'Settings').get_instance().flush_save()
            if self.renderer.is_screenshot_generator:
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ResetScreen'))
                return
            thread = _resolve('RestartView').DoResetThread()
            thread.start()
            try:
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ResetScreen'))
            except FeatureUnavailable:
                raise
            except Exception:
                thread.stop()
                raise

        class DoResetThread(_dependency('seedsigner.models.threads', 'BaseThread')):

            def run(self):
                pass
                _dependency('time', None).sleep(0.25)
                if not self.keep_running:
                    return
                _dependency('sys', None).stdout.flush()
                _dependency('sys', None).stderr.flush()
                pid = _dependency('os', None).getpid()
                if _dependency('seedsigner.models.settings', 'Settings').is_seedsigner_os():
                    python = _dependency('shlex', None).quote(_dependency('sys', None).executable)
                    _dependency('subprocess', 'call')('kill {0}; exec {1} /opt/src/main.py'.format(pid, python), shell=True)
                else:
                    _dependency('subprocess', 'call')('kill {0}'.format(pid), shell=True)

        def __init__(self):
            self.__post_init__()
    return RestartView

def _make_RebootToLoaderView():

    class RebootToLoaderView(_resolve('View')):
        """Reboot a Rockchip Luckfox Pico into rockusb Loader mode so it can be
    re-flashed over USB (Rockchip SocToolKit / rkdeveloptool) without the BOOT
    button."""

        def run(self):
            _dependency('seedsigner.models.settings', 'Settings').get_instance().flush_save()
            if self.renderer.is_screenshot_generator:
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'RebootToLoaderScreen'))
                return
            thread = _resolve('RebootToLoaderView').DoRebootToLoaderThread()
            thread.start()
            try:
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'RebootToLoaderScreen'))
            except FeatureUnavailable:
                raise
            except Exception:
                thread.stop()
                raise

        class DoRebootToLoaderThread(_dependency('seedsigner.models.threads', 'BaseThread')):

            def run(self):
                pass
                _dependency('time', None).sleep(0.25)
                if not self.keep_running:
                    return
                libc = _dependency('ctypes', None).CDLL(None, use_errno=True)
                rc = libc.syscall(88, 4276215469, 672274793, 2712847316, b'loader')
                pass

        def __init__(self):
            self.__post_init__()
    return RebootToLoaderView

def _make_PowerOffView():

    class PowerOffView(_resolve('View')):

        def run(self):
            _dependency('seedsigner.models.settings', 'Settings').get_instance().flush_save()
            if not _dependency('seedsigner.hardware.buttons', 'USING_GPIO'):
                if 'PYTEST_CURRENT_TEST' not in _dependency('os', None).environ:
                    _dependency('sys', None).exit(0)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('BackStackView'))
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'PowerOffNotRequiredScreen'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('BackStackView'))
    return PowerOffView

def _make_NotYetImplementedView():

    class NotYetImplementedView(_resolve('View')):
        """
        Temporary View to use during dev.
    """

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Work In Progress'), status_headline=_dependency('gettext', 'gettext')('Not Yet Implemented'), text=self.text, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Back to main menu')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'))

        def __init__(self, text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This is still on our to-do list!')):
            self.text = text
            self.__post_init__()
    return NotYetImplementedView

def _make_ErrorView():

    class ErrorView(_resolve('View')):

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ErrorScreen'), title=self.title, status_icon_name=self.status_icon_name, status_headline=self.status_headline, text=self.text, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(self.button_text)], show_back_button=self.show_back_button)
            return self.next_destination if self.next_destination else _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'), clear_history=True)

        def __init__(self, title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Error'), show_back_button=True, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=None, button_text=None, next_destination=None):
            self.title = title
            self.show_back_button = show_back_button
            self.status_icon_name = status_icon_name
            self.status_headline = status_headline
            self.text = text
            self.button_text = button_text
            self.next_destination = next_destination
            self.__post_init__()
    return ErrorView

def _make_NetworkMismatchErrorView():

    class NetworkMismatchErrorView(_resolve('ErrorView')):

        def __post_init__(self):
            self.title = _dependency('gettext', 'gettext')('Network Mismatch')
            self.status_icon_name = _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').WARNING
            self.show_back_button = False
            self.button_text = _dependency('gettext', 'gettext')('Change Setting')
            self.next_destination = _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'SettingsEntryUpdateSelectionView'), view_args=dict(attr_name=_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), clear_history=True)
            super().__post_init__()
            network = _dependency('gettext', 'gettext')(self.settings.get_value_display_name(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            self.text = _dependency('gettext', 'gettext')("Current network setting ({network}) doesn't match {derivation_path}.").format(network=network, derivation_path=self.derivation_path)

        def __init__(self, title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Error'), show_back_button=True, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=None, button_text=None, next_destination=None, derivation_path=None):
            self.title = title
            self.show_back_button = show_back_button
            self.status_icon_name = status_icon_name
            self.status_headline = status_headline
            self.text = text
            self.button_text = button_text
            self.next_destination = next_destination
            self.derivation_path = derivation_path
            self.__post_init__()
    return NetworkMismatchErrorView

def _make_UnhandledExceptionView():

    class UnhandledExceptionView(_resolve('View')):

        def __post_init__(self):
            super().__post_init__()
            if self.error[0] == _dependency('seedsigner.hardware.camera', 'CameraConnectionError').__name__:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_resolve('CameraConnectionErrorView'), skip_current_view=True))

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ErrorScreen'), title=_dependency('gettext', 'gettext')('System Error'), status_headline=self.error[0], text=self.error[1] + '\n' + self.error[2], button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Back to Main Menu')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'), clear_history=True)

        def __init__(self, error):
            self.error = error
            self.__post_init__()
    return UnhandledExceptionView

def _make_CameraConnectionErrorView():

    class CameraConnectionErrorView(_resolve('View')):

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ErrorScreen'), title=_dependency('gettext', 'gettext')('Hardware Error'), status_headline=_dependency('gettext', 'gettext')('Cannot access camera'), text=_dependency('gettext', 'gettext')('Disconnect power and check for a loose camera connection.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Back to Main Menu')], show_back_button=False)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'), clear_history=True)

        def __init__(self):
            self.__post_init__()
    return CameraConnectionErrorView

def _make_OptionDisabledView():

    class OptionDisabledView(_resolve('View')):
        UPDATE_SETTING = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Update setting')
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Back to Main Menu')

        def __post_init__(self):
            super().__post_init__()
            self.settings_entry = _dependency('seedsigner.models.settings_definition', 'SettingsDefinition').get_settings_entry(self.settings_attr)
            self.error_msg = _dependency('gettext', 'gettext')('"{}" is currently disabled in Settings.').format(_dependency('gettext', 'gettext')(self.settings_entry.display_name))

        def run(self):
            button_data = [self.UPDATE_SETTING, self.DONE]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Option Disabled'), status_headline=None, text=self.error_msg, button_data=button_data, show_back_button=False)
            if button_data[selected_menu_num] == self.UPDATE_SETTING:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'SettingsEntryUpdateSelectionView'), view_args=dict(attr_name=self.settings_attr), clear_history=True)
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'), clear_history=True)

        def __init__(self, settings_attr):
            self.settings_attr = settings_attr
            self.__post_init__()
    return OptionDisabledView

def _make_RemoveMicroSDWarningView():

    class RemoveMicroSDWarningView(_resolve('View')):
        CONTINUE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')
        SETTINGS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Settings')

        def run(self):
            button_data = [self.CONTINUE, self.SETTINGS]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Action Required'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD, status_headline=None, text=_dependency('gettext', 'gettext')('You must remove the\nMicroSD card to continue.'), show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.CONTINUE:
                if not _dependency('seedsigner.hardware.microsd', 'MicroSD').get_instance().is_inserted:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('MainMenuView'), clear_history=True)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('RemoveMicroSDWarningView'), clear_history=True)
            elif button_data[selected_menu_num] == self.SETTINGS:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.settings_views', 'SettingsEntryUpdateSelectionView'), view_args=dict(attr_name=_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__MICROSD_TOAST_TIMER, blocking_view=_resolve('RemoveMicroSDWarningView'), unblocking_view=_resolve('MainMenuView')))
    return RemoveMicroSDWarningView

_FACTORIES={'BackStackView':_make_BackStackView,'View':_make_View,'MainMenuView':_make_MainMenuView,'PowerOptionsView':_make_PowerOptionsView,'RestartView':_make_RestartView,'RebootToLoaderView':_make_RebootToLoaderView,'PowerOffView':_make_PowerOffView,'NotYetImplementedView':_make_NotYetImplementedView,'ErrorView':_make_ErrorView,'NetworkMismatchErrorView':_make_NetworkMismatchErrorView,'UnhandledExceptionView':_make_UnhandledExceptionView,'CameraConnectionErrorView':_make_CameraConnectionErrorView,'OptionDisabledView':_make_OptionDisabledView,'RemoveMicroSDWarningView':_make_RemoveMicroSDWarningView}
_CACHE={}
def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:raise AttributeError(name)
        _CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
