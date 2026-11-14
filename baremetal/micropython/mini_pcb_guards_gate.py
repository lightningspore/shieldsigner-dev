# SPDX-License-Identifier: MIT
# Block fixture APIs that overlap LCD reset/DC/keys on this app PCB.
import display
import machine
before=display.status()
for action in (lambda:machine.Pin(52,machine.Pin.OUT),lambda:machine.Pin(53,machine.Pin.IN),lambda:machine.SPI(0).write_readinto(b'x',bytearray(1))):
    try:
        action()
        assert False
    except OSError:
        pass
after=display.status()
for name in ('gpio_ddr_low','gpio_ddr_high','mux_b','mux_c','mux_d','spi_mux'):
    assert after[name]==before[name]
print('@@PASS mini-pcb-fixture-apis-rejected')
