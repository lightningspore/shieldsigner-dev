# SPDX-License-Identifier: MIT
# Public original export Views through real native keys, details and QR pixels.
import ui, qr, json, gc, machine, camera
from seedsigner_port.seed import Seed
from seedsigner_port.controller import Controller, StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.view_seed import SeedOptionsView
from seedsigner_port.settings_store import Settings, SettingsConstants as C

fixtures = [
    (
        'M',
        'ss',
        'nat',
        0,
        "m/84'/0'/0'",
        'zpub6s7nZx8HjMQ8mDGtp5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBSmYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd52D7Rk7owcd',
        "[4f4fbd02/84'/0'/0']zpub6s7nZx8HjMQ8mDGtp5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBSmYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd52D7Rk7owcd",
        [
            (0, False, 'bc1q5gxzrugds23phf3xd2rw097sv0zaw43ql88nvd'),
            (7, True, 'bc1q528lyx5hlkfglz82eymmymeqef2h784e869san'),
        ],
    ),
    (
        'M',
        'ms',
        'nat',
        0,
        "m/48'/0'/0'/2'",
        'Zpub751xj3uUrAmWkxyK1PLTVtYz1hXSUVQgBCxrZbktTS2yQSVvkjQpdKnuNuYwk8boWesgNwbzJ9gfdfxW7Ty9r4Hr47tDMzG3CNFXyqCwXe4',
        "[4f4fbd02/48'/0'/0'/2']Zpub751xj3uUrAmWkxyK1PLTVtYz1hXSUVQgBCxrZbktTS2yQSVvkjQpdKnuNuYwk8boWesgNwbzJ9gfdfxW7Ty9r4Hr47tDMzG3CNFXyqCwXe4",
        [],
    ),
    (
        'T',
        'ss',
        'nat',
        0,
        "m/84'/1'/0'",
        'vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D',
        "[4f4fbd02/84'/1'/0']vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D",
        [
            (0, False, 'tb1q4p5heuz43c3fl2zxrlpalhhrns988x3ujs7xnf'),
            (7, True, 'tb1q0qtn6e2l3aep250hlac25ljqk3we7e0eysr0m0'),
        ],
    ),
    (
        'T',
        'ms',
        'nat',
        0,
        "m/48'/1'/0'/2'",
        'Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My',
        "[4f4fbd02/48'/1'/0'/2']Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My",
        [],
    ),
]  # PUBLIC CPython oracle.
words = [
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
]  # PUBLIC prepared mnemonic.
configs = {}
machine.set_reset_marker(0x5850464C)


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def choose(cfg, label):
    labels = [b if isinstance(b, str) else b['label'] for b in cfg['button_list']]
    for _ in range(labels.index(label)):
        pulse(18)
    pulse(10)


def luma():
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
        self.fixture = fixture
        self.back = back
        self.details = 0
        self.qrs = 0
        self.warnings = 0
        self.options = 0
        self.route = None
        self.failure = None
        self.builder = None

    def __getattr__(self, name):
        return getattr(ui, name)

    def event(self):
        event = ui.event()
        if self.builder == 'qr_display_screen' and event is not None and event[0] == 4:
            assert event[1] == 224
            pulse(10)
        return event

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
        self.builder = builder
        if number == 0 and builder in (
            'loading_spinner_screen',
            'seed_export_xpub_details_screen',
            'qr_display_screen',
        ):
            configs[builder] = cfg
        network, sig, kind, account, path, key, payload, addresses = self.fixture
        if builder == 'button_list_screen':
            self.options += 1
            if self.options == 1:
                choose(cfg, 'Export xpub')
            else:
                assert self.back and self.details == 1
                pulse(20)
                pulse(10)
        elif builder == 'large_icon_status_screen':
            if cfg['top_nav']['title'] == 'Verify Address':
                assert sig == C.SINGLE_SIG and self.qrs == 1
                assert 'your wallet software' in cfg['text']
                self.route = 'verify-address'
                raise StopFlowBasedTest()
            assert cfg['status_headline'] == 'Privacy Leak!'
            self.warnings += 1
            pulse(10)
        elif builder == 'loading_spinner_screen':
            assert cfg['text'] == 'Generating xpub...'
        elif builder == 'seed_export_xpub_details_screen':
            self.details += 1
            assert (
                cfg['fingerprint'] == payload[1:9]
                and cfg['derivation_path'] == path
                and cfg['xpub'] == key
            )
            assert cfg['button_list'] == ['Export xpub']
            if self.back:
                pulse(20)
                pulse(10)
            else:
                pulse(10)
        elif builder == 'qr_display_screen':
            self.qrs += 1
            assert bytes.fromhex(cfg['qr_data']).decode() == payload
            assert qr.decode(luma(), 240, 240) == payload.encode()
            if number == 0:
                picture = ui.framebuffer()
                print('@@UI_RGB565_BEGIN 240 240')
                for y in range(240):
                    print('@@UI_ROW', bytes(picture[y * 480 : (y + 1) * 480]).hex())
                print('@@UI_RGB565_END')
            pulse(18)  # Actual native brightness event; event() then emits exit.
        elif builder == 'main_menu_screen':
            self.route = 'home'
            raise StopFlowBasedTest()
        else:
            raise AssertionError('Unreviewed native export builder')


settings = Settings.get_instance()
keys = (
    C.SETTING__NETWORK,
    C.SETTING__SIG_TYPES,
    C.SETTING__SCRIPT_TYPES,
    C.SETTING__XPUB_QR_FORMAT,
    C.SETTING__ACCOUNT_PROMPT,
    C.SETTING__PRIVACY_WARNINGS,
    C.SETTING__XPUB_DETAILS,
    C.SETTING__QR_BRIGHTNESS,
    C.SETTING__QR_BRIGHTNESS_TIPS,
)
old = [settings.get_value(k) for k in keys]
try:
    for number, fixture in enumerate(fixtures + [fixtures[-1]]):
        network, sig, kind, account, path, key, payload, addresses = fixture
        back = number == len(fixtures)
        values = (
            network,
            [sig],
            [kind],
            [C.XPUB_QR_FORMAT__STATIC],
            C.OPTION__DISABLED,
            C.OPTION__ENABLED,
            C.OPTION__ENABLED,
            255,
            C.OPTION__DISABLED,
        )
        for k, v in zip(keys, values):
            settings.set_value(k, v, save=False)
        Renderer._instance = None
        driver = Driver(fixture, back)
        Renderer.configure_instance(backend=driver)
        Controller._instance = None
        c = Controller.get_instance()
        seed = Seed(words, passphrase='PUBLIC')
        c.storage.set_pending_seed(seed)
        c.storage.finalize_pending_seed()
        c.start(
            initial_destination=Destination(SeedOptionsView, view_args={'seed': seed}),
            skip_startup_interstitials=True,
        )
        assert driver.failure is None, driver.failure
        assert driver.details == 1 and driver.warnings == 1 and driver.qrs == (0 if back else 1)
        assert driver.route == ('home' if sig == C.MULTISIG or back else 'verify-address')
        assert settings.get_value(C.SETTING__QR_BRIGHTNESS) == (255 if back else 224)
        assert c.storage.num_seeds() == 1 and c.storage.get_pending_seed() is None
        c.discard_seed(seed)
        assert camera.preview_status() == (False, 0) and machine.last_reset() is None
        gc.collect()
        print(
            '@@PASS original-static-xpub-details-qr-source-route',
            number,
            network,
            sig,
            back,
            driver.route,
        )
finally:
    for k, v in zip(keys, old):
        settings.set_value(k, v, save=False)
home = {'top_nav': {'title': 'Home'}, 'button_list': ['Scan', 'Seeds', 'Tools', 'Settings']}


def cycle():
    for builder in (
        'loading_spinner_screen',
        'seed_export_xpub_details_screen',
        'qr_display_screen',
    ):
        ui.render(builder, json.dumps(configs[builder]))
    ui.render('main_menu_screen', json.dumps(home))


cycle()
cycle()
baseline = ui.status()['heap_bytes']
for _ in range(20):
    cycle()
    gc.collect()
    assert ui.status()['heap_bytes'] == baseline
assert machine.last_reset() is None
print('@@PASS native-xpub-loading-details-qr-20-teardowns-stable', baseline)
Renderer._instance = None
r = Renderer.get_instance()
ui.overlays(0, 0)
r.session.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
