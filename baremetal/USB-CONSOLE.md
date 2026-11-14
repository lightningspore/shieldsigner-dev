# RV1103 USB debug console

RAM hardware console gates now pass on DUT0 and DUT1; see evidence/phase-11-usb.json. Standalone SD USB boot and the SeedSigner app remain open. The user prioritizes USB
REPL/script transfer so LCD/button pins can be released from UART debug. The
third app target is a Luckfox Pico Mini A (RV1103, no onboard flash), booting
microSD; retain the existing REF/DUT wired fixture during development.

`mise run baremetal:usb:build` builds an experimental `usb-console` runtime.
It inherits app-runtime's fast startup without the GPIO52 timing output.
UART2 remains operational for recovery while this driver is qualified.

Original MIT Rust implementation: `src/usb.rs`. Read-only register/sequence
references are the pinned local Luckfox SDK (0b5c1f30ca6333b7ec5af70d26511da9ef8d39af) kernel and U-Boot sources under
`.tools/kernel-reference`, not code copied into the driver. Facts checked:

- RV1106 device tree (also used by RV1103): DWC3 at ffb00000, SPI54 (GIC86),
  USB2-only high-speed, 16-bit UTMI, PHY ff3e0000, USB GRF ff000000.
- clk-rv1106.c: PERICRU gates4 bits7/8/9 bus/ref/UTMI, gates5 bits1/2 PHY clocks.
  CRU base ff3a0000 + PERICRU12000: ff3b2810/2814 gates, ff3b2a10/2a14 resets.
- phy-rockchip-inno-usb2.c: USB GRF0050 suspend/IDDIG and0058 clock/VBUS control.
- DWC3 core.h/gadget.h: endpoint command fields, TRBs and event format.
- Additional read-only reference: AsahiLinux/m1n1 usb_dwc3.c (GPL), used for
  cross-checking DWC3 control-transfer state/event sequencing only.
  https://github.com/AsahiLinux/m1n1/blob/main/src/usb_dwc3.c
- DWC3 hardware reference listed by that project:
  https://www.ti.com/lit/ug/spruhj7a/spruhj7a.pdf

DMA reservation: 60MiB..60MiB+16KiB inside the existing48..64MiB noncacheable
region. Event ring4KiB, six16-byte TRBs, six1KiB endpoint buffers. It does not
overlap RAW48/52MiB, ISP56MiB or statistics58MiB. No USB IRQ is enabled; a
bounded foreground poll runs during REPL, VM branches, output, and MicroPython delays.
Ctrl-C schedules MicroPython KeyboardInterrupt at VM branches; Ctrl-] requests a warm reset. Long native camera/3A operations do not yet service USB and require verification.

Enumeration exposes a development CDC ACM console (VID1209/PID0003, development
use only, no allocation/production identity claim). Endpoint81 interrupt,
02 OUT/82 IN bulk512. Only high-speed operation currently accepted.
UART evidence includes core identity, reset/connect and bounded setup traces.

`mise run baremetal:usb:console -- path/to/script.py` selects one matching CDC device (or an explicit --port), uploads in paste mode and saves the response with a random completion nonce. It never writes a storage device.

Remaining gates: real enumeration, native macOS serial binding, REPL/script
transfer, lossless bounded output/backpressure, reset/disconnect/reconnect,
peripheral/camera/GC regression, then SD packaging and standalone USB boot.
Do not remove UART wires until the USB tests pass. No ADB shell/filesystem is
implemented or promised. Smartcard software is excluded from the app scope.

Control-transfer review: the driver's actual phase transitions live in
`src/usb_control.rs`; five host tests exercise IN/OUT data, two/three-stage
status, incorrect direction and duplicate-not-ready rejection. These tests
complement the descriptor checks and do not prove hardware enumeration.

Hardware qualification: native macOS CDC, script upload,46593 exact output bytes
(up to32768 per block), full peripheral/two-camera/GC gate, Ctrl-C from a running
loop and3 port reopens passed on DUT0. DUT1's distinct rv1103-dut1 identity,
USB-only UART-pad release readbacks,3 reopens/Ctrl-C and USB warm reset to maskrom
passed. USB-only releases pads at Rust entry; unchanged DDR still prints earlier.
Initial IN stall was fixed by configuring bulk/interrupt endpoints at host
SET_CONFIGURATION rather than before the initial bus reset.

For DUT1, build with `mise run baremetal:usb:dut1:build`, then (when in maskrom)
`mise run baremetal:usb:dut1:ram:gate`. Both USB devices can coexist; pass
`--port /dev/cu.usbmodemrv1103_dut11` to the uploader/debug gate for DUT1.
The USB debug gate's `--reset-to-maskrom 101` proves USB Ctrl-] recovery.
Host loader location selection is documented in patches/README.md.
