# Electrical review — ShieldSigner Luckfox Plus

Reviewed 2026-10-11 against the native KiCad working project, pinned upstream sources, supplier drawings and controller datasheets. This is a **desk review**: no physical board, load measurement, oscilloscope capture or card transaction has been tested in this session.

The circuit is plausible, but it is not ready for manufacturing approval. The main unresolved questions concern the LCD connector/assembly, backlight load, supply protection and reader configuration. Native ERC currently has zero errors; PCB connectivity/parity checks also pass. Current native layout checks have zero active DRC errors/warnings, with two documented DNP courtyard exclusions; see [KICAD.md](../KICAD.md). This does not close the electrical bench items below. The [separate modular variant](LCD-MODULE-VARIANT.md) has its own reviewed lands, display power path and checks.

## Decisions and findings

| ID | Circuit | Result | Required next action |
|---|---|---|---|
| ER-01 | SEC1210 output capacitors | Nominal values corrected to 1 µF | Qualify effective capacitance and placement at the operating voltage |
| ER-02 | LCD connector selection | Incorrect inherited supplier ID corrected | Confirm the actual LCD cable orientation; review mounting-plate mask/paste |
| ER-03 | Backlight switch | AO3400A identity and logic-level suitability checked | Measure LED-branch currents and verify module 3.3 V load headroom |
| ER-04 | SEC1210 reset | Earlier edge-timing concern resolved by reading table columns | Retain RC; test startup and brownout behavior on hardware |
| ER-05 | UART reader | Selected part is UR2; stock firmware configuration names URT | Match the reader configuration to UR2 and exercise the connected slot |
| ER-06 | USB-C / 5 V supply | Basic sink topology is consistent | Verify power/current budget; do not treat the TVS as overvoltage shutdown |
| ER-07 | Buttons | Active-low topology is consistent | Verify firmware pulls/debounce and qualify the actual stocked switch footprint |
| ER-08 | Smartcard contacts | Main contact-channel wiring is consistent | Confirm card voltage/class, C6 use, presence detection and activation sequence |
| ER-09 | Module mounting and power inputs | No isolation between shared input paths is established | Use one power source; verify module variant and insulation under LCD |

“Checked” means supported by the identified source or native netlist. It does not mean measured, qualified for all substitutions, or approved for production.

## ER-01 — SEC1210 supply nodes and decoupling

There are three different supply roles around U601:

- `+5V` feeds VDD5, pin 3, with C602 nearby.
- `SEC1210_VDD33`, pin 18, is the bridge regulator output. It is separate from the Luckfox-generated carrier `+3.3V` rail.
- `SEC1210_SC_VCC`, pin 9, is the switched card supply. It goes to J601 C1 and, in this source design, C6.

The native variant changes **C603 and C604 from 100 nF to 1 µF**. This follows the external-capacitor requirements in [Microchip DS00001561D](https://www.microchip.com/content/dam/mchp/documents/UNG/ProductDocuments/DataSheets/00001561D.pdf), table 6-4 notes 6-2/6-3. This correction is already in both the schematic and PCB, with footprints unchanged.

The selected C28323 is Samsung **CL21B105KBFNNNE**, nominal 1 µF, 50 V, X7R, ±10%, 0805. This is a sensible nominal candidate; vendor DC-bias/temperature data or a measurement must establish its effective capacitance. The reference C602 uses the same selection. [Supplier specification](https://www.lcsc.com/product-detail/C28323.html).

Keep the internal bridge output and the module output separate. Joining them because both are called “3.3 V” would parallel independently generated rails. When there is no host installed, the carrier +3.3 V rail is not supplied; that does not imply U601's own VDD33 output should be absent after reset releases.

## ER-02 — LCD connector, mode and assembly

The PCB value specifies Amphenol **62684-402100ALF**, a top-contact connector. The inherited supplier code C19273935 actually identifies **HC-FPC-0.5-40P-FH20**, a bottom-contact Hong Cheng connector. They must not be treated as interchangeable solely because both have 40 contacts at 0.5 mm pitch. The native BOM now uses **C2931360**, the intended Amphenol part. [Amphenol specification](https://www.amphenol-cs.com/product/62684402100alf.html), [correct supplier identity](https://www.lcsc.com/product-detail/C2931360.html), [rejected substitute](https://jlcpcb.com/partdetail/HC-FPC-0.5-40P-FH20/C19273935).

The source PCB maps J401 pads 9/10/11/13/15 to CS/clock/DC/MOSI/reset. R403 fitted and R409 fitted, with R404/R408 absent, set IM1 high and IM0 low; IM2 is already high. This matches the upstream four-line SPI configuration. The two opposing strap resistors in a pair must never both be populated.

Two issues remain before approving this assembly:

1. **Cable orientation:** the upstream README and screen-sheet note disagree about whether the LCD pinout is reversed. Confirm the exact LCD drawing, cable contact face and pin-1 orientation by tracing actual pad assignments. The correct connector identity does not settle the cable question.
2. **Mounting plates:** the placed footprint's S1/S2 custom pads list `B.Cu` without `B.Mask` or `B.Paste`. The manufacturer drawing identifies metallic mounting plates. Determine whether these pads are intended solder lands and compare the exposed-mask/stencil pattern to the recommended land drawing. This is a concrete assembly review item; do not blindly add paste to a custom polygon or assume covered copper will solder.

An SPI controller name alone is not an LCD purchase specification. The exact panel and backlight characteristics remain to be selected/verified.

## ER-03 — Backlight current and 3.3 V budget

Q401's supplier code C20917 identifies **AO3400A**, not an unspecified MOSFET. Its SOT-23 pin arrangement is gate/source/drain, matching the schematic's pads 1/2/3. The manufacturer specifies on-resistance at a 2.5 V gate drive, so its selection is consistent with a roughly 3.3 V control signal. Threshold voltage alone would not establish that. [AOS manufacturer specification](https://www.aosmd.com/products/mosfets/low-voltage-mosfets-12v-30v/ao3400a).

With default JP201 closed, Q401 is driven from +3.3 V through 330 Ω R401. The 33 kΩ pull-down gives an estimated DC gate voltage of:

`Vgate ≈ 3.3 × 33000 / (33000 + 330) = 3.267 V`

This is a calculation from the schematic, not a measurement. The gate network draws approximately 99 µA in this state.

R405/R406/R407 provide separate 47 Ω paths for three LCD LED cathodes. Approximate each branch with:

`Ibranch ≈ (V3V3 − Vf_LED − VDS_Q401) / 47 Ω`

For illustration, at 3.3 V and negligible MOSFET drop, LED forward voltages of 2.8/3.0/3.2 V imply roughly **10.6/6.4/2.1 mA per branch**. These are hypothetical examples, not a rating or prediction for the chosen LCD. Measure voltage across each resistor and use `I = V/R`; then compare with the panel's specified branch current. The circuit is resistor-limited, not a constant-current driver.

The carrier's +3.3 V comes from U202 pin 3. The [Luckfox Mini schematic](https://files.luckfox.com/wiki/Luckfox-Pico/PDF/Luckfox%20Pico%20Mini_pub_sch.pdf) shows a shared module regulator supply. A regulator's headline rating is not the available external current after SoC, memory, SD and camera loads. The external headroom and transient response are **not established**. Record the +3.3 V minimum during display updates, camera capture and card operation before closing this finding.

The default has no PWM dependence. If PWM is later selected, module pin 6, paired jumpers and firmware pinmux must change together; do not infer PWM support from the net name `MCU_BACKLIGHT`.

## ER-04 — Reset: correction to the earlier concern

R601 = 100 kΩ and C601 = 100 nF give a nominal **10 ms RC time constant**. An ideal step produces a 10–90% rise time of about **22 ms** and reaches 3.0 V from a 5 V source after about **9.2 ms**. Real behavior depends on supply ramp, pin loading, capacitor discharge and reset thresholds.

**The 100 ns reset rise/fall figures in DS00001561D page 190 are in the MIN column, not MAX.** The datasheet also explicitly permits an external RC connection on RESET_N. Consequently, the earlier suggestion that the RC might violate a fast maximum edge requirement was not supported. **No reset supervisor or resistor change is justified by that interpretation.** The rendered table was inspected locally in `reference/research/reset-table.png`.

Retain the inherited reset network for this revision. Its actual startup behavior is still a bench item: verify reset initially low, then released, bridge enumeration after repeated power cycles, and recovery after short power interruptions. A nominal RC delay is not a guaranteed reset pulse length. Also verify that reset is not driven high from another source while VDD5 is absent.

## ER-05 — UART, actual bridge variant and firmware

The selected C633309 is **SEC1210/PV-UR2**, the dual-channel UART version. The upstream value had said URT, the single-channel version. The native value/MPN now match the stocked **UR2** part. Only the first card channel is wired on this carrier; the second remains unused. Package dimensions/pitch are consistent with the QFN-24, 5×5 mm, 0.65 mm layout. [Supplier identity](https://www.lcsc.com/product-detail/C633309.html), [Microchip ordering brief](https://ww1.microchip.com/downloads/en/DeviceDoc/PB-SEC1110-SEC1210-00004472.pdf).

The pin direction is correct in the netlist: U202 TX → R602 → U601 RXD pin 11; U601 TXD pin 14 → R603 → U202 RX. The two 100 Ω resistors are series elements, **not voltage translators**. U601 UART outputs use its 3.3 V domain; its inputs tolerate the host's logic. Confirm actual idle/active levels at the module against its I/O specifications; never substitute a 5 V UART transmitter on the host RX path by assumption.

The pinned OS reader configuration selects `/dev/ttyS2:SEC1210URT`. The pinned CCID 1.7.1 source recognizes `SEC1210UR2` separately and gives it two slots. For the selected part, the intended configuration is **`/dev/ttyS2:SEC1210UR2`**, with testing restricted to the physically connected first slot. This has been established from source code, not tested on a device. [Pinned OS configuration](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/files/sec1210), [CCID variant handling](https://github.com/LudovicRousseau/CCID/blob/1.7.1/src/ccid_serial.c).

The driver starts at 9600 baud and attempts a change to 115200. A logic capture can observe either during startup; permanently forcing a baud rate is not a substitute for the driver handshake. Ensure the selected UART is not simultaneously a serial console. The exact shipped firmware image and configuration must be recorded in bring-up.

## ER-06 — USB-C supply and transient protection

R301/R302 separately pull CC2/CC1 to ground with 5.1 kΩ, consistent with a power sink that accepts either cable orientation. J301 carries no USB data. It does not negotiate higher USB-PD voltages or charge a battery.

C668623 identifies **SHOU HAN TYPE-C 6P(073)**. Although the legacy footprint name mentions a HRO connector, the placed pad pattern has been edited: six signal pads at x = ±0.5/±1.52/±2.75 mm, plus four shell slots with 0.5×1.2 mm drills at an 8.64 mm transverse spacing. These dimensions correspond to the selected supplier drawing. The signal lands are extended relative to the drawing, so stencil and final assembly orientation still need DFM verification. Its through-hole shell attachments also need to be included in JLCPCB's assembly process, not left unsoldered. [Supplier selection](https://jlcpcb.com/partdetail/TYPE-C%206P%28073%29/C668623).

D301's C19077498 is **R+O SMF5.0CA**, rather than a qualified Vishay device. The supplier lists a 5 V stand-off and 9.2 V clamp under its specified pulse conditions. That is transient suppression, **not a guarantee that U601's supply stays below its 5.5 V maximum**. There is no demonstrated overvoltage disconnect, reverse-input protection or complete fault-current coordination. Use a regulated 5 V source for this revision; power-input robustness remains open if broader supply faults are in scope. [Actual TVS specification](https://www.lcsc.com/zh-CN/product-detail/C19077498.html).

D302's C2297 is **KT-0805G**, a green indicator. With 560 Ω R303 and the listed 2.6–3.1 V forward-voltage range, estimated current at 5 V is 3.4–4.3 mA; resistor dissipation is about 6.4–10.3 mW. Those calculations fit the selected 125 mW resistor's nominal rating. Brightness and actual current remain measurements. [LED specification](https://www.lcsc.com/it/product-detail/Light-Emitting-Diodes-LED_Hubei-KENTO-Elec-C2297_C2297.html).

C201/C302 provide nominal 10 µF bulk capacitance and C301 local 100 nF bypassing. Their adequacy for host/display/camera/card peak load is not proven by adding the nominal values: voltage bias, cable resistance, supply current limit and transient load matter.

## ER-07 — Buttons and stocked switch mechanics

SW501–SW508 ground the corresponding input when pressed. No external pull-ups are drawn. Firmware must configure the correct GPIO input buffers/pulls and perform debounce. Verify both released and pressed levels; a floating released input is a configuration/circuit finding, not an expected button state.

The supplier selection C318938 is **XKB TS-1101-C-W**, 6×3.6 mm, 2.5 mm high. The footprint/model name instead says **FSMSM**; the actual TE FSMSM is a different-height part, and its checked catalog code C7278475 has no available stock. The native values now name the stocked XKB part, but no automatic geometric substitution has been made.

The existing extended switch copper lands are 3.0×1.6 mm at ±4.5 mm. The XKB drawing's recommended transverse pad extents are 8.6 mm overall and 6.2 mm between inner edges, implying 1.2 mm-wide lands centered at ±3.7 mm. The existing lands overlap the terminal region, but that alone does not qualify reflow placement, paste volume, self-alignment or enclosure actuation. Compare the drawing to the stencil and qualify the exact 2.5 mm actuator with the faceplate. [Stocked XKB part](https://jlcpcb.com/partdetail/C318938), [TE part dimensions](https://www.te.com/en/product-1437566-3.html).

## ER-08 — Smartcard channel and contacts

J601 C1/C2/C3/C5/C7 map to switched VCC/reset/clock/ground/I/O. The normally-open detect switch connects its sense line to ground when actuated. R604/C606 condition clock edges; R605/R606 weakly bias reset/I/O. This is a coherent contact-reader topology, not evidence that every smartcard application is supported.

The C6 contact is tied to card VCC in the inherited circuit. C6 is historically VPP / application-dependent, so check the target card's contact assignment; do not assume an arbitrary ISO-7816 card accepts every contact wiring choice. C4/C8 are unconnected at the socket. The selected socket is [Amphenol 7312P0225A13LF](https://www.amphenol-cs.com/product/7312p0225a13lf.html), with the source's custom extended/contact footprint still requiring drawing/assembly review.

Card power is normally controlled by the bridge. Verify a selected card's supported voltage class and activation; do not manually force 5 V onto card contacts. Clock, reset and I/O levels follow the card domain, not necessarily the host 3.3 V rail. Verify presence, activation, ATR reception, then application selection in that order. A detected reader with no usable applet is different from an electrical reader failure.

## ER-09 — Host mounting, idle rails and multiple inputs

U202 +3.3 V is an output. U202 1.8 V is intentionally unused. If ordering the fully assembled carrier without the module, do not expect the LCD or buttons to operate or the carrier +3.3 V rail to be powered. The independent SEC1210 supply can still be checked on the module-less carrier.

J301, the optional J302 input and the module's own USB power connection are not shown with isolation between independent sources. Use one power source at a time until the exact module schematic and power-path behavior are verified.

Insulate protruding header pins beneath the LCD, as required by the upstream assembly notes. A metal LCD housing shorting +3.3 V to ground defeats otherwise correct circuitry. Confirm the module storage variant and mechanical orientation; module identification is not interchangeable with the PCB's package name.

## Closing the review

The desk review is complete for the circuits above. The unresolved items are specific and testable; they are not a passed electrical qualification. For each prototype record:

- Actual part markings, module variant, firmware version/hash and reader configuration.
- Supply minimum/maximum and current during idle, boot, display activity, camera activity and card activation.
- Reset waveform and repeated cold-start / short-interruption results.
- Three individual backlight currents and rail droop.
- Eight button released/pressed states, camera operation, card presence, ATR and applet operation.
- Evidence that the exact connector/switch land and stencil patterns have been accepted and assembled correctly.

The next separate task is to turn these findings into the staged [bring-up guide](BRINGUP.md) and finish the assembly BOM qualification. Bench evidence must come from a physical prototype; none is invented here.
