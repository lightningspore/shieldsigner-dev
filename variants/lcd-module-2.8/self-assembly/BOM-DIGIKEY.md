# DigiKey self-assembly BOM

Optional sourcing for the revised **0.0.5-dev eight-pin pill carrier**. JLCPCB remains the primary assembled-board ordering path. This overlay never replaces the JLC BOM/CPL or native part fields.

**35 SMT pieces / 17 DigiKey lines are selected, including every capacitor, resistor, LED and TVS (23 pieces / 12 lines).** The revised switches and USB-C use exact shared JLCPCB/DigiKey manufacturer parts. LCD, camera and Luckfox are excluded; customer headers and mechanical hardware remain separate.

[Download DigiKey CSV](bom-digikey.csv) · [Remaining original-parts CSV](remaining-parts.csv)

Stock is a dated observation, not reserved inventory. Counts marked “not recorded” require a checkout-time check. Quantities are exact installed counts without spares or soldering losses. Cut-tape order codes avoid full-reel minimums.

| References | Value / requirements | Qty: 1 / 5 boards | Selected MPN | DigiKey cut-tape/tray code | Stock snapshot |
|---|---|---:|---|---|---:|
| C605, C606 | 33 pF; 0805; 50 V; ±5%; C0G/NP0 | 2 / 10 | CC0805JRNPO9BN330 | [311-1105-1-ND](https://www.digikey.com/en/products/detail/yageo/CC0805JRNPO9BN330/302839) | 61962 |
| C301, C601 | 100 nF; 0805; 50 V; ±10%; X7R | 2 / 10 | CC0805KRX7R9BB104 | [311-1140-1-ND](https://www.digikey.com/en/products/detail/yageo/CC0805KRX7R9BB104/303050) | 880728 |
| C201, C302, C701, C702 | 10 µF; 0805; 25 V; ±10%; X5R; 0.95 mm max height | 4 / 20 | CL21A106KACLRNC | [1276-2397-1-ND](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21A106KACLRNC/3888055) | 2546 |
| C602, C603, C604 | 1 µF; 0805; 50 V; ±10%; X7R | 3 / 15 | C0805C105K5RACTU | [399-C0805C105K5RACTUCT-ND](https://www.digikey.com/en/products/detail/kemet/C0805C105K5RACTU/3317615) | 125411 |
| R601, R606 | 100 kΩ; 0805; ±1%; 125 mW | 2 / 10 | RC0805FR-07100KL | [311-100KCRCT-ND](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07100KL/727544) | 526449 |
| R602, R603 | 100 Ω; 0805; ±1%; 125 mW | 2 / 10 | RC0805FR-07100RL | [311-100CRCT-ND](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07100RL/727543) | 1083343 |
| R605, R607 | 10 kΩ; 0805; ±1%; 125 mW | 2 / 10 | RC0805FR-0710KL | [311-10.0KCRCT-ND](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0710KL/727535) | 1580141 |
| R604 | 47 Ω; 0805; ±1%; 125 mW | 1 / 5 | RC0805FR-0747RL | [311-47.0CRCT-ND](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0747RL/730919) | 94241 |
| R301, R302 | 5.1 kΩ; 0805; ±1%; 125 mW | 2 / 10 | CR0805-FX-5101ELF | [CR0805-FX-5101ELFCT-ND](https://www.digikey.com/en/products/detail/bourns-inc/CR0805-FX-5101ELF/3784995) | 28897 |
| R303 | 560 Ω; 0805; ±1%; 125 mW | 1 / 5 | RC0805FR-07560RL | [311-560CRCT-ND](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07560RL/728036) | 45507 |
| D302 | Green LED; 0805; 2.00×1.25 mm; 0.75 mm max height; Vf typ 2.65 V at 2 mA | 1 / 5 | APT2012LZGCK | [754-1939-1-ND](https://www.digikey.com/en/products/detail/kingbright/APT2012LZGCK/5177440) | 75055 |
| D301 | 5 V bidirectional TVS; SOD-123F; VRWM 5 V; VBR 6.4–7.0 V; VC max 9.2 V at 21.7 A; 200 W (10/1000 µs) | 1 / 5 | SMF5.0CA | [18-SMF5.0CACT-ND](https://www.digikey.com/en/products/detail/littelfuse-inc/SMF5-0CA/11206223) | 11192 |
| U701 | 3.3 V LDO; SOT-25; 600 mA | 1 / 5 | AP2112K-3.3TRG1 | [AP2112K-3.3TRG1DICT-ND](https://www.digikey.com/en/products/detail/diodes-incorporated/AP2112K-3-3TRG1/4470746) | not recorded |
| J601 | Contact smartcard socket; Original full-size contact socket | 1 / 5 | 7312P0225A13LF | [609-4481-ND](https://www.digikey.com/en/products/detail/amphenol-cs-fci/7312P0225A13LF/1527047) | 3141 |
| U601 | UART smartcard bridge; 24-QFN 5×5 mm; UR2 firmware | 1 / 5 | SEC1210/PV-UR2 | [SEC1210/PV-UR2-ND](https://www.digikey.com/en/products/detail/microchip-technology/SEC1210-PV-UR2/6192958) | 56 |
| SW501, SW502, SW503, SW504, SW505, SW506, SW507, SW508 | Momentary switch; G leads; 2.5 mm nominal height; 250 gf; SPST-NO | 8 / 40 | PTS636SK25SMTRLFS | [CKN12322-1-ND](https://www.digikey.com/en/products/detail/c-k/PTS636SK25SMTR-LFS/10071735) | 20644 |
| J301 | USB-C power input; 6 contacts; default 1.00 mm shell stakes; 3 A connector rating | 1 / 5 | USB4125-GF-A | [2073-USB4125-GF-ACT-ND](https://www.digikey.com/en/products/detail/gct/USB4125-GF-A/13547388) | 13606 |

## Unresolved fitted parts (none in this revision)


## Assembly notes

- All resistors remain 0805, ±1%, 125 mW with the same resistance. Capacitors retain nominal capacitance, voltage class, tolerance and dielectric. No pad or net changes are required by this sourcing overlay.
- The green LED uses the existing 560 Ω resistor. Its typical 2.65 V forward voltage gives an illustrative `(5 − 2.65) / 560 ≈ 4.2 mA`; actual current and brightness vary. Follow native K/cathode polarity.
- The TVS remains bidirectional 5 V stand-off / 200 W pulse class. A 9.2 V clamp rating is not an overvoltage shutdown or a guarantee that every downstream supply pin stays within its absolute maximum.
- Self-assembly of the entire board still includes the exposed-pad QFN smartcard bridge. Use a controlled paste/reflow process and inspection; the large passive lands do not make the QFN an ordinary header-soldering task.
- Use the revision-specific C&K switch and GCT USB4125 lands. Old-board footprints and enclosure plungers are not interchangeable by assumption.
- Physical bring-up and supply/camera/display qualification remain pending; use the staged assembly guide.

## Selection notes

- **C605, C606**: Same MPN as JLC.
- **C301, C601**: Same MPN as JLC.
- **C201, C302, C701, C702**: Replaces CL21A106KAYNNNE with the same nominal capacitance, voltage, tolerance and dielectric; lower body height.
- **C602, C603, C604**: Replaces CL21B105KBFNNNE at matching capacitance, voltage, tolerance and dielectric.
- **R601, R606**: Same resistance, tolerance and nominal power rating.
- **R602, R603**: Same resistance, tolerance and nominal power rating.
- **R605, R607**: Same resistance, tolerance and nominal power rating.
- **R604**: Same resistance, tolerance and nominal power rating.
- **R301, R302**: Same USB-C Rd resistance/tolerance/power. Selected over out-of-stock Yageo RC0805FR-075K1L.
- **R303**: Same LED series resistance, tolerance and power rating.
- **D302**: Green indicator on the existing LED lands; retain R303 560 Ω. Match cathode to native pad 1/K; brightness can differ.
- **D301**: Same TVS function and nominal pulse/clamp class in the existing SOD-123F footprint. Bidirectional CA required; does not add overvoltage disconnect.
- **U701**: Exact original regulator.
- **J601**: Exact original socket; orientation follows native drawing.
- **U601**: Exact original firmware suffix; do not use URT or another SEC1210 variant.
- **SW501, SW502, SW503, SW504, SW505, SW506, SW507, SW508**: Exact shared JLC/DigiKey MPN; revised native footprint. Requires physical first-article qualification.
- **J301**: Exact shared JLC/DigiKey MPN; revised native footprint. Requires physical first-article qualification.

## Retained reference

[Kingbright LED drawing and ratings](../../../reference/pdfs/Kingbright-APT2012LZGCK.pdf). The [Littelfuse SMF manufacturer data sheet](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smf_datasheet.pdf.pdf) is the online TVS reference. The original JLC TVS drawing is retained separately.

## Board identity

Board SHA-256: `d9ff1151deb55c36f355f1967cd5b3d3d09a6c394cdcebefc71823b60bdf0cdf`.
Supplier pages checked 2026-10-17. Rebuild using `mise run bom:self-assembly`; verify generated data with `mise run bom:self-assembly -- --check`.
