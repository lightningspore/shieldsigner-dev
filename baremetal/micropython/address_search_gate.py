# SPDX-License-Identifier: MIT
# PUBLIC source simple/continued/expanded searches through actual native screens.
import ui, json, gc, machine, camera
from seedsigner_port.seed import Seed
from seedsigner_port.controller import Controller, StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.view_seed import SeedAddressVerificationView
from seedsigner_port.settings_store import Settings, SettingsConstants as C
from seedsigner_port.hardware_buttons import HardwareButtons

fixtures = [
    (
        'simple0',
        'bc1q5gxzrugds23phf3xd2rw097sv0zaw43ql88nvd',
        "m/84'/0'/0'",
        'nat',
        0,
        False,
        'simple',
    ),
    (
        'next100',
        'bc1qthm54rn8c7zapf90k4j3r4txmldwdghwd69q27',
        "m/84'/0'/0'",
        'nat',
        150,
        True,
        'simple-batch',
    ),
    (
        'nonstandard',
        'bc1qnswecuzd7wqky6csdtrae6lwdgs77zxku7tspw',
        "m/44'/0'/1'",
        'nat',
        1,
        True,
        'expanded-nonstandard',
    ),
    (
        'next10',
        'bc1qqc59xephch5hmlrye752a90y9n4j6csclt52qu',
        "m/84'/0'/0'",
        'nat',
        10,
        False,
        'expanded-batch',
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


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def choose(cfg, label):
    labels = [b if isinstance(b, str) else b['label'] for b in cfg['button_list']]
    # Status screens may start in read-first scroll mode. Reach the last row
    # with bounded real DOWN inputs, then navigate up to the requested action.
    for _ in range(64):
        pulse(18)
    for _ in range(len(labels) - 1 - labels.index(label)):
        pulse(17)
    pulse(10)
    return labels.index(label)


class Driver:
    def __init__(self, fixture):
        self.fixture = fixture
        self.workers = []
        self.not_found = 0
        self.success = 0
        self.failure = None
        self.updates = 0
        self.routes = []
        self.events = []
        self.expected = None

    def __getattr__(self, name):
        return getattr(ui, name)

    def event(self):
        value = ui.event()
        if value is not None:
            self.events.append(value)
            print('@@SEARCH_EVENT', self.fixture[0], self.routes[-1], value, self.expected)
            if self.expected is not None:
                expected = self.expected
                self.expected = None
                if value != (1, expected, ''):
                    self.failure = ('unexpected-native-selection', expected, value)
                    raise StopFlowBasedTest()
        return value

    def address_progress(self, text):
        ui.address_progress(text)
        self.updates += 1

    def render(self, builder, encoded):
        try:
            self.checked(builder, encoded)
        except StopFlowBasedTest:
            raise
        except Exception as e:
            self.failure = (builder, type(e).__name__)
            raise StopFlowBasedTest()

    def checked(self, builder, encoded):
        cfg = json.loads(encoded)
        self.routes.append(builder)
        print(
            '@@SEARCH_ROUTE',
            self.fixture[0],
            builder,
            self.not_found,
            self.success,
            [(w.active, w.threadsafe_counter.cur_count) for w in self.workers],
        )
        ui.render(builder, encoded)
        name, address, path, kind, index, change, mode = self.fixture
        if builder == 'seed_address_verification_screen':
            worker = c.back_stack[-1].view.addr_verification_thread
            assert worker.active and worker.threadsafe_counter.worker is worker
            self.workers.append(worker)
            if len(self.workers) > 1:
                assert all(
                    not w.active and w.threadsafe_counter.worker is None for w in self.workers[:-1]
                )
        elif builder == 'large_icon_status_screen':
            assert (
                cfg['top_nav']['title'] == 'Not Found'
                and cfg['status_headline'] == 'Address Not Verified'
            )
            self.not_found += 1
            if mode == 'simple-batch':
                assert self.workers[-1].threadsafe_counter.cur_count == 100
                self.expected = choose(cfg, 'Next 100')
            elif mode == 'expanded-batch':
                assert self.workers[-1].threadsafe_counter.cur_count == 3280
                self.expected = choose(cfg, 'Check Next 10')
            else:
                raise AssertionError('Unexpected not-found route')
        elif builder == 'seed_address_verification_success_screen':
            self.success += 1
            assert cfg['address'] == address and cfg['index_text'] == 'index %d' % index
            assert cfg['address_type_text'] == ('change address' if change else 'receive address')
            assert cfg['is_non_standard'] == (mode == 'expanded-nonstandard')
            value = c.unverified_address
            assert value['verified_index'] == index and value['verified_index_is_change'] == change
            assert value['derivation_path'] == path and value['script_type'] == kind
            assert all(not w.active and w.threadsafe_counter.worker is None for w in self.workers)
            if number == 0:
                picture = ui.framebuffer()
                print('@@UI_RGB565_BEGIN 240 240')
                for y in range(240):
                    print('@@UI_ROW', bytes(picture[y * 480 : (y + 1) * 480]).hex())
                print('@@UI_RGB565_END')
            self.expected = choose(cfg, 'OK')
        elif builder == 'main_menu_screen':
            raise StopFlowBasedTest()
        else:
            raise AssertionError('Unexpected native search route')


ui.init()
ui.overlays(0, 0)
ui.overlays(5)
ui.overlays(2)
settings = Settings.get_instance()
old_network = settings.get_value(C.SETTING__NETWORK)
settings.set_value(C.SETTING__NETWORK, C.MAINNET, save=False)
machine.set_reset_marker(0x41445352)
try:
    for number, fixture in enumerate(fixtures):
        name, address, path, kind, index, change, mode = fixture
        HardwareButtons.get_instance().update_last_input_time()
        Renderer._instance = None
        driver = Driver(fixture)
        Renderer.configure_instance(backend=driver)
        Controller._instance = None
        c = Controller.get_instance()
        seed = Seed(words, passphrase='PUBLIC')
        c.storage.set_pending_seed(seed)
        c.storage.finalize_pending_seed()
        c.unverified_address = {
            'address': address,
            'sig_type': C.SINGLE_SIG,
            'script_type': C.NATIVE_SEGWIT,
            'network': C.MAINNET,
            'derivation_path': "m/84'/0'/0'",
        }
        d = Destination(
            SeedAddressVerificationView,
            view_args={'seed': seed, 'use_expanded': mode.startswith('expanded')},
        )
        c.back_stack.append(d)
        c.start(initial_destination=d, skip_startup_interstitials=True)
        assert driver.failure is None, driver.failure
        assert driver.success == 1 and driver.not_found == (1 if mode.endswith('batch') else 0), (
            name,
            driver.success,
            driver.not_found,
            driver.routes,
            driver.events,
            [(w.active, w.threadsafe_counter.cur_count) for w in driver.workers],
        )
        assert c.storage.num_seeds() == 1
        c.discard_seed(seed)
        assert machine.last_reset() is None and camera.preview_status() == (False, 0)
        gc.collect()
        print(
            '@@PASS original-address-search-continuation-expanded',
            number,
            name,
            len(driver.workers),
            driver.updates,
        )
finally:
    settings.set_value(C.SETTING__NETWORK, old_network, save=False)
Renderer._instance = None
r = Renderer.get_instance()
ui.overlays(0, 0)
r.session.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
gc.collect()
