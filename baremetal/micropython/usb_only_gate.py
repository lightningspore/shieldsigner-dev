# SPDX-License-Identifier: MIT
import machine

status = machine.console_status()
assert status['usb_only'] == 1
assert status['usb_ready'] == 1
assert status['uart_pad_mux'] == 0
assert status['uart_gpio_output'] == 0
assert status['uart_ier'] == 0
assert status['uart_irq_enabled'] == 0
print('@@USB_ONLY_STATUS', status)
print('@@PASS usb-only-pins-released')
