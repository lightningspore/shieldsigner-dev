# SPDX-License-Identifier: MIT
# Public BIP39 fixtures only; actual native keys, original Views and real roots.
from seedsigner_port.controller import Controller, StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.view_seed import SeedsMenuView
from seedsigner_port.navigation import Destination
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.seed import Seed
import ui, json, gc, machine
from seedsigner_port.settings_store import Settings, SettingsConstants as C

settings = Settings.get_instance()
original_lengths = list(settings.get_value(C.SETTING__SEED_WORD_LENGTHS))
settings.set_value(C.SETTING__SEED_WORD_LENGTHS, [12, 15, 18, 21, 24], save=False)
ui.init()


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


session = ScreenSession()
words = Seed.get_wordlist()
# A one-letter prefix has no visible candidate, hence KEY2 must not accept it.
session.show_screen(
    'SeedMnemonicEntryScreen',
    {'title': 'Public word entry', 'wordlist': words, 'initial_letters': ['a']},
)
pulse(50)
assert ui.event() is None
pulse(10)
pulse(19)  # lock a, float b: visible candidates now begin ab.
pulse(50)
assert session.screen_result(ui.event()) == 'abandon'
assert ui.event() is None
for initial, want, keys in (
    (['a', 'b'], 'about', [51, 51, 51, 50]),
    (list('about'), 'about', [50]),
):
    session.show_screen(
        'SeedMnemonicEntryScreen',
        {'title': 'Public candidate', 'wordlist': words, 'initial_letters': initial},
    )
    for key in keys:
        pulse(key)
    assert session.screen_result(ui.event()) == want
session.show_screen(
    'SeedMnemonicEntryScreen', {'title': 'Public Back', 'wordlist': words, 'initial_letters': ['a']}
)
pulse(17)
pulse(10)
assert session.screen_result(ui.event()) == 1000
session.show_screen(
    'SeedMnemonicEntryScreen',
    {'title': 'Public correction', 'wordlist': words, 'initial_letters': list('abandon')},
)
for _ in range(13):
    pulse(19)  # n -> DEL, actual keyboard selection.
for _ in range(5):
    pulse(10)  # Delete and retain ab.
for _ in range(12):
    pulse(20)  # DEL -> o, float abo -> about.
pulse(50)
assert session.screen_result(ui.event()) == 'about'
print('@@PASS native-mnemonic-prefix-accept-scroll-back-delete')
fixtures = [
    (12, 'about', '73c5da0a'),
    (15, 'address', '3726240e'),
    (18, 'agent', 'e08b8ac3'),
    (21, 'admit', '359c0843'),
    (24, 'art', '5436d724'),
]  # Independent public CPython embit0.8.0 oracle.


class Driver:
    def __init__(self, mode, size, last, fingerprint):
        self.size = size
        self.last = last
        self.fingerprint = fingerprint
        self.mode = mode
        self.entries = []
        self.load_count = 0
        self.invalids = 0
        self.finalized = False
        self.failure = None

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        c = Controller.get_instance()
        if builder == 'seed_mnemonic_entry_screen':
            index = int(cfg['top_nav']['title'].split('#')[1]) - 1
            self.entries.append(index)
            assert cfg['wordlist'] == words
            if self.mode == 'cancel':
                if index == 0 and len(self.entries) == 1:
                    pulse(10)
                    pulse(19)
                    pulse(50)
                else:
                    # Back from #2 restores #1; Back from #1 cancels the entry.
                    for _ in range(6):
                        pulse(17)
                    pulse(10)
                return
            if cfg['initial_letters'] == ['a']:
                pulse(10)  # Commit a, then float the desired second letter.
                target = self.last if index == self.size - 1 and self.mode == 'valid' else 'abandon'
                for _ in range(ord(target[1]) - ord('a')):
                    pulse(19)
                candidates = [word for word in words if word.startswith(target[:2])]
                for _ in range(candidates.index(target)):
                    pulse(51)
            else:
                assert self.mode == 'edit' and cfg['initial_letters'] == list('abandon')
                if index == self.size - 1:
                    for _ in range(13):
                        pulse(19)
                    for _ in range(5):
                        pulse(10)
                    for _ in range(12):
                        pulse(20)
            pulse(50)
        elif builder == 'seed_finalize_screen':
            assert self.mode in ('valid', 'edit') and cfg['fingerprint'] == self.fingerprint
            assert c.storage.get_pending_seed().mnemonic_list == ['abandon'] * (self.size - 1) + [
                self.last
            ]
            assert c.storage.pending_mnemonic_length == 0
            self.finalized = True
            pulse(10)
        elif builder == 'large_icon_status_screen':
            assert (
                self.mode in ('invalid', 'edit') and cfg['top_nav']['title'] == 'Invalid Mnemonic!'
            )
            assert (
                c.storage.pending_mnemonic == ['abandon'] * 12
                and c.storage.get_pending_seed() is None
            )
            self.invalids += 1
            if self.mode == 'invalid':
                pulse(18)  # Original Discard; edit remains first action.
            pulse(10)
        elif builder == 'button_list_screen':
            title = cfg['top_nav']['title']
            if title == 'Load a Seed':
                self.load_count += 1
                if self.load_count > 1:
                    assert self.mode == 'cancel' and c.storage.pending_mnemonic_length == 0
                    assert self.entries == [0, 1, 0]
                    raise StopFlowBasedTest()
                labels = [x if isinstance(x, str) else x['label'] for x in cfg['button_list']]
                selected = labels.index('Enter %d-word seed' % self.size)
                for _ in range(selected):
                    pulse(18)
                pulse(10)
            else:
                assert (
                    self.mode in ('valid', 'edit')
                    and title == self.fingerprint
                    and c.storage.num_seeds() == 1
                )
                pulse(20)
                pulse(10)
        elif builder == 'main_menu_screen':
            raise StopFlowBasedTest()
        else:
            self.failure = (builder, cfg['top_nav'])
            raise StopFlowBasedTest()


try:
    for mode, size, last, fingerprint in [('valid',) + tuple(fixture) for fixture in fixtures] + [
        (mode,) + tuple(fixtures[0]) for mode in ('invalid', 'edit', 'cancel')
    ]:
        Renderer._instance = None
        driver = Driver(mode, size, last, fingerprint)
        Renderer.configure_instance(backend=driver)
        Controller._instance = None
        c = Controller.get_instance()
        machine.clear_reset_record()
        machine.set_reset_marker(0x574F5244)
        c.start(initial_destination=Destination(SeedsMenuView), skip_startup_interstitials=True)
        assert driver.failure is None, driver.failure
        assert machine.last_reset() is None
        if mode in ('valid', 'edit'):
            assert (
                driver.entries == list(range(size)) * (2 if mode == 'edit' else 1)
                and driver.finalized
            )
            seed = c.storage.seeds[0]
            assert seed.get_fingerprint() == fingerprint
            c.discard_seed(seed)
        else:
            assert c.storage.num_seeds() == 0 and c.storage.pending_mnemonic_length == 0
            assert c.storage.get_pending_seed() is None
            if mode == 'invalid':
                assert driver.invalids == 1 and driver.entries == list(range(12))
        print('@@PASS original-mnemonic-' + mode + '-flow-real-lvgl', size, len(driver.entries))
finally:
    settings.set_value(C.SETTING__SEED_WORD_LENGTHS, original_lengths, save=False)
Renderer._instance = None
renderer = Renderer.get_instance()
ui.overlays(0, 0)
renderer.session.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
gc.collect()
