# SPDX-License-Identifier: MIT
# After the loader's wait and USB interrupt: real frozen entry, no injected driver.
import ui,camera,machine
from seedsigner_port import boot
from seedsigner_port.controller import Controller
status=machine.console_status()
assert status['usb_only']==status['usb_ready']==1
assert status['uart_pad_mux']==status['uart_ier']==status['uart_irq_enabled']==0
# Native Mini PCB init intentionally drives GPIO43/B3 as LCD backlight.
assert status['uart_gpio_output']==0x800
assert boot.starts==1 and not boot.running
assert boot.last_exit=='KeyboardInterrupt'
assert boot.last_screen=='large_icon_status_screen',boot.last_screen
assert camera.preview_status()==(False,0) and not ui.scan_state()['active']
assert not any(ui.framebuffer())
record=machine.last_reset()
print('@@AUTOBOOT_RESET_BEFORE',record)
# Retained record may describe the host-requested USB reset before this load.
assert record is None or record['reason']==2
machine.clear_reset_record()
assert not machine.fault_probes_enabled()
c=Controller.get_instance()
assert c.storage.num_seeds()==0 and c.storage.get_pending_seed() is None
print('@@PASS frozen-app-autostart-status-screen-usb-interrupt-blank-repl')
