# Prototype bring-up guide

> For the **eight-pin pill**, start with [modular assembly and first power](MODULAR-ASSEMBLY.md). The FPC connector, Q401 and R401–R410 below apply only to the standard FPC carrier and are absent from the pill. Shared Luckfox/SEC1210/card tests remain useful after completing the pill-specific rail and fit checks.

For the native KiCad ShieldSigner Luckfox carrier. This is a **proposed test procedure**, not a record of hardware passing. Use the [electrical review](ELECTRICAL-REVIEW.md) and [component pad maps](COMPONENTS.md) alongside it. Clear the layout/assembly review items before ordering; passing a prototype does not excuse unresolved manufacturing DRC.

Use a spare/test card and test data throughout. Production keys, PIN attempts, applet installation and card resets are not needed to prove the first electrical stages.

## Record the build before power

Copy [BRINGUP-RESULTS.md](BRINGUP-RESULTS.md) for each physical prototype. Record board revision, assembly supplier/order, fitted MPNs, module Mini A/B and storage variant, firmware image/hash, reader driver/configuration, instruments and supply limit. Record values and evidence, not only “works”.

Required equipment: magnification, a DMM, regulated/current-limited 5 V supply or equivalent protected bench arrangement, and a known-good compatible card. An oscilloscope/logic analyzer is needed for reset, rail transients and reader/display timing; a DMM alone cannot pass those tests. Avoid slipping probe tips across fine-pitch pins: use accessible capacitor/resistor pads and attach ground with power off.

## Stage 1 — Assembly inspection, unpowered

Check these first:

- R404, R408 and J302 are unpopulated. R403 and R409 are fitted. C603/C604 are 1 µF, not the original 100 nF.
- JP201, JP203 and JP205 are closed by their intended copper bridges; JP202, JP204 and JP206 remain open. Check actual continuity, not only silkscreen labels.
- U601 is the selected SEC1210/PV-UR2; Q401 is AO3400A; J401 is the top-contact Amphenol C2931360. Do not accept the bottom-contact C19273935 as an automatic alternative.
- Inspect U601 orientation/exposed pad, USB-C shell soldering, FPC contacts/mounting plates and card-socket contacts. Review the XKB switch actuator/stencil geometry.
- Inspect +5V-to-GND and +3.3V-to-GND for unexpected shorts. Allow capacitor charging to settle. There is no universal resistance threshold for a populated module; distinguish a sustained near-short from charging/semiconductor paths.
- With power off, verify the default CS path from U202 pad 6 through JP203/JP205 to J401 pad 9. Verify the backlight default path from +3.3V through JP201/R401 toward Q401 gate.
- Check that the display housing cannot touch supply/header pins. Fit insulation where the upstream assembly calls for it.

**Stop** for a sustained supply short, opposite straps both fitted, incorrect connector contact type or an unexplained assembly substitution. Do not power through it to see what happens.

## Stage 2 — Assembled carrier without host, LCD or card

This stage is useful when JLCPCB assembles the carrier but leaves U202 off. Disconnect all independent USB/power sources. Connect one regulated **5.00 V** supply to the intended power input with correct polarity.

A **100 mA current limit is a provisional fault-screening setting for the module-less carrier**, not a validated operating limit or acceptance current. Input capacitors can briefly cause current limiting. If the supply remains limited, power down and investigate; do not increase it blindly. No measured normal-current envelope exists yet.

| Measurement | Accessible probe | Expected / interpretation |
|---|---|---|
| +5V | C602 pad 1; ground C602 pad 2 | Near setpoint; record actual minimum/maximum |
| Power LED | D302 | Normally lit when +5V is present; polarity and R303 still matter |
| Bridge reset | C601 pad 1 to GND | Starts low, then releases toward +5V; capture the waveform |
| Bridge VDD33 | C603 pad 1 to GND | Approximately 3.3 V after bridge reset release; separate from carrier rail |
| Carrier +3.3V | U202 pad 3 or C401 pad 2 | **Not supplied without Luckfox. Absence is expected.** |
| Card VCC | C604 pad 1 to GND | May be off while inactive; no host/card activation command exists yet |

Record idle input current after settling. Compare it with the fitted bridge/indicator loads and investigate heat or excessive current. A reader bridge can be powered here, but the LCD, buttons and signer application cannot function without the host. Do not feed an external 3.3 V into the module-output node as an improvised substitute.

## Stage 3 — Host supply and boot

Power off, install the exact compatible Luckfox module using the reviewed orientation/attachment method, and inspect insulation/clearance again. Use an image for that module and its SD/NAND storage. Verify the image using the fork's release procedure; do not fuse secure boot or provision permanent keys during bring-up.

With no LCD/card load yet, choose a supply current limit based on the module's documented requirements and the intended loads. **No qualified host boot/peak-current limit has been established here.** An inadequate limit can cause brownout/reboot loops that resemble firmware failure. Record the configured limit and actual current/rail behavior.

Measure carrier +3.3V now. As an initial engineering screening target, use nominal 3.3 V ±5%, then check the actual module/LCD specifications before accepting that tolerance as a requirement. Observe transient minima during boot; a stable DMM reading cannot rule out short droops.

Use one supply source. Do not connect the module's USB power and carrier USB power to independent sources without verified isolation. If boot fails, first check supply integrity, module storage/image pairing and mounting; do not change the reader circuitry to compensate.

## Stage 4 — LCD logic and backlight

Power off before connecting the LCD cable. Confirm its contact face and pin numbering from the exact panel drawing. The upstream orientation notes conflict, so do not infer orientation from the connector's similar appearance.

On power-up:

1. Check LCD +3.3V at C401 pad 2 / J401 pads 6 and 7.
2. Check Q401 gate, source and drain. In the default configuration gate should be near 3.3 V, source at ground, and drain low while light is enabled.
3. Measure the differential voltage across each R405/R406/R407. Calculate **Ibranch = Vresistor / 47 Ω** and compare each branch with the panel rating. Record all three separately.
4. Confirm LCD reset transitions and SPI clock/MOSI/DC/CS activity during initialization. Display reset is on a module pin also named SPI MISO in the bundled symbol; firmware must use it as GPIO reset.
5. Exercise screen updates while monitoring rail droop and current. Check pixels, colors, rotation, readable text and persistent artifacts.

Light without pixels suggests a logic/reset/mode/SPI problem. Pixels without light suggests the backlight branch. Neither symptom alone proves the other block is healthy. The 47 Ω branches are not constant-current regulation, and a generic ST7789 designation does not provide the panel's LED limits.

## Stage 5 — Eight button inputs and camera

Verify every button separately. With firmware pull-ups enabled, each input should be high when released and close to ground when pressed. Record actual voltages/observed events. There are no external pull-up resistors in this button block.

| Switch | Function |
|---|---|
| SW501 | Left |
| SW502 | Up |
| SW503 | Press / select |
| SW504 | Down |
| SW505 | Right |
| SW506 | Key1 |
| SW507 | Key2 |
| SW508 | Key3 |

Confirm no adjacent key activates, held presses behave correctly, and bouncing is handled by the UI. Check actuator alignment with the intended case, not only with the bare PCB. A stuck/floating key can result from pinmux, input-buffer or pull configuration.

Attach the compatible low-profile camera directly to the module with power off. Test live capture and a harmless QR. Record display/camera peak current and +3.3V minima together; their combined load matters. The carrier intentionally has no routed camera connector.

## Stage 6 — Reader configuration before inserting a card

See the [complete smartcard reader guide](SMARTCARDS.md) for the exact J601 socket/contact map, Linux stack, card compatibility and diagnostic steps.

The selected C633309 part is **UR2**. The pinned OS configuration currently says URT. The reviewed target configuration for the UR2 part is:

```text
DEVICENAME        /dev/ttyS2:SEC1210UR2
FRIENDLYNAME      "SEC1210"
LIBPATH           /usr/lib/pcsc/drivers/serial/libccidtwin.so
```

Only the first hardware card channel is connected. A second PC/SC slot appearing empty can be normal for UR2. Confirm which enumerated slot corresponds to SC1 rather than assuming every listed slot has a socket.

Source evidence: [pinned Luckfox reader file](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/files/sec1210), [CCID 1.7.1 variant handling](https://github.com/LudovicRousseau/CCID/blob/1.7.1/src/ccid_serial.c). This target configuration has **not** been hardware tested here. Preserve the shipped configuration before intentionally changing a bench image, and restart only its reader service as appropriate to that image.

If using a development image with a local shell, read the installed `/etc/reader.conf.d/sec1210` configuration and confirm `/dev/ttyS2` exists. Where installed, `pcsc_scan` can show reader and insertion/removal state. A production image may not expose a shell or include that utility; use its smartcard tools instead. Do not install a generic Raspberry Pi package recipe onto a Luckfox Buildroot image by assumption.

Ensure no serial console or other process owns the same UART. The CCID driver initially tries 9600 baud then negotiates 115200; captures can show both. Verify U202 TX reaches U601 RXD through R602 and U601 TXD reaches U202 RX through R603.

## Stage 7 — Card detection, power, ATR and applet

Start with a known-good **contact-capable** retail SeedKeeper or Satochip and test data. This board has no NFC reader. A card that only offers contactless access is not a contact-reader test fixture.

Test in this order:

1. Insert/remove card and observe the J601 COM/NO presence switch and reader state. Record the physically connected slot.
2. Activate the card via the reader. Check switched supply at C604; do not externally force voltage onto J601 contacts. The selected voltage class depends on card/driver negotiation.
3. Capture/record ATR reception. An ATR demonstrates transport-level response, not support for the desired applet.
4. Use Card Info / applet information in the fork to identify the application/version before initializing anything.
5. Only after these pass, perform a reversible test operation on a spare initialized card. For SeedKeeper, save/load a harmless test secret; for Satochip, verify a test xpub/signing flow with test keys and a reviewed test transaction.

Do not repeatedly guess a PIN. Do not flash, factory-reset, change GlobalPlatform keys or unseal a bearer card just to diagnose “reader not detected”. These operations change persistent card state and can destroy the test fixture's data. Refer to the separate smartcard guide for deliberate provisioning.

Measure supply/rail behavior during activation and communication. An inactive card supply near zero is not inherently a fault. Card clock/reset/I/O operate in the selected card voltage domain and need appropriate probes.

## Stage 8 — Repetition and acceptance evidence

Record at least repeated cold boots, warm restarts, short power interruptions, card insertion/removal and a combined display/camera/card workload. Record the number of trials and failures; the exact production qualification sample size and environmental limits remain to be specified.

A prototype passes this proposed bring-up only after expected functions and measured limits are documented. It does not constitute environmental, ESD, EMC or production-lifetime qualification. Clear unresolved layout/assembly findings before a production release.

## Fault isolation

| Symptom | First checks |
|---|---|
| No +5V on a C-to-C supply | Cable/source, CC resistors, connector soldering, sustained input short |
| +5V exists but no carrier +3.3V | Host present? Module supply/output and mounting; no host means no carrier rail |
| Reboot loops / unstable screen | Supply current limit, cable drop and oscilloscope rail minima; then image pairing |
| Backlight only | Panel pinout, mode straps, reset and SPI signals |
| No backlight | JP201 path, Q401 gate/source/drain, LED resistor branches and panel cable |
| Buttons float / wrong button | Firmware input pulls/buffers, pinmux, mapping, soldering and actuator alignment |
| Reader missing | U601 supply/reset, UR2 configuration, UART ownership/levels and driver startup |
| Reader exists, card absent | Connected slot, COM/NO detect switch, insertion and contact alignment |
| Card detected, no ATR | Card voltage/class, clock/reset/I/O, contact condition, known-good card comparison |
| ATR exists, applet unavailable | Card/application identity, support settings and firmware version; separate from PCB transport |
