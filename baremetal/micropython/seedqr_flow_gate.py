# SPDX-License-Identifier: MIT
# Public fixture export through original Views and actual native key/pixel events.
import ui, qr, json, hashlib, gc, machine, time
from seedsigner_port.controller import Controller, StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.view_seed import SeedBackupView
from seedsigner_port.navigation import Destination
from seedsigner_port.seed import Seed
from seedsigner_port.settings_store import Settings, SettingsConstants as C

fixtures = [
    (
        [
            'abandon',
            'amount',
            'liar',
            'amount',
            'expire',
            'adjust',
            'cage',
            'candy',
            'arch',
            'gather',
            'drum',
            'buyer',
        ],
        False,
        '000000641030006406430028025702660088077105400251',
        '471747eb116f14d0155bc679f99c2330a990068c78a4676d512a0119e6edc376',
        25,
    ),
    (
        [
            'abandon',
            'amount',
            'liar',
            'amount',
            'expire',
            'adjust',
            'cage',
            'candy',
            'arch',
            'gather',
            'drum',
            'buyer',
        ],
        True,
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f',
        'e284601f69f37a5ad4e187cd4a640e6aae0732bb2ad3a503158ae9752582428e',
        21,
    ),
    (
        [
            'abandon',
            'amount',
            'liar',
            'amount',
            'expire',
            'adjust',
            'cage',
            'candy',
            'arch',
            'gather',
            'drum',
            'bullet',
            'absurd',
            'math',
            'era',
            'live',
            'bid',
            'rhythm',
            'alien',
            'crouch',
            'range',
            'attend',
            'journey',
            'unaware',
        ],
        False,
        '000000641030006406430028025702660088077105400241000810960610104501761478005004171422011609631891',
        '2138ce2ccb1217fd3b22e2a39971783bcdf8e314f6fd1460ea1df10846a27f36',
        29,
    ),
    (
        [
            'abandon',
            'amount',
            'liar',
            'amount',
            'expire',
            'adjust',
            'cage',
            'candy',
            'arch',
            'gather',
            'drum',
            'bullet',
            'absurd',
            'math',
            'era',
            'live',
            'bid',
            'rhythm',
            'alien',
            'crouch',
            'range',
            'attend',
            'journey',
            'unaware',
        ],
        True,
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f',
        'ad31b522d5f160bae0260ea093ea05b4e1db038556fee6c6972daba74725f5e4',
        25,
    ),
]  # PUBLIC CPython oracle.


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def choose(cfg, label):
    labels = [x if isinstance(x, str) else x['label'] for x in cfg['button_list']]
    for _ in range(labels.index(label)):
        pulse(18)
    pulse(10)


def drawn_luma():
    raw = ui.framebuffer()
    pixels = bytearray(240 * 240)
    for i in range(240 * 240):
        v = (raw[i * 2] << 8) | raw[i * 2 + 1]
        pixels[i] = (
            ((v >> 11) * 255 // 31) * 77
            + (((v >> 5) & 63) * 255 // 63) * 150
            + ((v & 31) * 255 // 31) * 29
        ) >> 8
    return pixels


class Driver:
    def __init__(self, fixture, back=False):
        self.words, self.compact, self.data, self.digest, self.size = fixture
        self.back = back
        self.overviews = 0
        self.zooms = 0
        self.failure = None
        self.closed = False

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        try:
            self.checked(builder, encoded)
        except StopFlowBasedTest:
            raise
        except Exception as error:
            self.failure = (builder, type(error).__name__)
            raise StopFlowBasedTest()

    def checked(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        c = Controller.get_instance()
        title = cfg['top_nav']['title']
        if builder == 'button_list_screen':
            if title == 'Backup Seed':
                choose(cfg, 'Export as SeedQR')
            elif title == 'Confirm SeedQR?':
                assert self.zooms == 1
                self.closed = True
                choose(cfg, 'Done')
            else:
                assert title == seed.get_fingerprint() and self.closed
                assert c.storage.num_seeds() == 1 and len(c.back_stack) == 1
                pulse(20)
                pulse(10)
        elif builder == 'seed_transcribe_seedqr_format_screen':
            label = ('Compact' if self.compact else 'Standard') + ': %dx%d' % (self.size, self.size)
            choose(cfg, label)
        elif builder == 'large_icon_status_screen':
            assert cfg['status_headline'] == 'SeedQR is your private key!'
            pulse(10)
        elif builder in ('seed_transcribe_whole_qr_screen', 'seed_transcribe_zoomed_qr_screen'):
            packed = bytes.fromhex(cfg['matrix_hex'])
            assert packed[0] == self.size and hashlib.sha256(packed).hexdigest() == self.digest
            actual = (
                bytes.fromhex(cfg['qr_data']) if cfg['data_encoding'] == 'hex' else cfg['qr_data']
            )
            assert actual == self.data
            if builder == 'seed_transcribe_whole_qr_screen':
                self.overviews += 1
                assert qr.decode(drawn_luma(), 240, 240) == (
                    self.data if self.compact else self.data.encode()
                )
                if self.back and self.overviews == 1:
                    pulse(20)
                    pulse(10)
                else:
                    pulse(10)
            else:
                self.zooms += 1
                before = hashlib.sha256(ui.framebuffer()).hexdigest()
                pulse(19)
                pulse(18)
                for _ in range(50):
                    ui.tick()
                    time.sleep_ms(5)
                assert hashlib.sha256(ui.framebuffer()).hexdigest() != before
                pulse(10)
        elif builder == 'main_menu_screen':
            raise StopFlowBasedTest()
        else:
            raise ValueError('Unreviewed export screen')


settings = Settings.get_instance()
keys = (C.SETTING__COMPACT_SEEDQR, C.SETTING__ENCRYPTED_QR, C.SETTING__DIRE_WARNINGS)
old = [settings.get_value(key) for key in keys]
for key, value in zip(keys, (C.OPTION__ENABLED, C.OPTION__DISABLED, C.OPTION__ENABLED)):
    settings.set_value(key, value, save=False)
try:
    for number, fixture in enumerate(fixtures):
        Renderer._instance = None
        driver = Driver(fixture, back=number == 0)
        Renderer.configure_instance(backend=driver)
        Controller._instance = None
        c = Controller.get_instance()
        seed = Seed(list(fixture[0]))
        c.storage.set_pending_seed(seed)
        c.storage.finalize_pending_seed()
        destination = Destination(SeedBackupView, view_args={'seed': seed})
        c.back_stack.append(destination)
        machine.clear_reset_record()
        machine.set_reset_marker(0x51524558)
        c.start(initial_destination=destination, skip_startup_interstitials=True)
        assert driver.failure is None, driver.failure
        assert driver.closed and driver.zooms == 1 and driver.overviews == (2 if number == 0 else 1)
        assert machine.last_reset() is None
        c.discard_seed(seed)
        assert c.storage.num_seeds() == 0
        print(
            '@@PASS original-seedqr-export-native-pixels-pan-exit',
            len(fixture[0]),
            fixture[1],
            fixture[4],
            driver.overviews,
        )
finally:
    for key, value in zip(keys, old):
        settings.set_value(key, value, save=False)
# The existing inactivity policy must unwind a displayed private QR to Home.
from seedsigner_port.view_seed import SeedTranscribeSeedQRWholeQRView
from seedsigner_port.qr_type import QRType
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port import clock


class IdleDriver(Driver):
    def checked(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        if builder == 'seed_transcribe_whole_qr_screen':
            assert hashlib.sha256(bytes.fromhex(cfg['matrix_hex'])).hexdigest() == self.digest
            self.overviews += 1
            HardwareButtons.get_instance().last_input_time = int(clock.time() * 1000) - 60001
        elif builder == 'main_menu_screen':
            assert qr.decode(drawn_luma(), 240, 240) is None
            raise StopFlowBasedTest()
        else:
            raise ValueError('Unexpected idle export screen')


Renderer._instance = None
driver = IdleDriver(fixtures[0])
Renderer.configure_instance(backend=driver)
Controller._instance = None
c = Controller.get_instance()
seed = Seed(list(fixtures[0][0]))
alias = seed.seed_bytes
c.storage.set_pending_seed(seed)
c.storage.finalize_pending_seed()
destination = Destination(
    SeedTranscribeSeedQRWholeQRView,
    view_args={'seed': seed, 'seedqr_format': QRType.SEED__SEEDQR, 'num_modules': fixtures[0][4]},
)
c.back_stack.append(destination)
old_timer = settings.get_value(C.SETTING__WIPE_TIMER)
HardwareButtons.get_instance().update_last_input_time()
settings.set_value(C.SETTING__WIPE_TIMER, 1, save=False)
machine.clear_reset_record()
machine.set_reset_marker(0x51524558)
try:
    c.start(initial_destination=destination, skip_startup_interstitials=True)
finally:
    settings.set_value(C.SETTING__WIPE_TIMER, old_timer, save=False)
assert driver.failure is None, driver.failure
assert driver.overviews == 1 and alias == bytes(64)
assert c.storage.num_seeds() == 0 and c.storage.get_pending_seed() is None
assert machine.last_reset() is None
ui.overlays(5)
HardwareButtons.get_instance().update_last_input_time()
print('@@PASS original-seedqr-idle-wipe-clears-visible-qr-home')
Renderer._instance = None
r = Renderer.get_instance()
ui.overlays(0, 0)
r.session.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
gc.collect()
