# SPDX-License-Identifier: MIT
# Frozen cooperative UI adapter, real native renderer and local camera coexistence.
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.buttons import ButtonInput
import ui
import display
import machine
import camera
import gc
assert machine.console_status()['usb_only']==1
config={'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']}
physical=ScreenSession()
physical.show('main_menu_screen',config)
assert physical.wait(300) is None
print('@@APP_UI_HELD_MASK',display.buttons())
class Input:
    now=0
    mask=0
f=Input()
b=ButtonInput(lambda:f.mask,lambda:f.now)
s=ScreenSession(buttons=b,clock=lambda:f.now,sleep=lambda ms:None)
s.show('main_menu_screen',config)
f.mask=8
assert s.poll() is None
f.now=10
assert s.poll() is None
f.mask=0
f.now=20
s.poll()
f.now=30
s.poll()
f.mask=16
f.now=40
assert s.poll() is None
f.now=50
selected=s.poll()
assert selected==(1,1,'')
print('@@APP_UI_FROZEN_EVENT',selected)
s.show('main_menu_screen',config)
assert s.poll() is None
camera.init()
initial=display.status()
baseline=ui.status()['heap_bytes']
frame=camera.capture()
display.blit_nv12(frame)
assert ui.status()['heap_bytes']==baseline
for field in ('gpio_ddr_low','gpio_ddr_high','mux_b','mux_c','mux_d','spi_mux','spi_divisor'):
    assert display.status()[field]==initial[field]
# Restore the genuine Home through the same backend, without LCD reinit.
s.show('main_menu_screen',config)
gc.collect()
assert ui.status()['heap_bytes']==baseline
pins=machine.console_status()
assert pins['uart_pad_mux']==0 and pins['uart_gpio_output']==2048
assert pins['uart_ier']==0 and pins['uart_irq_enabled']==0
print('@@APP_UI_CAMERA_RESTORE',ui.status(),pins)
print('@@PASS app-ui-frozen-camera')
