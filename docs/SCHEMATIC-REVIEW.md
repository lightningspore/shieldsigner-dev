# Schematic review — 11 November 2026

Reviewed all six native sheets for the working 0.0.12-dev main board, using native PDF renders, KiCad MCP inspection/ERC, the module-pinout audit and an independent before/after XML netlist comparison.

| Sheet | Review and result |
|---|---|
| System overview | Reading map, five child sheets, four-layer stackup and factory jumper defaults agree with the design. |
| Host and straps | U202 is the fitted Luckfox module; U201/TP201 are explicitly schematic-only legacy references. Confirmed default backlight/CS straps and the host GPIO mapping. Stacked legacy symbol pin numbers remain an inherited presentation limitation. |
| Power | Each USB-C CC pin has its own 5.1 kOhm pull-down. Bypass, TVS and LED branch are legible. Re-spaced all nine service symbols and their wire/label groups so TP909 and its labels fit inside the drawing border. Physical clip positions are unchanged. |
| Buttons | Eight active-low inputs match the host pinout. Added the 1.8 V domain warning for Key1/Key2 (GPIO4_C0/GPIO4_C1); other button inputs use 3.3 V. |
| Smartcard reader | Checked host TX/RX crossing, reset/test networks, reader/card bypass, clock damping, card detect and intentionally unused interfaces. Added explicit UART directions and U601 pin numbers to remove ambiguity. |
| Display | Eight-pin carrier/module numbering and dedicated LCD_3V3 rail agree with the pinout audit. VIN and EN share +5 V; NC is unconnected. Added the rear placement of U701/C701/C702 to the service notes. |

Only presentation and explanatory notes changed. Native component references, values, footprint assignments and the complete electrical pin partitions are identical before and after, including all nine service points. The PCB file is byte-for-byte unchanged. Native ERC/DRC/connectivity/parity and the module pinout audit pass under the current project rules.

The MCP readability check reported 49 heuristic findings and a cosmetic score of 16/100 before this pass. Many estimated symbol/power-symbol bounding boxes overlap even where the native rendering is readable; stacked legacy pins also confuse text estimates. These scores were used as inspection leads, not as acceptance criteria. Every sheet was inspected in the native PDF. The actual service-row clipping was corrected rather than blindly moving electrically connected objects to clear heuristic warnings.

Outstanding physical checks remain: regulated 5 V bench input and USB must not be driven together; there is no source selection or reverse-polarity protection. Measure LCD supply/current/temperature, button input levels and reader/card operation on first articles. TVS presence and clean ERC do not establish overvoltage protection or powered qualification.

Regenerate the PDF and overview PNG with `mise run hardware:review`. The detailed netlist evidence is in `hardware/schematic-once-over-audit.json` and `hardware/service-schematic-audit.json`.
