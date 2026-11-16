# SPDX-License-Identifier: MIT
# Public fixtures. Actual Controller error path, native screens, real sensor stop.
from seedsigner_port.controller import Controller, StopFlowBasedTest
from seedsigner_port.view_core import View, MainMenuView, UnhandledExceptionView
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.seed import Seed
from seedsigner_port.scan_screen import NativeVideoStream
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port.settings_store import Settings, SettingsConstants as C
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port import clock
import ui, json, camera, gc


class MissingProviderView(View):
    def run(self):
        raise FeatureUnavailable('Public fixture provider unavailable')


class ErrorDriver:
    def __init__(self):
        self.screens = []

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        self.screens.append(builder)
        if builder == 'large_icon_status_screen':
            assert cfg['status_headline'] == 'FeatureUnavailable'
            assert 'Public fixture provider unavailable' in cfg['text']
            assert cfg['top_nav']['title'] == 'System Error'
            ui.key(10, True)
            ui.key(10, False)
        elif builder == 'main_menu_screen':
            assert Controller.get_instance().back_stack == []
            raise StopFlowBasedTest()
        else:
            raise StopFlowBasedTest()


Renderer._instance = None
driver = ErrorDriver()
Renderer.configure_instance(backend=driver)
Controller._instance = None
controller = Controller.get_instance()
controller.start(
    initial_destination=Destination(MissingProviderView), skip_startup_interstitials=True
)
assert driver.screens == ['large_icon_status_screen', 'main_menu_screen']
print('@@PASS original-controller-explicit-unavailable-error-home')


class StartupErrorDriver(ErrorDriver):
    def render(self, builder, encoded):
        if builder == 'opening_splash_screen':
            raise FeatureUnavailable('Public fixture provider unavailable')
        return super().render(builder, encoded)


Renderer._instance = None
startup_driver = StartupErrorDriver()
Renderer.configure_instance(backend=startup_driver)
Controller._instance = None
controller = Controller.get_instance()
controller.start()
assert startup_driver.screens == ['large_icon_status_screen', 'main_menu_screen']
print('@@PASS original-startup-unavailable-error-home')


class ExpiringCamera(NativeVideoStream):
    starts = 0
    stops = 0
    frames = 0

    def read_video_stream(self):
        frame = super().read_video_stream()
        self.status = camera.preview_status()
        assert self.status[0] is True and self.status[1] >= 1
        self.frames += 1
        return frame

    def start_video_stream_mode(self):
        super().start_video_stream_mode()
        self.starts += 1
        controller.luckfox_release_keys = {'public': 1}
        controller.luckfox_bip85_cache = {'public': 1}
        controller.password_generator_entropy_cache = {'public': 1}
        HardwareButtons.get_instance().last_input_time = int(clock.time() * 1000) - 60001

    def stop_video_stream_mode(self):
        if self.active:
            self.stops += 1
        super().stop_video_stream_mode()


class IdleDriver:
    def __init__(self):
        self.screens = []

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        self.screens.append(builder)
        if builder != 'main_menu_screen':
            print('@@IDLE_UNEXPECTED', cfg)
            raise StopFlowBasedTest()
        if len(self.screens) == 1:
            ui.key(10, True)
            ui.key(10, False)
        else:
            assert (
                controller.storage.num_seeds() == 0
                and controller.storage.get_pending_seed() is None
            )
            assert controller.storage2.encryptedqr is None
            assert stored_alias == bytes(64) and pending_alias == bytes(64)
            assert controller.luckfox_release_keys is None and controller.luckfox_bip85_cache == {}
            assert controller.password_generator_entropy_cache is None
            assert controller.psbt is None and controller.resume_main_flow is None
            assert source.starts == 1 and source.stops == 1 and not source.active
            assert not controller.auto_wiped  # Actual MainMenuView consumed the wipe notification.
            assert ui.overlays(6) == 1
            raise StopFlowBasedTest()


Renderer._instance = None
driver = IdleDriver()
Renderer.configure_instance(backend=driver)
Controller._instance = None
controller = Controller.get_instance()
settings = Settings.get_instance()
old = settings.get_value(C.SETTING__WIPE_TIMER)
settings.set_value(C.SETTING__WIPE_TIMER, 1)
stored = Seed(('abandon ' * 11 + 'about').split())
pending = Seed(('abandon ' * 11 + 'about').split(), passphrase='public')
stored_alias = stored.seed_bytes
pending_alias = pending.seed_bytes
controller.storage.seeds.append(stored)
controller.storage.set_pending_seed(pending)
controller.storage2.set_encryptedqr('public fixture')
controller.luckfox_release_keys = {'public': 1}
controller.luckfox_bip85_cache = {'public': 1}
source = ExpiringCamera()
controller._camera = source
try:
    controller.start(skip_startup_interstitials=True)
finally:
    settings.set_value(C.SETTING__WIPE_TIMER, old)
assert driver.screens == ['main_menu_screen', 'main_menu_screen']
assert not source.active and source.stops == 1
assert camera.preview_status() == (False, 0) and source.frames == 1
print('@@REAL_CAMERA_IDLE_STOP', source.status, camera.preview_status())
print('@@PASS original-controller-idle-wipe-real-camera-unwind-home')
Renderer._instance = None
renderer = Renderer.get_instance()
ui.overlays(0, 0)
renderer.session.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
gc.collect()
