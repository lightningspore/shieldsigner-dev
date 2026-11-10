# Hardware datasheets

Local PDF references cover all **18 SKUs / 43 placements** in the current
0.0.11-dev factory BOM, plus the host/LCD modules and historical alternatives.
`manifest.json` records original paths or public source pages and SHA-256;
`bom-coverage.json` binds the table below to the exact BOM bytes.
Some documents cover a component family; coverage is not physical qualification.
The original snapshots in `reference/pdfs/` are preserved. PDFs use Git LFS.

Run `mise run datasheets:check` to validate the collection, or
`mise run datasheets:fetch` to obtain missing current-BOM PDFs.

## Current factory BOM

| Component | LCSC | References | Local document |
|---|---|---|---|
| CC0805JRNPO9BN330 | C107115 | C605, C606 | [C107115.pdf](C107115.pdf) |
| 0805W8F1003T5E | C149504 | R601, R606 | [C149504.pdf](C149504.pdf) |
| CL21A106KAYNNNE | C15850 | C201, C302, C701, C702 | [Samsung-CL21A106KAYNNNE-spec.pdf](Samsung-CL21A106KAYNNNE-spec.pdf) |
| 0805W8F1000T5E | C17408 | R602, R603 | [C17408.pdf](C17408.pdf) |
| 0805W8F1002T5E | C17414 | R605, R607 | [C17414.pdf](C17414.pdf) |
| 0805W8F470JT5E | C17714 | R604 | [C17714.pdf](C17714.pdf) |
| SMF5.0CA | C19077498 | D301 | [C19077498-current.pdf](C19077498-current.pdf) |
| KT-0805G | C2297 | D302 | [C2297.pdf](C2297.pdf) |
| PTS636SK25SMTRLFS | C2689642 | SW501, SW502, SW503, SW504, SW505, SW506, SW507, SW508 | [CK-PTS636.pdf](CK-PTS636.pdf) |
| 0805W8F5101T5E | C27834 | R301, R302 | [C27834.pdf](C27834.pdf) |
| CL21B105KBFNNNE | C28323 | C602, C603, C604 | [C28323.pdf](C28323.pdf) |
| 0805W8F5600T5E | C28636 | R303 | [C28636.pdf](C28636.pdf) |
| 5015 | C2906768 | TP901, TP902, TP903, TP904, TP905, TP906, TP907, TP908 | [Keystone-5015.pdf](Keystone-5015.pdf) |
| CC0805KRX7R9BB104 | C49678 | C301, C601 | [C49678.pdf](C49678.pdf) |
| AP2112K-3.3TRG1 | C51118 | U701 | [Diodes-AP2112.pdf](Diodes-AP2112.pdf) |
| USB4125-GF-A-0190 | C5246813 | J301 | [GCT-USB4125.pdf](GCT-USB4125.pdf) |
| 7312P0225A13LF | C5417011 | J601 | [C5417011.pdf](C5417011.pdf) |
| SEC1210/PV-UR2 | C633309 | U601 | [SEC1210-DS00001561D.pdf](SEC1210-DS00001561D.pdf) |

## Modules, supporting data and retained alternatives

These are additional references, not automatic substitutes for the selected parts.

- [AO3400A.pdf](AO3400A.pdf)
- [C19077498.pdf](C19077498.pdf)
- [C2931360.pdf](C2931360.pdf)
- [C2939938.pdf](C2939938.pdf)
- [C318938.pdf](C318938.pdf)
- [C668623.pdf](C668623.pdf)
- [GCT-USB4135.pdf](GCT-USB4135.pdf)
- [HOTHMI-HTM-TFT028A16-SPI.pdf](HOTHMI-HTM-TFT028A16-SPI.pdf)
- [Kingbright-APT2012LZGCK.pdf](Kingbright-APT2012LZGCK.pdf)
- [Luckfox-Pico-Mini.pdf](Luckfox-Pico-Mini.pdf)
- [Microchip-AN2089-QFN-assembly.pdf](Microchip-AN2089-QFN-assembly.pdf)
- [Samsung-CL21A106KAYNNNE-characteristics.pdf](Samsung-CL21A106KAYNNNE-characteristics.pdf)
- [Waveshare-Pico-ResTouch-LCD-2.8-Schematic.pdf](Waveshare-Pico-ResTouch-LCD-2.8-Schematic.pdf)

Keystone primary reference: [manufacturer drawing](https://www.keyelco.com/product-pdf.cfm?p=1353).
