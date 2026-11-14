# SPDX-License-Identifier: MIT
# Real local sensor capture -> native conversion -> physical PCB LCD, static frame.
import camera
import display
import machine
import ui
camera.init()
before=display.status()
baseline=ui.status()['heap_bytes']
frame=camera.capture()
assert len(frame)==460800
display.blit_nv12(frame)
after=display.status()
for key in ('gpio_ddr_high','gpio_ddr_low','mux_b','mux_c','mux_d','spi_mux','spi_divisor'):
    assert before[key]==after[key]
assert ui.status()['heap_bytes']==baseline
assert machine.console_status()['uart_gpio_output']==2048
print('@@MINI_PCB_CAMERA',camera.timings(),baseline)
print('@@PASS mini-pcb-camera-static-submitted')
