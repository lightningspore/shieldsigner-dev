# SPDX-License-Identifier: MIT
# PUBLIC seed (abandon x11 about). Original Tools > Address explorer on native
# screens; QR pixels decoded. Oracle: embit m/84'/0'/0'.
import ui, json, qr, gc
from seedsigner_port.seed import Seed
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.navigation import Destination
from seedsigner_port.camera_entropy_views import ToolsMenuView

RECV = ['bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu', 'bc1qnjg0jd8228aq7egyzacy8cys3knf9xvrerkf9g']
RECV10 = 'bc1qd30z5a5e50jtgx28rvt64483tq65r9pkj623wh'
CHANGE0 = 'bc1q8c6fshw2dlwun7ekn9qwf37cu2rn755upcp6el'


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def labels(cfg):
    return [b if isinstance(b, str) else b.get('label') for b in cfg.get('button_list', [])]


def choose(cfg, label):
    for _ in range(labels(cfg).index(label)):
        pulse(18)
    pulse(10)


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
    def __init__(self, change):
        self.change = change
        self.seen = []
        self.pages = 0
        self.qr = None

    waiting = False

    def __getattr__(self, name):
        return getattr(ui, name)

    def tick(self):
        result = ui.tick()
        if self.waiting and not ui.qr_tip_active():
            self.waiting = False
            self.qr = decoded_frame()
            assert self.qr == RECV10.encode(), self.qr
            pulse(20)
        return result

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        title = cfg.get('top_nav', {}).get('title')
        self.seen.append((builder, title))
        if builder == 'loading_spinner_screen':
            return
        if title == 'Tools':
            choose(cfg, 'Address explorer')
        elif builder == 'button_list_screen' and title == 'Address Explorer':
            pulse(10)  # first item: loaded seed
        elif builder == 'button_list_screen' and 'Segwit' in ''.join(labels(cfg)):
            choose(cfg, 'Native Segwit')
        elif builder == 'tools_address_explorer_address_type_screen':
            assert cfg['fingerprint'] == '73c5da0a', cfg
            choose(cfg, 'Change addresses' if self.change else 'Receive addresses')
        elif builder == 'tools_address_explorer_address_list_screen':
            self.pages += 1
            a = cfg['addresses']
            if self.change:
                assert a[0] == CHANGE0, a[0]
                raise Stop()
            if self.pages == 1:
                assert a[:2] == RECV and cfg['start_index'] == 0, (a[:2], cfg['start_index'])
                choose(cfg, cfg['next_label'])
            elif self.pages == 2:
                assert cfg['start_index'] == len(a) and a[0] == RECV10, (cfg['start_index'], a[0])
                pulse(10)
            else:
                raise Stop()
        elif builder == 'qr_display_screen':
            # Original brightness tip overlays the QR and auto-hides; decode after it clears.
            assert bytes.fromhex(cfg['qr_data']) == RECV10.encode()
            self.waiting = True
        else:
            raise AssertionError(('Unexpected screen', builder, title))


ui.init()
for change in (False, True):
    Renderer._instance = None
    driver = Driver(change)
    Renderer.configure_instance(backend=driver)
    Controller._instance = None
    c = Controller.get_instance()
    seed = Seed(['abandon'] * 11 + ['about'])
    c.storage.set_pending_seed(seed)
    c.storage.finalize_pending_seed()
    d = Destination(ToolsMenuView)
    try:
        for _ in range(20):
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
    gc.collect()
    print(
        '@@PASS original-address-explorer',
        'change' if change else 'receive',
        driver.pages,
        driver.qr,
        [s[0] for s in driver.seen],
    )
