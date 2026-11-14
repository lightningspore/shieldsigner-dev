# SPDX-License-Identifier: MIT
# Actual locked main-menu screen on the native LVGL runtime; no wallet substitute.
import ui
import time
import gc
start=time.ticks_ms()
ui.init()
print('@@UI_INIT_MS',(time.ticks_ms()-start)&0xffffffff,ui.status())
for config in ('{broken','{}'):
    try:
        ui.render('main_menu_screen',config)
        assert False
    except RuntimeError as error:
        print('@@UI_EXPECTED_EXCEPTION',str(error))
try:
    ui.render('not_a_screen','{}')
    assert False
except RuntimeError:
    pass
config='{"top_nav":{"title":"Home"},"button_list":["Scan","Seeds","Tools","Settings"]}'
start=time.ticks_ms()
ui.render('main_menu_screen',config)
print('@@UI_RENDER_MS',(time.ticks_ms()-start)&0xffffffff,ui.status())
frame=ui.framebuffer()
assert len(frame)==115200
try:
    frame[0]=0
    assert False
except TypeError:
    pass
assert any(frame)
# LVGL hardware keypad contract: center=ENTER; right selects the second tile.
ui.key(10,True)
ui.key(10,False)
first=ui.event()
print('@@UI_FIRST_EVENT',first)
assert first is not None and first[0]==1 and first[1]==0
ui.render('main_menu_screen',config)
ui.key(19,True)
ui.key(19,False)
ui.key(10,True)
ui.key(10,False)
second=ui.event()
print('@@UI_SECOND_EVENT',second)
assert second is not None and second[0]==1 and second[1]==1
for n in range(3):
    ui.render('main_menu_screen',config)
    ui.tick()
    gc.collect()
print('@@UI_FINAL',ui.status())
print('@@UI_RGB565_BEGIN 240 240')
digits='0123456789abcdef'
for y in range(240):
    row=''
    for x in range(480):
        value=frame[y*480+x]
        row+=digits[value>>4]+digits[value&15]
    print('@@UI_ROW',row)
print('@@UI_RGB565_END')
print('@@PASS native-ui-main-menu')
