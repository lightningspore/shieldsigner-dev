# SPDX-License-Identifier: MIT
# Genuine native Home rendering on the exact Mini PCB, not full app startup.
from seedsigner_port.native_ui import ScreenSession
import display
import machine

s = ScreenSession()
s.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
assert display.buttons() == 0
pins = machine.console_status()
assert pins['uart_gpio_output'] == 2048 and pins['uart_pad_mux'] == 0
assert pins['uart_ier'] == 0 and pins['uart_irq_enabled'] == 0
print('@@MINI_PCB_HOME', display.status(), pins)
print('@@PASS mini-pcb-native-home-submitted')
