# SPDX-License-Identifier: MIT
# Exercise genuine list/grid navigation; displayed labels are public test fixtures.
import ui
import json
import machine
import gc

assert machine.console_status()['usb_only'] == 0
ui.init()
registry = ui.screens()
assert isinstance(registry, tuple) and len(registry) == 43
assert tuple(sorted(registry)) == registry
for name in (
    'button_list_screen',
    'main_menu_screen',
    'power_options_screen',
    'keyboard_screen',
    'qr_display_screen',
):
    assert name in registry
print('@@UI_REGISTRY', len(registry), registry)
home = {'top_nav': {'title': 'Home'}, 'button_list': ['Scan', 'Seeds', 'Tools', 'Settings']}
listing = {
    'top_nav': {'title': 'Navigation test', 'show_back_button': True},
    'button_list': ['First', 'Second', 'Third'],
}
power = {
    'top_nav': {'title': 'Grid test', 'show_back_button': True},
    'button_list': ['First', 'Second'],
}


def render(name, config):
    ui.render(name, json.dumps(config))


def key(value):
    ui.key(value, True)
    ui.key(value, False)


render('main_menu_screen', home)
cold_baseline = ui.status()['heap_bytes']
# Native fonts memoize glyphs. Warm every tested text/focus path once, then
# require an unchanged absolute baseline across five complete later cycles.
for number in range(6):
    render('button_list_screen', listing)
    key(18)
    key(10)
    assert ui.event() == (1, 1, '')
    render('button_list_screen', listing)
    key(17)
    key(10)
    back = ui.event()
    assert back is not None and back[0] == 1 and back[1] == 1000
    render('power_options_screen', power)
    key(19)
    key(10)
    assert ui.event() == (1, 1, '')
    render('main_menu_screen', home)
    gc.collect()
    if number == 0:
        baseline = ui.status()['heap_bytes']
        print('@@UI_REGISTRY_WARMUP', cold_baseline, baseline)
    else:
        assert ui.status()['heap_bytes'] == baseline
print('@@UI_REGISTRY_NATIVE_HEAP', baseline, ui.status())
try:
    render('power_options_screen', {'top_nav': {'title': 'Invalid'}, 'button_list': ['One']})
    assert False
except RuntimeError:
    pass
render('main_menu_screen', home)
assert ui.status()['heap_bytes'] == baseline
print('@@PASS native-registry-list-grid-back')
