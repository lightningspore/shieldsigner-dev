# SPDX-License-Identifier: MIT
# PUBLIC fixture: original Tools > Calc final word through native screens.
# Oracle (embit, host): 11x"abandon" + zeros -> "about"; + flips 1111111 -> "wrap".
import ui, json, gc, machine
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.navigation import Destination
from seedsigner_port.camera_entropy_views import ToolsMenuView, ToolsCalcFinalWordFinalizePromptView


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def choose(cfg, label):
    labels = [b if isinstance(b, str) else b.get('label') for b in cfg['button_list']]
    for _ in range(labels.index(label)):
        pulse(18)
    pulse(10)


class Stop(Exception):
    pass


class Driver:
    def __init__(self, mode, expected):
        self.mode = mode
        self.expected = expected
        self.seen = []

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        title = cfg.get('top_nav', {}).get('title')
        self.seen.append((builder, title))
        if builder == 'button_list_screen' and title == 'Tools':
            choose(cfg, 'Calc 12th/24th word')
        elif builder == 'button_list_screen' and title == 'Build Final Word':
            choose(cfg, 'Finalize with zeros' if self.mode == 'zeros' else 'Coin flip entropy')
        elif builder == 'keyboard_screen':
            assert cfg['keys'] == ['1', '0'] and cfg['return_after_n_chars'] == 7
            for _ in range(7):
                pulse(10)
        elif builder == 'tools_calc_final_word_screen':
            assert cfg['final_word_text'] == 'Final Word: "%s"' % self.expected, cfg[
                'final_word_text'
            ]
            pulse(10)
        elif builder == 'tools_calc_final_word_done_screen':
            assert cfg['final_word'] == self.expected and cfg['top_nav']['title'] == '12th Word'
            choose(cfg, 'Load seed')
        elif builder == 'seed_finalize_screen':
            self.fingerprint = cfg['fingerprint']
            raise Stop()
        else:
            raise AssertionError(('Unexpected screen', builder, title))


ui.init()
for mode, expected in (('zeros', 'about'), ('flips', 'wrap')):
    Renderer._instance = None
    driver = Driver(mode, expected)
    Renderer.configure_instance(backend=driver)
    Controller._instance = None
    c = Controller.get_instance()
    c.storage.init_pending_mnemonic(12)
    for i in range(11):
        c.storage.update_pending_mnemonic('abandon', i)
    d = Destination(ToolsCalcFinalWordFinalizePromptView)
    try:
        for _ in range(10):
            d = d.run()
        raise AssertionError('flow did not reach finalize')
    except Stop:
        pass
    seed = c.storage.get_pending_seed()
    assert seed.mnemonic_list == ['abandon'] * 11 + [expected], seed.mnemonic_list
    c.storage.clear_pending_seed()
    gc.collect()
    print(
        '@@PASS original-calc-final-word',
        mode,
        expected,
        driver.fingerprint,
        [s[0] for s in driver.seen],
    )
# Tools menu exposes the restored entry.
Renderer._instance = None
driver = Driver('zeros', 'about')
Renderer.configure_instance(backend=driver)
Controller._instance = None
c = Controller.get_instance()
d = ToolsMenuView().run()
print('@@TOOLS_ROUTE', d.View_cls.__name__)
assert d.View_cls.__name__ == 'ToolsCalcFinalWordNumWordsView'
print('@@PASS tools-menu-calc-final-word-route')
