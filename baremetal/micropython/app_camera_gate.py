# SPDX-License-Identifier: MIT
# Local DUT1 capture→native RGB565→SPI pipeline. Optical output is a separate gate.
import camera
import display
import machine
import time
import gc
assert machine.console_status()['usb_only']==1
display.init('mini-pcb240')
initial=display.status()
camera.init()
baseline=camera.settings()['rust_heap_bytes']
for number in range(2):
    frame=camera.capture()
    assert len(frame)==460800
    try:
        frame[0]=0
        assert False
    except TypeError:
        pass
    after=display.status()
    for name in ('mux_b','mux_c','mux_d','gpio_ddr_low','gpio_ddr_high','spi_mux','spi_divisor'):
        assert after[name]==initial[name]
    start=time.ticks_ms()
    display.blit_nv12(frame)
    elapsed=time.ticks_ms()-start
    assert camera.settings()['rust_heap_bytes']==baseline
    print('@@APP_CAMERA_NATIVE_BLIT',number,elapsed,camera.timings())
    gc.collect()
try:
    display.blit_nv12(b'bad')
    assert False
except ValueError:
    pass
print('@@APP_CAMERA_BUTTON_MASK',display.buttons())
print('@@PASS app-camera-native-blit')
