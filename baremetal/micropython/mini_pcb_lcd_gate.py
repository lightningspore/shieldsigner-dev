# SPDX-License-Identifier: MIT
# Exact user-provided Mini PCB. Old DC56/RST57 are joystick inputs here.
import display
import machine
try:
    display.init('bench240')
    assert False
except OSError:
    pass
display.init('mini-pcb240')
display.fill(0xffff)
status=display.status()
pins=machine.console_status()
assert status['gpio_ddr_high']==24  # C3 reset + C4 DC; all button pins input
assert status['gpio_ddr_low']==2048 # B3 backlight; B2 unused input
assert pins['uart_pad_mux']==0 and pins['uart_ier']==0 and pins['uart_irq_enabled']==0
assert pins['uart_gpio_output']==2048
print('@@MINI_PCB_LCD_WHITE',status,pins,display.buttons())
print('@@PASS mini-pcb-lcd-white-submitted')
