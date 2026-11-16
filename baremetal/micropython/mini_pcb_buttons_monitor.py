# SPDX-License-Identifier: MIT
# Physical switch exercise on correct PCB. No substitute wallet navigation.
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.buttons import NAMES
import display
import time

s = ScreenSession()
s.show_screen(
    'MainMenuScreen', {'title': 'Home', 'button_data': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
start = time.ticks_ms()
previous = display.buttons()
seen = 0
print('@@PCB_INPUT_READY', previous)
while ((time.ticks_ms() - start) & 0xFFFFFFFF) < 120000:
    raw = display.buttons()
    if raw != previous:
        print('@@PCB_RAW', raw, tuple(NAMES[n] for n in range(8) if raw & (1 << n)))
        seen |= raw
        previous = raw
    event = s.poll()
    if event is not None:
        print('@@PCB_NATIVE_EVENT', event)
    time.sleep_ms(5)
print('@@PCB_INPUT_SEEN', seen)
print('@@PASS mini-pcb-buttons-monitor-complete')
