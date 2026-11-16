# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Original foreground Controller; reviewed native setup/error/service boundaries.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination
from seedsigner_port.app_services import NativeIdleWipe


class StopFlowBasedTest(Exception):
    """
    This is a special exception that is only raised by the test suite to stop the
    Controller's main loop. It should not be raised by any other code.
    """

    pass


class FlowBasedTestException(Exception):
    """
    This is a special exception that is only raised by the test suite.
    It should not be raised by any other code.
    """

    pass


class Controller(_dependency('seedsigner.models.singleton', 'Singleton')):
    """
    The Controller is a globally available singleton that maintains SeedSigner state.

    It only makes sense to ever have a single Controller instance so it is
    implemented here as a singleton. One departure from the typical singleton pattern
    is the addition of a `configure_instance()` call to pass run-time settings into
    the Controller.

    Any code that needs to interact with the one and only Controller can just run:
    ```
    from seedsigner.controller import Controller
    controller = Controller.get_instance()
    ```
    Note: In many/most cases you'll need to do the Controller import within a method
    rather than at the top in order avoid circular imports.
    """

    VERSION = 'SeSi-0.8.7+ShSi-B13'
    RELEASE_BLOCK_HEIGHT = 963408
    RELEASE_BLOCK_TIME = 1787616000
    SECONDS_PER_BLOCK = 600
    RECENT_MAX_FEE_RATE = 120
    _storage = None
    _storage2 = None
    settings = None
    psbt = None
    psbt_seed = None
    psbt_parser = None
    psbt_sign_with_satochip = False
    psbt_from_microsd = False
    psbt_microsd_save_path = None
    psbt_microsd_seed_warning_shown = False
    psbt_source_time = None
    sign_message_with_satochip = False
    unverified_address = None
    multisig_wallet_descriptor = None
    image_entropy_preview_frames = None
    image_entropy_final_image = None
    address_explorer_data = None
    password_generator_entropy_cache = None
    sign_message_data = None
    gpg_keys_imported = False
    gpg_pending_message = None
    Satochip_Connector = None
    Satochip_PIN = None
    Satochip_Last_UID_SHA1 = None
    Satodime_unlock_secrets = None
    Satodime_unlock_nicknames = None
    satodime_slot_cache = None
    GPG_Admin_PIN = None
    javacard_keys = None
    FLOW__PSBT = 'psbt'
    FLOW__VERIFY_MULTISIG_ADDR = 'multisig_addr'
    FLOW__VERIFY_SINGLESIG_ADDR = 'singlesig_addr'
    FLOW__ADDRESS_EXPLORER = 'address_explorer'
    FLOW__SIGN_MESSAGE = 'sign_message'
    FLOW__SATOCHIP_IMPORT_SEED = 'satochip_import_seed'
    FLOW__GPG_MESSAGE = 'gpg_message'
    resume_main_flow = None
    back_stack = None
    screensaver = None
    toast_notification_thread = None
    wipe_timer_thread = None
    rng_monitor_thread = None
    hardware_rng_monitor = None
    wipe_timer_ms = None
    auto_wiped = False

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        else:
            return cls.configure_instance()

    @classmethod
    def reset_instance(cls):
        """
        Currently used by the screenshot generator, but could potentially be used to
        wipe and reset the state of the device.
        """
        cls._instance = None
        cls.configure_instance()

    @classmethod
    def configure_instance(cls):
        if cls._instance:
            raise Exception('Instance already configured')
        controller = object.__new__(cls)
        cls._instance = controller
        controller.settings = _dependency('seedsigner.models.settings', 'Settings').get_instance()
        controller._storage = _dependency('seedsigner.models.seed_storage', 'SeedStorage')()
        controller._storage2 = _dependency('seedsigner.models.encryptedqr', 'EncryptedQRStorage')()
        controller._camera = _dependency('seedsigner_port.scan_screen', 'NativeVideoStream')()
        _dependency('seedsigner_port.renderer', 'Renderer').get_instance()
        controller.back_stack = _dependency('seedsigner_port.navigation', 'BackStack')()
        controller.screensaver_activation_ms = 120000
        controller.screensaver = _dependency('seedsigner_port.app_services', 'ScreensaverScreen')()
        _dependency('ui', None).overlays(0, controller.screensaver_activation_ms)
        return controller

    @property
    def camera(self):
        return self._camera

    @property
    def storage(self):
        while not self._storage:
            _dependency('seedsigner_port.clock', None).sleep(0.001)
        return self._storage

    @property
    def storage2(self):
        while not self._storage2:
            _dependency('seedsigner_port.clock', None).sleep(0.001)
        return self._storage2

    @property
    def hardware_rng_is_healthy(self):
        if not self.hardware_rng_monitor:
            return False
        return self.hardware_rng_monitor.is_healthy()

    @property
    def hardware_rng_failure_reason(self):
        if not self.hardware_rng_monitor:
            return 'System RNG monitor unavailable'
        return self.hardware_rng_monitor.failure_reason()

    def discard_seed(self, seed):
        try:
            seed.wipe()
        except FeatureUnavailable:
            raise
        except Exception:
            pass
        self.storage.seeds.remove(seed)

    def pop_prev_from_back_stack(self):
        if len(self.back_stack) > 0:
            self.back_stack.pop()
            if len(self.back_stack) > 0:
                return self.back_stack.pop()
        return _dependency('seedsigner.views.view', 'Destination')(None)

    def clear_back_stack(self):
        self.back_stack = _dependency('seedsigner_port.navigation', 'BackStack')()

    def start(self, initial_destination=None, skip_startup_interstitials=False):
        startup_error_destination = None
        if not skip_startup_interstitials:
            try:
                _dependency('seedsigner_port.view_splash', 'OpeningSplashView')().run()
                _dependency('seedsigner_port.view_development', 'DeveloperOSWarningView')().run()
            except Exception as e:
                startup_error_destination = self.handle_exception(e)
        try:
            if startup_error_destination:
                next_destination = startup_error_destination
            elif initial_destination:
                next_destination = initial_destination
            else:
                next_destination = _dependency('seedsigner.views.view', 'Destination')(
                    _dependency('seedsigner.views', 'MainMenuView')
                )
            if _dependency('seedsigner.models.settings', 'Settings').RUNTIME_PROFILE not in {
                'luckfox_22',
                'luckfox_40',
                'luckfox_pi',
                'desktop',
            }:
                if (
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__MICROSD_TOAST_TIMER
                    )
                    == _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).MICROSD_TOAST_TIMER_FIVE_SECONDS
                ):
                    self.activate_toast(
                        _dependency('seedsigner.gui.toast', 'RemoveSDCardToastManagerThread')()
                    )
                elif (
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__MICROSD_TOAST_TIMER
                    )
                    == _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).MICROSD_TOAST_TIMER_FOREVER
                ):
                    next_destination = _dependency('seedsigner.views.view', 'Destination')(
                        _dependency('seedsigner.views', 'RemoveMicroSDWarningView')
                    )
            while True:
                if next_destination.View_cls is None:
                    next_destination = _dependency('seedsigner.views.view', 'Destination')(
                        _dependency('seedsigner.views', 'MainMenuView')
                    )
                if next_destination.View_cls == _dependency('seedsigner.views', 'MainMenuView'):
                    self.clear_back_stack()
                    self.resume_main_flow = None
                    self.unverified_address = None
                    self.address_explorer_data = None
                    self.psbt = None
                    self.psbt_parser = None
                    self.psbt_seed = None
                    self.psbt_sign_with_satochip = False
                    self.sign_message_with_satochip = False
                    self.image_entropy_preview_frames = None
                    self.image_entropy_final_image = None
                    self.password_generator_entropy_cache = None
                    if (
                        _dependency('seedsigner.models.settings', 'Settings')
                        .get_instance()
                        .get_value(
                            _dependency(
                                'seedsigner.models.settings_definition', 'SettingsConstants'
                            ).SETTING__CACHE_SCARD_PIN
                        )
                        != 'E'
                    ):
                        self.Satochip_PIN = None
                        self.Satochip_Last_UID_SHA1 = None
                        self.Satochip_Connector = None
                        self.Satodime_unlock_secrets = None
                        self.Satodime_unlock_nicknames = None
                    self.GPG_Admin_PIN = None
                    self.satodime_slot_cache = None
                pass
                try:
                    pass
                    next_destination = next_destination.run()
                except StopFlowBasedTest:
                    return
                except FlowBasedTestException as e:
                    raise e
                except (KeyboardInterrupt, SystemExit):
                    raise
                except NativeIdleWipe:
                    next_destination = Destination(
                        _dependency('seedsigner.views', 'MainMenuView'), clear_history=True
                    )
                except BaseException as e:
                    pass
                    next_destination = self.handle_exception(e)
                if not next_destination:
                    next_destination = _dependency('seedsigner.views.view', 'Destination')(
                        _dependency('seedsigner.views.view', 'NotYetImplementedView')
                    )
                if next_destination.skip_current_view:
                    current_view = self.back_stack.pop()
                    pass
                clear_history = next_destination.clear_history
                if next_destination.View_cls == _dependency('seedsigner.views', 'BackStackView'):
                    next_destination = self.pop_prev_from_back_stack()
                if clear_history:
                    self.clear_back_stack()
                try:
                    unwind_index = self.back_stack.index(next_destination)
                except ValueError:
                    unwind_index = None
                if unwind_index is not None:
                    if unwind_index < len(self.back_stack) - 1:
                        pass
                    del self.back_stack[unwind_index:]
                pass
                self.back_stack.append(next_destination)
        finally:
            if self.is_screensaver_running:
                self.screensaver.stop()
            if self.toast_notification_thread and self.toast_notification_thread.is_alive():
                self.toast_notification_thread.stop()
            if hasattr(self, 'battery_hat') and self.battery_hat.is_alive():
                self.battery_hat.stop()
            if self.wipe_timer_thread and self.wipe_timer_thread.is_alive():
                self.wipe_timer_thread.stop()
            if self.rng_monitor_thread and self.rng_monitor_thread.is_alive():
                self.rng_monitor_thread.stop()
            if _dependency('sys', None).exc_info()[0] is None:
                pass
                _dependency(
                    'seedsigner.gui.renderer', 'Renderer'
                ).get_instance().display_blank_screen()
            else:
                pass

    @property
    def is_screensaver_running(self):
        return self.screensaver is not None and self.screensaver.is_running

    def start_screensaver(self):
        if self.toast_notification_thread and self.toast_notification_thread.is_alive():
            pass
            self.toast_notification_thread.toggle_renderer_lock()
        pass
        if not self.screensaver:
            self.screensaver = _dependency('seedsigner.views.screensaver', 'ScreensaverScreen')(
                _dependency('seedsigner.hardware.buttons', 'HardwareButtons').get_instance()
            )
        self.screensaver.start()
        pass

    def reset_screensaver_timeout(self):
        """
        Reset the screensaver's timeout starting point to right now (i.e. make it think
        that zero time has elapsed since the last user interaction).
        """
        _dependency(
            'seedsigner.hardware.buttons', 'HardwareButtons'
        ).get_instance().update_last_input_time()
        _dependency('ui', None).overlays(3)

    def activate_toast(self, toast_manager_thread):
        """
        Ensures that the Controller has explicit control over which processes get to
        claim the Renderer.lock and which need to (potentially) release it.
        """
        if self.is_screensaver_running:
            pass
            self.screensaver.stop()
        if self.toast_notification_thread and self.toast_notification_thread.is_alive():
            pass
            self.toast_notification_thread.stop()
        self.toast_notification_thread = toast_manager_thread
        pass
        self.toast_notification_thread.start()

    def handle_wipe_timeout(self):
        pass
        for seed in self.storage.seeds:
            try:
                seed.wipe()
            except FeatureUnavailable:
                raise
            except Exception:
                pass
        self.storage.seeds = []
        self.storage.clear_pending_seed()
        if self._storage2:
            self._storage2.clear_encryptedqr()
        self.password_generator_entropy_cache = None
        try:
            _dependency('seedsigner.views.resign_views', 'clear_signing_keys')(self)
        except FeatureUnavailable:
            raise
        except Exception:
            pass
        self.psbt = None
        self.psbt_parser = None
        self.psbt_seed = None
        self.psbt_sign_with_satochip = False
        self.sign_message_with_satochip = False
        self.multisig_wallet_descriptor = None
        self.unverified_address = None
        self.address_explorer_data = None
        self.sign_message_data = None
        self.resume_main_flow = None
        self.Satochip_PIN = None
        self.Satochip_Last_UID_SHA1 = None
        self.Satochip_Connector = None
        self.Satodime_unlock_secrets = None
        self.Satodime_unlock_nicknames = None
        self.satodime_slot_cache = None
        self.GPG_Admin_PIN = None
        self.image_entropy_preview_frames = None
        self.image_entropy_final_image = None
        self.clear_back_stack()
        self.back_stack.append(
            _dependency('seedsigner.views.view', 'Destination')(
                _dependency('seedsigner.views', 'MainMenuView')
            )
        )
        self.auto_wiped = True
        self.activate_toast(
            _dependency('seedsigner.gui.toast', 'InfoToast')(
                label_text=_dependency('gettext', 'gettext')('Data wiped after inactivity')
            )
        )
        raise NativeIdleWipe()

    def handle_exception(self, e):
        location = _dependency('machine', None).exception_location(e)
        line_info = ''
        if location is not None:
            line_info = '{}, {} in {}'.format(location[0], location[1], location[2])
        return _dependency('seedsigner.views.view', 'Destination')(
            _dependency('seedsigner.views.view', 'UnhandledExceptionView'),
            view_args={'error': [type(e).__name__, line_info, str(e)]},
            clear_history=True,
        )

    @property
    def is_screensaver_start_allowed(self):
        """
        Determines whether the screensaver is allowed to start.

        The screensaver can start only if:
        - It is not currently running.
        - The current active view allows screensaver activity.
        """
        active_view = (
            self.back_stack[-1].view
            if self.back_stack
            else _dependency('seedsigner.views', 'MainMenuView')()
        )
        return not self.is_screensaver_running and active_view.is_screensaver_allowed

    def service(self):
        minutes = self.settings.get_value(
            _dependency(
                'seedsigner.models.settings_definition', 'SettingsConstants'
            ).SETTING__WIPE_TIMER
        )
        if (
            minutes
            and minutes
            != _dependency(
                'seedsigner.models.settings_definition', 'SettingsConstants'
            ).WIPE_TIMER__DISABLED
        ):
            self.wipe_timer_ms = minutes * 60000
            buttons = _dependency(
                'seedsigner_port.hardware_buttons', 'HardwareButtons'
            ).get_instance()
            if (
                int(_dependency('seedsigner_port', 'clock').time() * 1000) - buttons.last_input_time
                > self.wipe_timer_ms
            ):
                buttons.update_last_input_time()
                self.handle_wipe_timeout()
