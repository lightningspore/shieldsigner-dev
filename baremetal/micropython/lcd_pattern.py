# SPDX-License-Identifier: MIT
# Hardware diagnostic for the user-confirmed existing Linux bench board only.
import display
import machine
import time
assert machine.console_status()['usb_only'] == 1
start=time.ticks_ms()
display.init('bench240')
display.fill(0)
for x,y,color in [(0,0,0xf800),(120,0,0x07e0),(0,120,0x001f),(120,120,0xffff)]:
    pixels=bytes([color>>8,color&255])*14400
    display.blit(x,y,120,120,pixels)
# Contrasting border around each quadrant makes crop/geometry visible.
black=bytes([0,0])*240
for y in [0,119,120,239]:
    display.blit(0,y,240,1,black)
print('@@LCD_PATTERN_READY',time.ticks_ms()-start,'ms')
print('@@BENCH_BUTTON_MASK',display.buttons())
print('@@PASS lcd-spi-pattern-written')
