# SPDX-License-Identifier: MIT
from seedsigner_port.buttons import ButtonInput
import time


class Fixture:
    def __init__(self):
        self.mask = 0
        self.now = 0

    def read(self):
        return self.mask

    def clock(self):
        return self.now


f = Fixture()
b = ButtonInput(f.read, f.clock)
f.mask = 1
assert b.poll() is None
f.now = 9
assert b.poll() is None
f.now = 10
assert b.poll() == 'KEY_UP'
f.now = 234
assert b.poll() is None
f.now = 235
assert b.poll() == 'KEY_UP'
f.now = 484
assert b.poll() is None
f.now = 485
assert b.poll() == 'KEY_UP'
print('@@PASS app-buttons-debounce-repeat')
f.mask = 64
b.reset_input()
f.now = 1000
assert b.poll() is None
f.mask = 0
assert b.poll() is None
f.now = 1010
assert b.poll() is None
f.mask = 64
assert b.poll() is None
f.now = 1020
assert b.poll() == 'KEY2'
print('@@PASS app-buttons-held-release')
f.now = 0xFFFFFFF0
f.mask = 0
b.reset_input()
f.now = 0xFFFFFFF8
f.mask = 1
assert b.poll() is None
f.now = 1
assert b.poll() is None
f.now = 2
assert b.poll() == 'KEY_UP'
assert hex((1 << 256) - 1) == '0x' + 'f' * 64
assert 'abcdef'[1:5] == 'bcde'
assert '%02x' % 15 == '0f'
print('@@PASS app-runtime-core-bigints')
import display
import machine
import gc

display.init('mini-pcb240')
physical = ButtonInput()
held = display.buttons()
assert physical.poll() is None
time.sleep_ms(260)
assert physical.poll() is None
print('@@APP_BUTTON_STARTUP_BLOCKED', held)
rejected = 0
for action in [
    lambda: display.init('carrier'),
    lambda: display.fill(65536),
    lambda: display.blit(240, 0, 1, 1, b'xx'),
    lambda: display.blit(0, 0, 2, 2, b'xx'),
    lambda: display.blit(0, 0, 0, 1, b''),
    lambda: display.blit(1073741823, 0, 1, 1, b'xx'),
]:
    try:
        action()
    except ValueError:
        rejected += 1
assert rejected == 6
status = display.status()
assert status['gpio_ddr_low'] == 2048
assert status['gpio_ddr_high'] == 24
assert status['mux_b'] == 0 and status['mux_c'] == 0 and status['mux_d'] == 0
assert status['pull_b'] == 16 and status['pull_c'] == 21504 and status['pull_d'] == 85
assert status['spi_mux'] == 1604
assert machine.console_status()['uart_irq_enabled'] == 0
print('@@PASS app-display-input-guards')
gc.collect()
print('@@PASS app-buttons')
