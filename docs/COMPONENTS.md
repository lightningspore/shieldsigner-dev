# Component guide

Every physical component in the pinned PCB is covered below. Population flags, footprints and pin/net mappings come from the pinned KiCad PCB. Values and supplier IDs include the documented native variant overrides and catalog identity corrections; the experimental tscircuit reference still uses upstream values. Functional explanations are engineering interpretations unless the hardware guide explicitly attributes them to an upstream note or datasheet. This describes the inherited circuit; it does not claim the original designer compared alternatives or optimized each value.

Use original KiCad pad numbers when wiring or probing. The tscircuit `pinN` names identify individual copper lands, not original package pin numbers. Repeated module pad numbers are intentional (castellated land plus through-hole).

**Default DNP: J302, R404, R408.** Their footprints remain on the board. Populate R403 and R409 for IM1=1 and IM0=0. Never fit both resistors in either strap pair. Solder-jumper pairs have their own open/closed settings; see [hardware guide](HARDWARE.md#configuration).

## Index

| Ref | Value | Block / role | Assembly |
|---|---|---|---|
| [C201](#c201) | 10u | 5 V bulk decoupling | Reference default |
| [C301](#c301) | 100n | 5 V high-frequency decoupling | Reference default |
| [C302](#c302) | 10u | 5 V bulk decoupling | Reference default |
| [C401](#c401) | 100n | LCD logic-supply decoupling | Reference default |
| [C601](#c601) | 100n | SEC1210 reset startup network | Reference default |
| [C602](#c602) | 1u | SEC1210 input-rail decoupling | Reference default |
| [C603](#c603) | 1u | SEC1210 VDD33 decoupling | Reference default |
| [C604](#c604) | 1u | Switched smartcard supply decoupling | Reference default |
| [C605](#c605) | 33p | Card reset high-frequency shunt | Reference default |
| [C606](#c606) | 33p | Card clock high-frequency shunt | Reference default |
| [D301](#d301) | SMF5.0CA | 5 V rail transient clamp | Reference default |
| [D302](#d302) | KT-0805G | Power indicator | Reference default |
| [J301](#j301) | TYPE-C 6P(073) | USB-C power input | Reference default |
| [J302](#j302) | Conn_01x02_Pin | Optional direct 5 V input header | DNP |
| [J401](#j401) | 62684-402100ALF | LCD FPC connector | Reference default |
| [J601](#j601) | 7312P0225A13LF | Smartcard socket | Reference default |
| [JP201](#jp201) | Jumper_2_Small_Bridged | Default backlight source | Reference default |
| [JP202](#jp202) | Jumper_2_Small_Open | Alternative backlight source | Reference default |
| [JP203](#jp203) | Jumper_2_Small_Bridged | Default module pin-6 function | Reference default |
| [JP204](#jp204) | Jumper_2_Small_Open | Alternative module pin-6 function | Reference default |
| [JP205](#jp205) | Jumper_2_Small_Bridged | Default LCD chip-select source | Reference default |
| [JP206](#jp206) | Jumper_2_Small_Open | Alternative permanent LCD select | Reference default |
| [Q401](#q401) | AO3400A | Low-side LCD backlight switch | Reference default |
| [R301](#r301) | 5K1 | USB-C CC sink pull-down | Reference default |
| [R302](#r302) | 5K1 | USB-C CC sink pull-down | Reference default |
| [R303](#r303) | 560R | Power LED current limiter | Reference default |
| [R401](#r401) | 330R | Backlight MOSFET gate series resistor | Reference default |
| [R402](#r402) | 33k | Backlight gate pull-down | Reference default |
| [R403](#r403) | 0R | LCD IM1 mode strap | Reference default |
| [R404](#r404) | 0R | LCD IM1 mode strap | DNP |
| [R405](#r405) | 47R | Individual backlight current limiter | Reference default |
| [R406](#r406) | 47R | Individual backlight current limiter | Reference default |
| [R407](#r407) | 47R | Individual backlight current limiter | Reference default |
| [R408](#r408) | 0R | LCD IM0 mode strap | DNP |
| [R409](#r409) | 0R | LCD IM0 mode strap | Reference default |
| [R410](#r410) | 10K | Unused LCD read-strobe pull-up | Reference default |
| [R601](#r601) | 100K | SEC1210 reset startup network | Reference default |
| [R602](#r602) | 100R | Host UART series damping | Reference default |
| [R603](#r603) | 100R | Host UART series damping | Reference default |
| [R604](#r604) | 47R | Card clock series damping | Reference default |
| [R605](#r605) | 10K | Card reset pull-down | Reference default |
| [R606](#r606) | 100K | Card I/O weak pull-down | Reference default |
| [R607](#r607) | 10K | SEC1210 test-mode bias | Reference default |
| [SW501](#sw501) | TS-1101-C-W | JoystickLeft input switch | Reference default |
| [SW502](#sw502) | TS-1101-C-W | JoystickUp input switch | Reference default |
| [SW503](#sw503) | TS-1101-C-W | JoystickPress input switch | Reference default |
| [SW504](#sw504) | TS-1101-C-W | JoystickDown input switch | Reference default |
| [SW505](#sw505) | TS-1101-C-W | JoystickRight input switch | Reference default |
| [SW506](#sw506) | TS-1101-C-W | Key1 input switch | Reference default |
| [SW507](#sw507) | TS-1101-C-W | Key2 input switch | Reference default |
| [SW508](#sw508) | TS-1101-C-W | Key3 input switch | Reference default |
| [U202](#u202) | LuckFox_Pico_MINI | Linux host module | Reference default |
| [U601](#u601) | SEC1210/PV-UR2 | UART-to-smartcard bridge | Reference default |

## C201

**10u — 5 V bulk decoupling.**

**How it works:** A 10 µF capacitor between +5V and ground provides local charge for load transients; it cannot sustain a long power interruption.

**Why this choice:** The source uses bulk storage at the host interface and power entry, complementing smaller high-frequency decouplers. Effective capacitance depends on dielectric, package and DC bias.

**How it is used:** C201 is associated with the host interface; C302 with power entry. Match the upstream supplier selection or qualify voltage rating, dielectric and effective capacitance; value alone is insufficient.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C15850`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## C301

**100n — 5 V high-frequency decoupling.**

**How it works:** A 100 nF capacitor shunts high-frequency rail noise to ground near the power block.

**Why this choice:** Small ceramic decoupling complements the 10 µF bulk capacitor by providing a short high-frequency current loop. The value is inherited, not newly optimized.

**How it is used:** Populate alongside C302. Preserve the local rail/ground layout rather than moving it to a distant location.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C49678`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## C302

**10u — 5 V bulk decoupling.**

**How it works:** A 10 µF capacitor between +5V and ground provides local charge for load transients; it cannot sustain a long power interruption.

**Why this choice:** The source uses bulk storage at the host interface and power entry, complementing smaller high-frequency decouplers. Effective capacitance depends on dielectric, package and DC bias.

**How it is used:** C201 is associated with the host interface; C302 with power entry. Match the upstream supplier selection or qualify voltage rating, dielectric and effective capacitance; value alone is insufficient.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C15850`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## C401

**100n — LCD logic-supply decoupling.**

**How it works:** A 100 nF capacitor from +3.3V to ground provides a local high-frequency current path for the LCD interface.

**Why this choice:** The LCD logic rail benefits from local decoupling. The source chose 100 nF; retain appropriate voltage rating and ceramic dielectric.

**How it is used:** Keep near J401 and the supply-return path. It is not the backlight current-setting element.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C49678`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `+3.3V` |

## C601

**100n — SEC1210 reset startup network.**

**How it works:** R601 (100 kΩ) pulls the reset net up to +5V and C601 (100 nF) initially holds it near ground. Their nominal RC time constant is 10 ms.

**Why this choice:** The network biases active-low RESET_N and slows its release after power rises. The actual reset threshold, internal bias, rail ramp and permitted edge timing still require datasheet review; 10 ms is not a guaranteed reset pulse duration.

**How it is used:** Preserve the reset net on U601 pin 22. If the bridge fails to start, measure this waveform rather than assuming the RC alone guarantees a compliant reset.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C49678`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_RESET` |
| 2 | `pin2` | `GND` |

## C602

**1u — SEC1210 input-rail decoupling.**

**How it works:** 1 µF from +5V to ground supplies local transient current for the bridge.

**Why this choice:** The input-side local capacitor is inherited and supports the reader load near U601. It complements the board bulk capacitors.

**How it is used:** Keep its connection loop short. Check effective capacitance and voltage rating when substituting parts.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C28323`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## C603

**1u — SEC1210 VDD33 decoupling.**

**How it works:** The native variant uses 1 µF on the separate SEC1210_VDD33 output at U601 pin 18; upstream used 100 nF. This decouples the bridge internal regulator output, which is distinct from carrier +3.3V.

**Why this choice:** Microchip DS00001561D table 6-4 note 6-3 calls for an external 1 µF at this node. The variant follows that requirement; check the selected ceramic capacitor retains sufficient effective capacitance at its DC operating voltage.

**How it is used:** Preserve the separate net and capacitor. Do not tie this node to Luckfox pin 3 just because both are described as 3.3 V.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Native variant change:** Native KiCad variant changes upstream 100 nF to 1 µF: SEC1210 DS00001561D table 6-4, note 6-3 requires an external 1 µF on VDD33. Qualify effective capacitance under bias; supplier selection is inherited from the reference C602.

**Source supplier identifier:** LCSC `C28323`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_VDD33` |
| 2 | `pin2` | `GND` |

## C604

**1u — Switched smartcard supply decoupling.**

**How it works:** The native variant uses 1 µF from SEC1210_SC_VCC to ground at the active card supply output; upstream used 100 nF.

**Why this choice:** Microchip DS00001561D table 6-4 note 6-2 calls for an external 1 µF at the card supply output. The variant aligns the nominal value with that requirement; capacitance under bias still needs qualification.

**How it is used:** Connect to the switched card supply, not +5V. Observe with a card inserted and an activation command; zero volts while inactive need not be a fault.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Native variant change:** Native KiCad variant changes upstream 100 nF to 1 µF: SEC1210 DS00001561D table 6-4, note 6-2 requires an external 1 µF on active card supply output. Qualify effective capacitance under bias; supplier selection is inherited from the reference C602.

**Source supplier identifier:** LCSC `C28323`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_SC_VCC` |
| 2 | `pin2` | `GND` |

## C605

**33p — Card reset high-frequency shunt.**

**How it works:** 33 pF from card reset to ground loads very fast edges and noise. R605 also biases this line low.

**Why this choice:** A small shunt is consistent with signal conditioning on the external card interface. This is an inferred role; no value-selection calculation was found in the source.

**How it is used:** Preserve placement and value. Increasing it arbitrarily can degrade required card reset transitions.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C107115`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_SC_RST` |
| 2 | `pin2` | `GND` |

## C606

**33p — Card clock high-frequency shunt.**

**How it works:** 33 pF from the post-R604 card clock net to ground combines with the 47 Ω series resistor to soften very fast edges.

**Why this choice:** Signal conditioning can reduce ringing on the socket clock line. The simple R×C product is about 1.55 ns, but driver, trace and card capacitance determine the actual response.

**How it is used:** Keep on the socket side of R604. Do not treat it as a clock-generation capacitor or add a crystal to this net.

**Assembly:** Populate in the reference default. 

**Footprint:** `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C107115`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_SC_CLK_PostR` |
| 2 | `pin2` | `GND` |

## D301

**SMF5.0CA — 5 V rail transient clamp.**

**How it works:** A TVS across +5V and ground shunts transient current when its breakdown threshold is exceeded.

**Why this choice:** The source specifies SMF5.0CA for transient protection. The 5.0 in its name does not mean the rail is tightly regulated or clamped to exactly 5 V.

**How it is used:** Keep its ground/current-return path short. This does not replace current limiting, reverse-polarity protection or a regulator. Confirm the fitted supplier part and clamp characteristics against the actual supply/load requirements.

**Assembly:** Populate in the reference default. 

**Footprint:** `Diode_SMD:D_SOD-123F`; bottom side.

**Source supplier identifier:** LCSC `C19077498`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## D302

**KT-0805G — Power indicator.**

**How it works:** Conducts from +5V through the LED and R303 to ground, producing a visible power indication.

**Why this choice:** A simple LED offers a direct check that the supply rail is present. LED colour, forward voltage and brightness must come from the actual supplier part; the generic value alone does not specify them.

**How it is used:** Respect polarity: pad 2 is the anode on +5V; pad 1 is the cathode feeding R303. A lit LED does not prove that Linux booted or that the 3.3 V/card rails are correct.

**Assembly:** Populate in the reference default. 

**Footprint:** `LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder`; bottom side.

**Native variant change:** Native value now states the exact JLCPCB catalog part selected by its supplier ID; electrical copper is unchanged. Footprint and assembly qualification are tracked in BOM.md.

**Source supplier identifier:** LCSC `C2297`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(D302-K)` |
| 2 | `pin2` | `+5V` |

## J301

**TYPE-C 6P(073) — USB-C power input.**

**How it works:** Brings VBUS onto +5V and grounds onto GND. CC pull-down resistors tell a USB-C source that a sink is attached.

**Why this choice:** A power-only connector provides a compact 5 V input. It does not provide USB data, charging, or negotiated higher-voltage USB PD.

**How it is used:** Use a regulated 5 V USB supply. Its shield lands are grounded. Inspect all duplicated VBUS/GND contacts. The host module has a separate USB connector: this design has no demonstrated isolation for powering both at once.

**Assembly:** Populate in the reference default. 

**Footprint:** `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-17`; bottom side.

**Native variant change:** Native value now states the exact JLCPCB catalog part selected by its supplier ID; electrical copper is unchanged. Footprint and assembly qualification are tracked in BOM.md.

**Source supplier identifier:** LCSC `C668623`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| A5 | `pin1` | `Net-(J301-CC1)` |
| A9 | `pin2` | `+5V` |
| A12 | `pin3` | `GND` |
| B5 | `pin4` | `Net-(J301-CC2)` |
| B9 | `pin5` | `+5V` |
| B12 | `pin6` | `GND` |
| S1 | `pin7` | `GND` |
| S1 | `pin8` | `GND` |
| S1 | `pin9` | `GND` |
| S1 | `pin10` | `GND` |

## J302

**Conn_01x02_Pin — Optional direct 5 V input header.**

**How it works:** Provides +5V and ground as an alternate physical supply connection.

**Why this choice:** A two-pin header is convenient on a bench, but the upstream default leaves it unpopulated. There is no regulator or battery charger on this input.

**How it is used:** DNP by default. If deliberately fitted, pin 1 is regulated 5 V and pin 2 ground. Do not apply a raw battery or a higher supply voltage; do not assume multiple power inputs are isolated.

**Assembly:** Do not populate in the reference default. 

**Footprint:** `Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 2 | `pin2` | `GND` |

## J401

**62684-402100ALF — LCD FPC connector.**

**How it works:** Routes power, SPI control and backlight connections into the external 2.8-inch ST7789 display; the connector itself is not a display controller.

**Why this choice:** The inherited 40-position 0.5 mm Amphenol connector matches the reference LCD cable and physical layout. An arbitrary 40-pin LCD can have a different pinout, contact face, voltage or LED current requirement.

**How it is used:** Fit the exact compatible module and confirm cable contact orientation. Pins 9/10/11/13/15 carry CS/clock/DC/MOSI/reset. Parallel-data and touch pins are unused. Pins 38–40 set interface mode. Read the pinout discrepancy in HARDWARE.md before inserting a cable.

**Assembly:** Populate in the reference default. 

**Footprint:** `Seedsigner-plus-library:AMPHENOL_62684-402100ALF`; bottom side.

**Native variant change:** Corrected LCD supplier ID: C19273935 is a bottom-contact Hong Cheng connector; C2931360 is the intended top-contact Amphenol 62684-402100ALF.

**Source supplier identifier:** LCSC `C2931360`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 01 | `pin1` | `unconnected-(J401-Pad01)` |
| 02 | `pin2` | `unconnected-(J401-Pad02)` |
| 03 | `pin3` | `unconnected-(J401-Pad03)` |
| 04 | `pin4` | `unconnected-(J401-Pad04)` |
| 05 | `pin5` | `GND` |
| 06 | `pin6` | `+3.3V` |
| 07 | `pin7` | `+3.3V` |
| 08 | `pin8` | `unconnected-(J401-Pad08)` |
| 09 | `pin9` | `RPI_SPI_CS` |
| 10 | `pin10` | `LCD_SCLK` |
| 11 | `pin11` | `LCD_DC` |
| 12 | `pin12` | `Net-(J401-Pad12)` |
| 13 | `pin13` | `LCD_MOSI` |
| 14 | `pin14` | `unconnected-(J401-Pad14)` |
| 15 | `pin15` | `LCD_RST` |
| 16 | `pin16` | `GND` |
| 17 | `pin17` | `unconnected-(J401-Pad17)` |
| 18 | `pin18` | `unconnected-(J401-Pad18)` |
| 19 | `pin19` | `unconnected-(J401-Pad19)` |
| 20 | `pin20` | `unconnected-(J401-Pad20)` |
| 21 | `pin21` | `unconnected-(J401-Pad21)` |
| 22 | `pin22` | `unconnected-(J401-Pad22)` |
| 23 | `pin23` | `unconnected-(J401-Pad23)` |
| 24 | `pin24` | `unconnected-(J401-Pad24)` |
| 25 | `pin25` | `unconnected-(J401-Pad25)` |
| 26 | `pin26` | `unconnected-(J401-Pad26)` |
| 27 | `pin27` | `unconnected-(J401-Pad27)` |
| 28 | `pin28` | `unconnected-(J401-Pad28)` |
| 29 | `pin29` | `unconnected-(J401-Pad29)` |
| 30 | `pin30` | `unconnected-(J401-Pad30)` |
| 31 | `pin31` | `unconnected-(J401-Pad31)` |
| 32 | `pin32` | `unconnected-(J401-Pad32)` |
| 33 | `pin33` | `+3.3V` |
| 34 | `pin34` | `Net-(J401-Pad34)` |
| 35 | `pin35` | `Net-(J401-Pad35)` |
| 36 | `pin36` | `Net-(J401-Pad36)` |
| 37 | `pin37` | `GND` |
| 38 | `pin38` | `Net-(J401-Pad38)` |
| 39 | `pin39` | `Net-(J401-Pad39)` |
| 40 | `pin40` | `+3.3V` |
| S1 | `pin41` | `unconnected-(J401-SHIELD-PadS1)` |
| S2 | `pin42` | `unconnected-(J401-SHIELD__1-PadS2)` |

## J601

**7312P0225A13LF — Smartcard socket.**

**How it works:** Makes physical contact with the card; the normally-open presence switch connects the detect net to ground when actuated. It does not implement encryption or a protocol.

**Why this choice:** The inherited Amphenol socket matches the footprint and enclosure, includes detection and has eight card contacts. The upstream README describes full-size/SIM support; verify the actual mechanics before assuming any small card fits without an adapter.

**How it is used:** C1 is switched card VCC, C2 reset, C3 clock, C5 ground, C7 I/O; C6 is also tied to card VCC in this design. C4/C8 are unconnected at the socket. Use a compatible card and the upstream insertion orientation. Do not treat this as an SD-card connector.

**Assembly:** Populate in the reference default. 

**Footprint:** `Library:AMPHENOL_7312P0225A13LF_smrt2_combo_handsolder`; bottom side.

**Source supplier identifier:** LCSC `C5417011`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| C1 | `pin3` | `/Smartcard Interface/SEC1210_SC_VCC` |
| C2 | `pin4` | `/Smartcard Interface/SEC1210_SC_RST` |
| C3 | `pin5` | `/Smartcard Interface/SEC1210_SC_CLK_PostR` |
| C4 | `pin6` | `unconnected-(J601-RFU-PadC4)` |
| C5 | `pin7` | `GND` |
| C6 | `pin8` | `/Smartcard Interface/SEC1210_SC_VCC` |
| C7 | `pin9` | `/Smartcard Interface/SEC1210_SC_IO` |
| C8 | `pin10` | `unconnected-(J601-RFU__1-PadC8)` |
| COM | `pin11` | `GND` |
| NO | `pin12` | `/Smartcard Interface/SEC1210_SC_PRSNT` |

## JP201

**Jumper_2_Small_Bridged — Default backlight source.**

**How it works:** Bridges +3.3V to RPI_BACKLIGHT.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Closed by default; JP202 open. Gives always-on backlight through Q401. Never bridge both members of a pair. See HARDWARE.md for the missing logical bridge representation and source discrepancy.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+3.3V` |
| 2 | `pin2` | `RPI_BACKLIGHT` |

## JP202

**Jumper_2_Small_Open — Alternative backlight source.**

**How it works:** Can bridge MCU_BACKLIGHT to RPI_BACKLIGHT.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Open by default. For an intentional PWM alternative, open JP201/JP203/JP205 and close JP202/JP204/JP206: U202 pin 6 then reaches backlight control while LCD CS is grounded. Requires firmware that configures that pin for PWM and supports permanently asserted display CS. MCU_BACKLIGHT has no direct module pad; its connection is through the selected jumpers. Never bridge both members of a pair.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `MCU_BACKLIGHT` |
| 2 | `pin2` | `RPI_BACKLIGHT` |

## JP203

**Jumper_2_Small_Bridged — Default module pin-6 function.**

**How it works:** Bridges MCU_SPI_CS to Net-(JP203-B), which reaches U202 pin 6.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Closed by default; JP204 open. This selects the intended CS path in the inherited interface. Never bridge both members of a pair. See HARDWARE.md for the missing logical bridge representation and source discrepancy.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `MCU_SPI_CS` |
| 2 | `pin2` | `Net-(JP203-B)` |

## JP204

**Jumper_2_Small_Open — Alternative module pin-6 function.**

**How it works:** Can bridge MCU_BACKLIGHT to the U202 pin-6 node.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Open by default; JP203 closed. In the alternative configuration this connects U202 pin 6 to MCU_BACKLIGHT, which reaches Q401 through closed JP202. The default uses closed JP203 instead to reach MCU_SPI_CS. Never bridge both members of a pair.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `MCU_BACKLIGHT` |
| 2 | `pin2` | `Net-(JP203-B)` |

## JP205

**Jumper_2_Small_Bridged — Default LCD chip-select source.**

**How it works:** Bridges MCU_SPI_CS to RPI_SPI_CS at J401 pin 9.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Closed by default; JP206 open. Important: the PCB includes both ends as pads, but closed solder bridges are not native copper/net connections in this port. Never bridge both members of a pair. See HARDWARE.md for the missing logical bridge representation and source discrepancy.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `MCU_SPI_CS` |
| 2 | `pin2` | `RPI_SPI_CS` |

## JP206

**Jumper_2_Small_Open — Alternative permanent LCD select.**

**How it works:** Can bridge GND to RPI_SPI_CS, holding LCD CS low.

**Why this choice:** The upstream schematic uses paired solder jumpers to reuse display-interface signals for different hat configurations. They are physical configuration choices, not fitted resistors.

**How it is used:** Open by default. Closing may be usable with the reference firmware mode, but changes bus-sharing and display-driver requirements; never close simultaneously with JP205. Never bridge both members of a pair. See HARDWARE.md for the missing logical bridge representation and source discrepancy.

**Assembly:** Present in the reference default; jumpers require the stated bridge setting. 

**Footprint:** `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `RPI_SPI_CS` |

## Q401

**AO3400A — Low-side LCD backlight switch.**

**How it works:** An N-channel MOSFET sinks current from three LCD LED-cathode resistor branches to ground. R401 drives the gate; R402 pulls it low when undriven.

**Why this choice:** A MOSFET lets a logic control switch or PWM LED current without passing that current through the GPIO. The source generic symbol is not a purchase specification: supplier C20917 must be checked for actual device, pinout and conduction at a 3.3 V gate drive.

**How it is used:** Gate pad 1, source pad 2 to ground, drain pad 3 to backlight resistors. Default JP201 holds its control high for always-on light. PWM requires the compatible jumper and firmware configuration.

**Assembly:** Populate in the reference default. 

**Footprint:** `Package_TO_SOT_SMD:SOT-23`; bottom side.

**Native variant change:** Native value now states the exact JLCPCB catalog part selected by its supplier ID; electrical copper is unchanged. Footprint and assembly qualification are tracked in BOM.md.

**Source supplier identifier:** LCSC `C20917`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-G)` |
| 2 | `pin2` | `GND` |
| 3 | `pin3` | `Net-(Q401-D)` |

## R301

**5K1 — USB-C CC sink pull-down.**

**How it works:** Each 5.1 kΩ resistor connects one CC pin to ground. Separate resistors allow either plug orientation to advertise a sink.

**Why this choice:** 5.1 kΩ is the conventional USB-C Rd value. Two independent pull-downs are required; connecting CC1 and CC2 together is not equivalent.

**How it is used:** R301 serves CC2 and R302 serves CC1. These are not series power resistors. If C-to-C power is absent, check both CC paths and soldering before changing firmware.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C27834`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(J301-CC2)` |
| 2 | `pin2` | `GND` |

## R302

**5K1 — USB-C CC sink pull-down.**

**How it works:** Each 5.1 kΩ resistor connects one CC pin to ground. Separate resistors allow either plug orientation to advertise a sink.

**Why this choice:** 5.1 kΩ is the conventional USB-C Rd value. Two independent pull-downs are required; connecting CC1 and CC2 together is not equivalent.

**How it is used:** R301 serves CC2 and R302 serves CC1. These are not series power resistors. If C-to-C power is absent, check both CC paths and soldering before changing firmware.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C27834`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(J301-CC1)` |
| 2 | `pin2` | `GND` |

## R303

**560R — Power LED current limiter.**

**How it works:** Limits the current through D302; approximately I=(5 V minus LED forward voltage)/560 Ω.

**Why this choice:** 560 Ω is inherited and gives a modest indicator current for typical LEDs. For example, a 2 V LED drop gives about 5.4 mA; that is an estimate, not a measured current.

**How it is used:** Keep it in series with D302. Do not bridge it. Changing its resistance changes brightness and LED power.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C28636`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `Net-(D302-K)` |

## R401

**330R — Backlight MOSFET gate series resistor.**

**How it works:** 330 Ω is in series between RPI_BACKLIGHT and Q401 gate, limiting gate charging current and reducing edge ringing.

**Why this choice:** The value is an inherited compromise between transition speed and drive current. It does not set steady-state LED current.

**How it is used:** Use together with R402. Trace the default jumper source before assuming RPI_BACKLIGHT is an active GPIO PWM signal.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17630`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-G)` |
| 2 | `pin2` | `RPI_BACKLIGHT` |

## R402

**33k — Backlight gate pull-down.**

**How it works:** 33 kΩ pulls Q401 gate to ground when the driving signal is floating, favouring an off state.

**Why this choice:** A weak pull-down defines startup behaviour without heavily loading a driven high signal. This exact value is inherited.

**How it is used:** Populate from gate net to GND. A missing or wrong-value part may leave the backlight state undefined when the control is disconnected.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17633`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-G)` |
| 2 | `pin2` | `GND` |

## R403

**0R — LCD IM1 mode strap.**

**How it works:** These alternative 0 Ω links connect J401 pad 39 to either +3.3V (R403) or ground (R404).

**Why this choice:** A resistor strap allows manufacturing-time mode selection with the same PCB. The reference SPI mode requires IM1=1.

**How it is used:** Fit R403; leave R404 DNP. Fitting both directly shorts 3.3 V to ground. These are assembly alternatives, not two operating resistors that should both be purchased and fitted.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17477`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(J401-Pad39)` |
| 2 | `pin2` | `+3.3V` |

## R404

**0R — LCD IM1 mode strap.**

**How it works:** These alternative 0 Ω links connect J401 pad 39 to either +3.3V (R403) or ground (R404).

**Why this choice:** A resistor strap allows manufacturing-time mode selection with the same PCB. The reference SPI mode requires IM1=1.

**How it is used:** Fit R403; leave R404 DNP. Fitting both directly shorts 3.3 V to ground. These are assembly alternatives, not two operating resistors that should both be purchased and fitted.

**Assembly:** Do not populate in the reference default. Excluded from the upstream BOM.

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17477`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(J401-Pad39)` |
| 2 | `pin2` | `GND` |

## R405

**47R — Individual backlight current limiter.**

**How it works:** Each 47 Ω resistor sits between one LED cathode and Q401 drain. Separate resistors limit the current in individual LED branches.

**Why this choice:** This simple resistor arrangement is inherited for the reference LCD; it is not a constant-current driver. Current depends on LED forward voltage, 3.3 V rail and MOSFET drop.

**How it is used:** R405 serves LCD pad 36, R406 pad 35, R407 pad 34. Do not parallel the resistors into one branch or bypass them. Recalculate and measure currents when changing the LCD.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17714`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-D)` |
| 2 | `pin2` | `Net-(J401-Pad36)` |

## R406

**47R — Individual backlight current limiter.**

**How it works:** Each 47 Ω resistor sits between one LED cathode and Q401 drain. Separate resistors limit the current in individual LED branches.

**Why this choice:** This simple resistor arrangement is inherited for the reference LCD; it is not a constant-current driver. Current depends on LED forward voltage, 3.3 V rail and MOSFET drop.

**How it is used:** R405 serves LCD pad 36, R406 pad 35, R407 pad 34. Do not parallel the resistors into one branch or bypass them. Recalculate and measure currents when changing the LCD.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17714`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-D)` |
| 2 | `pin2` | `Net-(J401-Pad35)` |

## R407

**47R — Individual backlight current limiter.**

**How it works:** Each 47 Ω resistor sits between one LED cathode and Q401 drain. Separate resistors limit the current in individual LED branches.

**Why this choice:** This simple resistor arrangement is inherited for the reference LCD; it is not a constant-current driver. Current depends on LED forward voltage, 3.3 V rail and MOSFET drop.

**How it is used:** R405 serves LCD pad 36, R406 pad 35, R407 pad 34. Do not parallel the resistors into one branch or bypass them. Recalculate and measure currents when changing the LCD.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17714`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(Q401-D)` |
| 2 | `pin2` | `Net-(J401-Pad34)` |

## R408

**0R — LCD IM0 mode strap.**

**How it works:** These alternative 0 Ω links connect J401 pad 38 to either +3.3V (R408) or ground (R409).

**Why this choice:** The reference 4-line SPI configuration needs IM0=0, while alternative links allow another module mode without routing changes.

**How it is used:** Leave R408 DNP; fit R409. Fitting both shorts 3.3 V to ground. J401 pad 40 (IM2) is already high, giving IM2/IM1/IM0 = 1/1/0.

**Assembly:** Do not populate in the reference default. Excluded from the upstream BOM.

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17477`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Net-(J401-Pad38)` |
| 2 | `pin2` | `+3.3V` |

## R409

**0R — LCD IM0 mode strap.**

**How it works:** These alternative 0 Ω links connect J401 pad 38 to either +3.3V (R408) or ground (R409).

**Why this choice:** The reference 4-line SPI configuration needs IM0=0, while alternative links allow another module mode without routing changes.

**How it is used:** Leave R408 DNP; fit R409. Fitting both shorts 3.3 V to ground. J401 pad 40 (IM2) is already high, giving IM2/IM1/IM0 = 1/1/0.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17477`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `Net-(J401-Pad38)` |

## R410

**10K — Unused LCD read-strobe pull-up.**

**How it works:** 10 kΩ pulls J401 pad 12 (RDX in the schematic note) to +3.3V.

**Why this choice:** In this SPI configuration the parallel read strobe is not used. A defined high level prevents an otherwise floating control input; retain the reference module mapping.

**How it is used:** Populate; it is not a MOSI or MISO termination resistor. Confirm pad numbering against the actual display cable.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17414`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+3.3V` |
| 2 | `pin2` | `Net-(J401-Pad12)` |

## R601

**100K — SEC1210 reset startup network.**

**How it works:** R601 (100 kΩ) pulls the reset net up to +5V and C601 (100 nF) initially holds it near ground. Their nominal RC time constant is 10 ms.

**Why this choice:** The network biases active-low RESET_N and slows its release after power rises. The actual reset threshold, internal bias, rail ramp and permitted edge timing still require datasheet review; 10 ms is not a guaranteed reset pulse duration.

**How it is used:** Preserve the reset net on U601 pin 22. If the bridge fails to start, measure this waveform rather than assuming the RC alone guarantees a compliant reset.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C149504`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_RESET` |
| 2 | `pin2` | `+5V` |

## R602

**100R — Host UART series damping.**

**How it works:** Each 100 Ω resistor is in series in a host/bridge UART path, moderating edge current and ringing.

**Why this choice:** The bridge and host use compatible digital UART paths in the reference design. A series resistor is not a voltage-level translator. Exact values are inherited.

**How it is used:** R602 carries host TX to U601 RXD pin 11; R603 carries U601 TXD pin 14 to host RX. No RTS/CTS are routed. Verify baud rate, console conflicts and voltage compatibility before changing the circuit.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17408`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `UART_TX` |
| 2 | `pin2` | `/Smartcard Interface/UART_TX_PostR` |

## R603

**100R — Host UART series damping.**

**How it works:** Each 100 Ω resistor is in series in a host/bridge UART path, moderating edge current and ringing.

**Why this choice:** The bridge and host use compatible digital UART paths in the reference design. A series resistor is not a voltage-level translator. Exact values are inherited.

**How it is used:** R602 carries host TX to U601 RXD pin 11; R603 carries U601 TXD pin 14 to host RX. No RTS/CTS are routed. Verify baud rate, console conflicts and voltage compatibility before changing the circuit.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17408`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `UART_RX` |
| 2 | `pin2` | `/Smartcard Interface/UART_RX_PostR` |

## R604

**47R — Card clock series damping.**

**How it works:** 47 Ω is in series between U601 SC1_CLK and the card clock net at J601 C3.

**Why this choice:** The external card clock path benefits from edge conditioning. Source values and geometry are retained; no signal-integrity simulation has been performed for the port.

**How it is used:** Keep near its intended source/route and preserve C606 on the post-resistor net. It does not divide the clock frequency.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17714`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `/Smartcard Interface/SEC1210_SC_CLK_PreR` |
| 2 | `pin2` | `/Smartcard Interface/SEC1210_SC_CLK_PostR` |

## R605

**10K — Card reset pull-down.**

**How it works:** 10 kΩ from SEC1210_SC_RST to ground biases the card reset line low when undriven.

**Why this choice:** A low default is consistent with inactive/reset card behaviour. This exact strength is inherited, not a newly proven optimum.

**How it is used:** This is J601 card reset, not the separate U601 chip reset net serviced by R601/C601.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17414`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `/Smartcard Interface/SEC1210_SC_RST` |

## R606

**100K — Card I/O weak pull-down.**

**How it works:** 100 kΩ from the bidirectional card I/O net to ground provides a weak low bias when otherwise undriven.

**Why this choice:** The source includes this bias. It is not a UART receive pull-up or a level shifter; card line behaviour depends on the SEC1210 driver and card.

**How it is used:** Preserve at J601 C7/U601 pin 6. Avoid replacing it with a much stronger pull-down, which would load the active card bus.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C149504`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `/Smartcard Interface/SEC1210_SC_IO` |

## R607

**10K — SEC1210 test-mode bias.**

**How it works:** 10 kΩ pulls U601 TEST pin 15 to ground.

**Why this choice:** A defined low on the test pin supports normal operation rather than an unintended test mode. Other boot/debug settings remain dependent on the exact device and firmware.

**How it is used:** Populate and keep this net low for the reference build. Do not use TEST as an application GPIO without reviewing startup mode selection.

**Assembly:** Populate in the reference default. 

**Footprint:** `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder`; bottom side.

**Source supplier identifier:** LCSC `C17414`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `GND` |
| 2 | `pin2` | `Net-(U601-TEST)` |

## SW501

**TS-1101-C-W — JoystickLeft input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to JoystickLeft and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `JoystickLeft` |
| 2 | `pin2` | `GND` |

## SW502

**TS-1101-C-W — JoystickUp input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to JoystickUp and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `JoystickUp` |
| 2 | `pin2` | `GND` |

## SW503

**TS-1101-C-W — JoystickPress input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to JoystickPress and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `JoystickPress` |
| 2 | `pin2` | `GND` |

## SW504

**TS-1101-C-W — JoystickDown input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to JoystickDown and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `JoystickDown` |
| 2 | `pin2` | `GND` |

## SW505

**TS-1101-C-W — JoystickRight input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to JoystickRight and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `JoystickRight` |
| 2 | `pin2` | `GND` |

## SW506

**TS-1101-C-W — Key1 input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to Key1 and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Key1` |
| 2 | `pin2` | `GND` |

## SW507

**TS-1101-C-W — Key2 input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to Key2 and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Key2` |
| 2 | `pin2` | `GND` |

## SW508

**TS-1101-C-W — Key3 input switch.**

**How it works:** Pressing the normally-open switch connects its input net to ground. With a pull-up configured, the GPIO reads high when released and low when pressed.

**Why this choice:** The inherited tactile switch footprint and supplier selection match the handheld button positions. The five joystick functions are separate switches, not an analog joystick.

**How it is used:** Connect pad 1 to Key3 and pad 2 to ground. There are no external pull-up resistors in this button block: firmware must configure appropriate pulls and debounce. A floating or stuck input can be a pinmux/pull issue, not a missing series resistor.

**Assembly:** Populate in the reference default. 

**Footprint:** `ShieldSigner:XKB_TS1101_C_W_extended`; top side.

**Native variant change:** Selected XKB identity uses a dedicated native footprint with a 9.1 × 6.5 mm assembly courtyard based on the body/terminal/recommended-land envelope plus 0.25 mm. Existing extended 3.0 × 1.6 mm copper lands are retained; paste/reflow and 2.5 mm actuator height remain assembly qualification items.

**Source supplier identifier:** LCSC `C318938`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `Key3` |
| 2 | `pin2` | `GND` |

## U202

**LuckFox_Pico_MINI — Linux host module.**

**How it works:** Runs the signer application and firmware, drives SPI display and GPIO inputs, and communicates with the smartcard bridge over UART. The module supplies the carrier 3.3 V rail from its 3V3(OUT) pin.

**Why this choice:** The inherited Pico Mini interface combines Linux, camera CSI and the required digital interfaces on a small module. Mini A/B storage choice determines the firmware image; the carrier is not a discrete RV1103 design.

**How it is used:** Feed pin 1 with 5 V; pin 3 is a 3.3 V output, not a second power input. Mount microSD side upward and USB end toward the board edge. Camera plugs directly into the module. Leave the 1.8 V output unconnected. See the host pin table and module/version caveats in HARDWARE.md.

**Assembly:** Populate in the reference default. 

**Footprint:** `Library:LUCKFOX_PICO_MINI_reversed`; bottom side.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin1` | `+5V` |
| 1 | `pin2` | `+5V` |
| 2 | `pin3` | `GND` |
| 2 | `pin4` | `GND` |
| 3 | `pin5` | `+3.3V` |
| 3 | `pin6` | `+3.3V` |
| 4 | `pin7` | `UART_TX` |
| 4 | `pin8` | `UART_TX` |
| 5 | `pin9` | `UART_RX` |
| 5 | `pin10` | `UART_RX` |
| 6 | `pin11` | `Net-(JP203-B)` |
| 6 | `pin12` | `Net-(JP203-B)` |
| 7 | `pin13` | `LCD_SCLK` |
| 7 | `pin14` | `LCD_SCLK` |
| 8 | `pin15` | `LCD_MOSI` |
| 8 | `pin16` | `LCD_MOSI` |
| 9 | `pin17` | `LCD_RST` |
| 9 | `pin18` | `LCD_RST` |
| 10 | `pin19` | `LCD_DC` |
| 10 | `pin20` | `LCD_DC` |
| 11 | `pin21` | `Key3` |
| 11 | `pin22` | `Key3` |
| 12 | `pin23` | `JoystickLeft` |
| 12 | `pin24` | `JoystickLeft` |
| 13 | `pin25` | `JoystickUp` |
| 13 | `pin26` | `JoystickUp` |
| 14 | `pin27` | `I2C-SDA` |
| 14 | `pin28` | `I2C-SDA` |
| 15 | `pin29` | `I2C-SCL` |
| 15 | `pin30` | `I2C-SCL` |
| 16 | `pin31` | `JoystickPress` |
| 16 | `pin32` | `JoystickPress` |
| 17 | `pin33` | `JoystickDown` |
| 17 | `pin34` | `JoystickDown` |
| 18 | `pin35` | `JoystickRight` |
| 18 | `pin36` | `JoystickRight` |
| 19 | `pin37` | `Key1` |
| 19 | `pin38` | `Key1` |
| 20 | `pin39` | `Key2` |
| 20 | `pin40` | `Key2` |
| 21 | `pin41` | `GND` |
| 21 | `pin42` | `GND` |
| 22 | `pin43` | `unconnected-(U202-1V8(OUT)-Pad22)` |
| 22 | `pin44` | `unconnected-(U202-1V8(OUT)-Pad22)` |

## U601

**SEC1210/PV-UR2 — UART-to-smartcard bridge.**

**How it works:** Converts host UART traffic into smartcard clock, reset, power, detection and bidirectional data transactions. Uses one card channel; USB and the second card channel are unused here.

**Why this choice:** SEC1210 provides the card protocol/timing and voltage interface that a GPIO UART alone cannot provide. The upstream firmware supports this UART bridge. The exact preprogrammed suffix matters; a similarly named blank or differently configured device is not an established substitute.

**How it is used:** 5 V enters pin 3; pin 18 has its own VDD33 decoupler. Host TX goes to RXD pin 11 and host RX comes from TXD pin 14. Use the upstream compatible reader driver and disable a competing serial console. The smartcard, not this bridge, provides Satochip/SeedKeeper key storage.

**Assembly:** Populate in the reference default. 

**Footprint:** `Package_DFN_QFN:QFN-24-1EP_5x5mm_P0.65mm_EP3.4x3.4mm`; bottom side.

**Native variant change:** Native value now states the exact JLCPCB catalog part selected by its supplier ID; electrical copper is unchanged. Footprint and assembly qualification are tracked in BOM.md.

**Source supplier identifier:** LCSC `C633309`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification.

| Original pad | tscircuit physical land | Connected net |
|---|---|---|
| 1 | `pin5` | `unconnected-(U601-SC2_RST_N-Pad1)` |
| 2 | `pin6` | `unconnected-(U601-SC2_VCC-Pad2)` |
| 3 | `pin7` | `+5V` |
| 4 | `pin8` | `/Smartcard Interface/SEC1210_C8` |
| 5 | `pin9` | `/Smartcard Interface/SEC1210_C4` |
| 6 | `pin10` | `/Smartcard Interface/SEC1210_SC_IO` |
| 7 | `pin11` | `/Smartcard Interface/SEC1210_SC_CLK_PreR` |
| 8 | `pin12` | `/Smartcard Interface/SEC1210_SC_RST` |
| 9 | `pin13` | `/Smartcard Interface/SEC1210_SC_VCC` |
| 10 | `pin14` | `/Smartcard Interface/SEC1210_SC_PRSNT` |
| 11 | `pin15` | `/Smartcard Interface/UART_TX_PostR` |
| 12 | `pin16` | `unconnected-(U601-SPI1_CLK{slash}CTS-Pad12)` |
| 13 | `pin17` | `unconnected-(U601-SPI1_CE{slash}RTS-Pad13)` |
| 14 | `pin18` | `/Smartcard Interface/UART_RX_PostR` |
| 15 | `pin19` | `Net-(U601-TEST)` |
| 16 | `pin20` | `unconnected-(U601-USB_DM-Pad16)` |
| 17 | `pin21` | `unconnected-(U601-USB_DP-Pad17)` |
| 18 | `pin22` | `/Smartcard Interface/SEC1210_VDD33` |
| 19 | `pin23` | `unconnected-(U601-JTAG_CLK-Pad19)` |
| 20 | `pin24` | `unconnected-(U601-SC_LED_ACT_N{slash}JTAG_TDO-Pad20)` |
| 21 | `pin25` | `unconnected-(U601-SC2_PRSNT_N{slash}JTAG_TDI-Pad21)` |
| 22 | `pin26` | `/Smartcard Interface/SEC1210_RESET` |
| 23 | `pin27` | `unconnected-(U601-SC2_IO-Pad23)` |
| 24 | `pin28` | `unconnected-(U601-SC2_CLK-Pad24)` |
| 25 | `pin29` | `GND` |
