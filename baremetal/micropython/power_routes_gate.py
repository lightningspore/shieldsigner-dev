# SPDX-License-Identifier: MIT
# Original Reset/Power Views through native screens. RESTART=1 ends in a real reset.
import ui, json, machine
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.view_core import PowerOptionsView, PowerOffView


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


class Driver:
    def __init__(self, choose):
        self.choose = choose
        self.seen = []

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        cfg = json.loads(encoded)
        ui.render(builder, encoded)
        self.seen.append((builder, cfg['top_nav']['title']))
        if (
            builder in ('power_options_screen', 'button_list_screen')
            and cfg['top_nav']['title'] == 'Reset / Power'
        ):
            labels = [b if isinstance(b, str) else b.get('label') for b in cfg['button_list']]
            index = labels.index(self.choose)
            for _ in range(index):
                pulse(19 if builder == 'power_options_screen' else 18)
            pulse(10)
        elif builder == 'reset_screen':
            print('@@RESET_SCREEN', cfg['top_nav']['title'])
        elif builder == 'power_off_not_required_screen':
            assert (
                cfg['top_nav']['show_back_button']
                and 'unplug' in cfg['text'].lower()
                or 'disconnect' in cfg['text']
            )
            pulse(20)
            pulse(10)


ui.init()
RESTART = globals().get('RESTART', 0)
Renderer._instance = None
driver = Driver('Power off')
Renderer.configure_instance(backend=driver)
Controller._instance = None
c = Controller.get_instance()
d = PowerOptionsView().run()
print('@@ROUTE', d.View_cls.__name__)
assert d.View_cls.__name__ == 'PowerOffView'
d = PowerOffView().run()
print('@@POWEROFF', driver.seen[-1], d.View_cls.__name__)
assert (
    driver.seen[-1][0] == 'power_off_not_required_screen' and d.View_cls.__name__ == 'BackStackView'
)
print('@@PASS original-power-off-unplug-screen-back')
if RESTART:
    driver.choose = 'Restart'
    d = PowerOptionsView().run()
    assert d.View_cls.__name__ == 'RestartView'
    print('@@RESTARTING')
    d.View_cls().run()
    print('@@FAIL restart returned')
