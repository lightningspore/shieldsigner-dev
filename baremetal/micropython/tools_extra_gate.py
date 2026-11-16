# SPDX-License-Identifier: MIT
# Original Tools > Text QR Code, Password Generator and SLIP39 seed flows on
# native screens with key pulses. PUBLIC data only: seed abandon x11 about and
# scripted dice patterns. Oracles are computed on the host from upstream
# SeedSigner/embit code (tools/tools_extra_oracle.py) and pasted below.
# Optional: CASES=('textqr-scan',) needs the host to show TEXT_QR on the monitor.
import ui, json, qr, gc, machine
from seedsigner_port.seed import Seed
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.navigation import Destination
from seedsigner_port.settings_store import Settings, SettingsConstants as C
from seedsigner_port.camera_entropy_views import ToolsMenuView

print('@@TOOLS_RESET_BEFORE', machine.last_reset())
machine.clear_reset_record()
ORACLE = {
    'pw-dice-hex': '287b331037fc586eb6258a44488b2fe6',
    'pw-bip85-hex': '866a12e42e31a09aa8ca4f25a02e999e',
    'pw-bip85-eff-long': 'skillet entity numbness affected reveler',
    'pw-bip85-base85': 'IPqw{iRWU<W@1+9_D73O',
    'pw-bip85-bip39': 'owner.bonus.scissors.column.patch.stuff.follow.column.someone.loop.danger.region',
    'pw-bip85-dicerolls': '4,11,5,1,9,6,7,9',
}  # tools/tools_extra_oracle.py
TEXT_QR = globals().get('TEXT_QR', 'SHIELDSIGNER TEXT QR 1')


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def labels(cfg):
    return [b if isinstance(b, str) else b.get('label') for b in cfg.get('button_list', [])]


def choose(cfg, label):
    names = labels(cfg)
    assert label in names, (label, names)
    cur = cfg.get('initial_selected_index', 0)
    target = names.index(label)
    for _ in range(abs(target - cur)):
        pulse(18 if target > cur else 17)
    pulse(10)


def digits(text):
    # 0-9 keyboard, 5 columns, focus starts on 0; 51 saves.
    for ch in text:
        v = int(ch)
        r, c = divmod(v, 5)
        for _ in range(r):
            pulse(18)
        for _ in range(c):
            pulse(19)
        pulse(10)
        for _ in range(c):
            pulse(20)
        for _ in range(r):
            pulse(17)
    pulse(51)


FACES = []


def dice(n):
    # Scripted varied faces on the 3-column dice keyboard (focus starts on face 1);
    # navigate relative to the origin like digits().
    del FACES[:]
    for i in range(n):
        f = (i * 7 + i // 3) % 6
        r, c = divmod(f, 3)
        FACES.append(f + 1)
        for _ in range(r):
            pulse(18)
        for _ in range(c):
            pulse(19)
        pulse(10)
        for _ in range(c):
            pulse(20)
        for _ in range(r):
            pulse(17)


def decoded_frame():
    raw = ui.framebuffer()
    pixels = bytearray(240 * 240)
    for i in range(240 * 240):
        v = (raw[2 * i] << 8) | raw[2 * i + 1]
        pixels[i] = (
            ((v >> 11) * 255 // 31) * 77
            + (((v >> 5) & 63) * 255 // 63) * 150
            + ((v & 31) * 255 // 31) * 29
        ) >> 8
    return qr.decode(pixels, 240, 240)


class Stop(Exception):
    pass


class Driver:
    def __init__(self, steps):
        self.steps = list(steps)
        self.seen = []
        self.out = {}
        self.waiting = None

    def __getattr__(self, name):
        return getattr(ui, name)

    def tick(self):
        result = ui.tick()
        if self.waiting is not None and not ui.qr_tip_active():
            expect = self.waiting
            self.waiting = None
            got = decoded_frame()
            assert got == expect.encode(), (got, expect)
            self.out['qr_pixels'] = got.decode()
            pulse(20)
        return result

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        title = cfg.get('top_nav', {}).get('title')
        self.seen.append((builder, title))
        if builder == 'loading_spinner_screen':
            return
        assert self.steps, ('Unexpected extra screen', builder, title, labels(cfg))
        want, action = self.steps.pop(0)
        assert want == (builder, title) or (want[1] is None and want[0] == builder), (
            'Expected',
            want,
            'got',
            (builder, title),
            labels(cfg),
        )
        action(self, cfg)


def stop(d, cfg):
    raise Stop()


def pick(label):
    return lambda d, cfg: choose(cfg, label)


def run(name, steps, setup=None):
    Renderer._instance = None
    driver = Driver(steps)
    Renderer.configure_instance(backend=driver)
    Controller._instance = None
    c = Controller.get_instance()
    seed = Seed(['abandon'] * 11 + ['about'])
    c.storage.set_pending_seed(seed)
    c.storage.finalize_pending_seed()
    if setup:
        setup(c)
    d = Destination(ToolsMenuView)
    try:
        for _ in range(40):
            c.back_stack.append(d)
            d = d.run()
            if d.View_cls.__name__ == 'BackStackView':
                c.back_stack.pop()
                d = c.back_stack.pop()
        raise AssertionError(('did not finish', driver.seen))
    except Stop:
        pass
    finally:
        c.discard_seed(seed)
        c.create_slip39 = False
    assert not driver.steps, ('Unused steps', driver.steps, driver.seen)
    gc.collect()
    return driver


def check(name, got):
    exp = ORACLE.get(name)
    if exp is not None:
        assert got == exp, (name, got, exp)
    print('@@PASS', name, repr(got), 'oracle' if exp is not None else 'NO-ORACLE')


CASES = globals().get(
    'CASES',
    (
        'textqr-scan',
        'menu',
        'textqr',
        'pw-dice-hex',
        'pw-bip85-hex',
        'pw-bip85-eff-long',
        'pw-bip85-base85',
        'pw-bip85-dicerolls',
        'pw-bip85-bip39',
        'pw-system-rng',
    ),
)
ui.init()
settings = Settings.get_instance()
old_slip = settings.get_value(C.SETTING__SLIP39_SEEDS)
try:
    if 'menu' in CASES:
        got = {}

        def menu(d, cfg):
            got['labels'] = labels(cfg)
            raise Stop()

        run('menu', [(('button_list_screen', 'Tools'), menu)])
        assert (
            'Password Generator' in got['labels']
            and 'Text QR Code' in got['labels']
            and 'SLIP39 seed' not in got['labels']
        ), got
        # SLIP39 creation needs an RNG for share generation; omitted even when enabled.
        settings.set_value(C.SETTING__SLIP39_SEEDS, C.OPTION__ENABLED, save=False)
        run('menu-slip', [(('button_list_screen', 'Tools'), menu)])
        settings.set_value(C.SETTING__SLIP39_SEEDS, old_slip, save=False)
        assert 'SLIP39 seed' not in got['labels'], got
        print('@@PASS tools-menu', got['labels'])
    if 'textqr' in CASES:
        out = {}

        def entry(d, cfg):
            assert cfg['initial_text'] == ''
            pulse(10)
            pulse(19)
            pulse(10)
            pulse(51)

        def review(d, cfg):
            out['review'] = cfg['text']
            choose(cfg, 'Generate QR code')

        def whole(d, cfg):
            out['modules'] = cfg['num_modules']
            out['qr_data'] = cfg['qr_data']
            pulse(10)

        def zoom(d, cfg):
            pulse(10)

        steps = [
            (('button_list_screen', 'Tools'), pick('Text QR Code')),
            (('button_list_screen', 'Text QR Code'), pick('Encode text')),
            (('seed_add_passphrase_screen', 'Text to Encode'), entry),
            (('button_list_screen', 'Text to Encode'), review),
            (('button_list_screen', 'Transcribe Mode ?'), pick('Transcribe mode')),
            (('seed_transcribe_whole_qr_screen', 'Transcribe Text QR'), whole),
            (('seed_transcribe_zoomed_qr_screen', None), zoom),
            (('button_list_screen', 'Confirm Text QR ?'), pick('Done')),
            (('button_list_screen', 'Text QR Code'), pick('Encode text')),
            (
                ('seed_add_passphrase_screen', 'Text to Encode'),
                lambda d, cfg: (pulse(10), pulse(51)),
            ),
            (('button_list_screen', 'Text to Encode'), pick('Generate QR code')),
            (('button_list_screen', 'Transcribe Mode ?'), pick('FullScreen mode')),
            (
                ('qr_display_screen', None),
                lambda d, cfg: setattr(
                    d,
                    'waiting',
                    bytes.fromhex(cfg['qr_data']).decode()
                    if cfg.get('data_encoding') == 'hex'
                    else cfg['qr_data'],
                ),
            ),
            (('button_list_screen', 'Text QR Code'), stop),
        ]
        d = run('textqr', steps)
        assert (
            out['review'] == out['qr_data'] and out['modules'] == 21 and len(out['review']) == 2
        ), out
        print('@@PASS textqr-encode-transcribe-fullscreen', out, d.out)
    if 'textqr-scan' in CASES:
        out = {}

        def decoded(d, cfg):
            out['text'] = cfg['text']
            out['buttons'] = labels(cfg)
            raise Stop()

        steps = [
            (('button_list_screen', 'Tools'), pick('Text QR Code')),
            (('button_list_screen', 'Text QR Code'), pick('Decode QR code')),
            (('button_list_screen', 'Decoded Text'), decoded),
        ]
        run('textqr-scan', steps)
        assert out['text'] == TEXT_QR, out
        print('@@PASS textqr-decode-camera', out)

    def password(name, ptype, strength, source, extra, qr=False):
        out = {}

        def review(d, cfg):
            out['password'] = cfg['text']
            if qr:
                choose(cfg, 'Next')
            else:
                raise Stop()

        steps = [
            (('button_list_screen', 'Tools'), pick('Password Generator')),
            (('button_list_screen', 'Password Type'), pick(ptype)),
        ]
        if strength:
            steps.append((('button_list_screen', 'Password Strength'), pick(strength)))
        steps += extra(source) + [(('button_list_screen', 'Password'), review)]
        if qr:
            steps += [
                (('button_list_screen', 'Save Password'), pick('Show as QR')),
                (('button_list_screen', 'Transcribe Mode ?'), pick('FullScreen mode')),
                (
                    ('qr_display_screen', None),
                    lambda d, cfg: setattr(d, 'waiting', out['password']),
                ),
                (('button_list_screen', 'Tools'), stop),
            ]
        d = run(name, steps)
        if qr:
            assert d.out['qr_pixels'] == out['password']
        check(name, out['password'])

    src = lambda label: [(('button_list_screen', 'Entropy Source'), pick(label))]
    bip85_index = [(('keyboard_screen', 'BIP85 Index'), lambda d, cfg: digits('0'))]
    if 'pw-dice-hex' in CASES:
        password(
            'pw-dice-hex',
            'Hex',
            '128 bits',
            'Dice',
            lambda s: (
                src(s)
                + [
                    (
                        ('keyboard_screen', None),
                        lambda d, cfg: (cfg['return_after_n_chars'] == 50 or 1 / 0, dice(50)),
                    )
                ]
            ),
            qr=True,
        )
    if 'pw-bip85-hex' in CASES:
        password('pw-bip85-hex', 'Hex', '128 bits', 'BIP85', lambda s: src(s) + bip85_index)
    if 'pw-bip85-eff-long' in CASES:
        password(
            'pw-bip85-eff-long',
            'Diceware-EFF Long',
            '64 bits',
            'BIP85',
            lambda s: src(s) + bip85_index + [(('button_list_screen', 'Separator'), pick('Space'))],
        )
    if 'pw-bip85-base85' in CASES:
        password('pw-bip85-base85', 'Base85', '128 bits', 'BIP85', lambda s: src(s) + bip85_index)
    if 'pw-bip85-bip39' in CASES:
        password(
            'pw-bip85-bip39',
            'Diceware-BIP39',
            '128 bits',
            'BIP85',
            lambda s: src(s) + bip85_index + [(('button_list_screen', 'Separator'), pick('.'))],
        )
    if 'pw-bip85-dicerolls' in CASES:
        password(
            'pw-bip85-dicerolls',
            'Dice Rolls',
            None,
            'BIP85',
            lambda s: (
                [
                    (('button_list_screen', 'Dice Sides'), pick('20 sides')),
                    (('keyboard_screen', 'Number of Rolls'), lambda d, cfg: digits('8')),
                ]
                + src(s)
                + bip85_index
            ),
        )
    if 'pw-system-rng' in CASES:
        out = {}

        def warn(d, cfg):
            out['text'] = cfg.get('text')
            raise Stop()

        run(
            'pw-system-rng',
            [
                (('button_list_screen', 'Tools'), pick('Password Generator')),
                (('button_list_screen', 'Password Type'), pick('Hex')),
                (('button_list_screen', 'Password Strength'), pick('128 bits')),
                (('button_list_screen', 'Entropy Source'), pick('System RNG')),
                (('large_icon_status_screen', 'System RNG Error'), warn),
            ],
        )
        assert out['text'] == 'System RNG monitor unavailable', out
        print('@@PASS pw-system-rng-honest-unavailable', out)
    if 'slip39-dice' in CASES:
        settings.set_value(C.SETTING__SLIP39_SEEDS, C.OPTION__ENABLED, save=False)
        out = {}

        def words(d, cfg):
            out['first_words'] = cfg['words']
            raise Stop()

        steps = [
            (('button_list_screen', 'Tools'), lambda d, cfg: choose_nth(cfg, 'SLIP39 seed', 1)),
            (('button_list_screen', 'Mnemonic Length'), pick('20 words (50 rolls)')),
            (('keyboard_screen', None), lambda d, cfg: dice(50)),
            (('keyboard_screen', 'Num Shares'), lambda d, cfg: digits('3')),
            (('keyboard_screen', 'Threshold'), lambda d, cfg: digits('2')),
            (('large_icon_status_screen', None), lambda d, cfg: pulse(10)),
            (('seed_words_screen', None), words),
        ]

        def choose_nth(cfg, label, nth):
            names = labels(cfg)
            idx = [i for i, n in enumerate(names) if n == label][nth]
            cur = cfg.get('initial_selected_index', 0)
            for _ in range(abs(idx - cur)):
                pulse(18 if idx > cur else 17)
            pulse(10)

        Renderer._instance = None
        driver = Driver(steps)
        Renderer.configure_instance(backend=driver)
        Controller._instance = None
        c = Controller.get_instance()
        d = Destination(ToolsMenuView)
        try:
            for _ in range(40):
                c.back_stack.append(d)
                d = d.run()
                if d.View_cls.__name__ == 'BackStackView':
                    c.back_stack.pop()
                    d = c.back_stack.pop()
            raise AssertionError(('did not finish', driver.seen))
        except Stop:
            pass
        finally:
            c.create_slip39 = False
        seed = c.storage.get_pending_seed()
        import shamir_mnemonic

        sh = seed._shares
        assert len(sh) == 3, len(sh)
        a = shamir_mnemonic.combine_mnemonics([sh[0], sh[1]])
        b = shamir_mnemonic.combine_mnemonics([sh[1], sh[2]])
        assert a == b and len(a) == 16, (a, b)
        try:
            shamir_mnemonic.combine_mnemonics([sh[0]])
            raise AssertionError('one share must not combine')
        except shamir_mnemonic.MnemonicError:
            pass
        assert out['first_words'] == sh[0].split()[:4], out
        c.storage.discard_pending_seed() if hasattr(c.storage, 'discard_pending_seed') else None
        check('slip39-dice-secret', a.hex())
finally:
    settings.set_value(C.SETTING__SLIP39_SEEDS, old_slip, save=False)
print('@@TOOLS_EXTRA_DONE')
