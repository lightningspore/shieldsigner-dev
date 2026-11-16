# SPDX-License-Identifier: MIT
# Repeated real screen rebuilds and exception cleanup must return C heap to baseline.
import ui
import gc

ui.init()
config = '{"top_nav":{"title":"Home"},"button_list":["Scan","Seeds","Tools","Settings"]}'
ui.render('main_menu_screen', config)
baseline = ui.status()['heap_bytes']
for n in range(20):
    try:
        ui.render('main_menu_screen', '{broken')
        assert False
    except RuntimeError:
        pass
    ui.render('main_menu_screen', config)
    gc.collect()
    assert ui.status()['heap_bytes'] == baseline
print('@@UI_STRESS', ui.status())
print('@@PASS ui-stress-no-leak')
