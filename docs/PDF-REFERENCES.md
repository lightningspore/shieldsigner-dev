# Saved reference PDFs

All retained supplier/manufacturer PDFs are in `reference/pdfs/`, tracked by Git LFS. Generated native schematic PDFs are release artifacts. The index records original sources, byte sizes and SHA-256; retained references are not automatic part selections.

The current pill LCD and added regulator use **HOTHMI-HTM-TFT028A16-SPI.pdf** and **Diodes-AP2112.pdf**. The former Pico display schematic and standard bare-panel PDFs remain archived for their separate revisions.

| Document | Source | SHA-256 |
|---|---|---|
| [AO3400A](../reference/pdfs/AO3400A.pdf) | Original URL not recorded | `9c60d0b6c1ddc7609a4b788a91181468d8ffe6c3e9ba425c3d8ffc5ba88c5033` |
| [SMF5.0CA](../reference/pdfs/C19077498.pdf) | [Manufacturer/supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312041000_hongjiacheng-SMF5-0CA_C19077498.pdf) | `c8f137df222c1c36b0356096e10d601434b420c2f65407c222229dbd725df74a` |
| [62684-402100ALF](../reference/pdfs/C2931360.pdf) | [Manufacturer/supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2201201700_Amphenol-ICC-62684-402100ALF_C2931360.pdf) | `db5cce2a20ec2c04c545dfe7316ac220e8210442845547f6cad3ed8a1697fea3` |
| [HS280S010B](../reference/pdfs/C2939938.pdf) | [Manufacturer/supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2401291705_HS-HS280S010B_C2939938.pdf) | `96811636f099962f48140096ebce2ac228e62cb0e421ca2ecea0bd7f14bad168` |
| [TS-1101-C-W](../reference/pdfs/C318938.pdf) | [Manufacturer/supplier PDF](https://www.lcsc.com/datasheet/lcsc_datasheet_2002271735_XKB-Connection-TS-1101-C-W_C318938.pdf) | `e7d601aea4c19a0afadd6818dda3136957abf0371b422559d55dd991920e8151` |
| [7312P0225A13LF](../reference/pdfs/C5417011.pdf) | Original URL not recorded | `12a17d19f8a76b04b896529b786c3208bc36fdb336a24522f9b309150fb0dd2f` |
| [TYPE-C 6P(073)](../reference/pdfs/C668623.pdf) | [Manufacturer/supplier PDF](https://www.lcsc.com/datasheet/lcsc_datasheet_2006181823_SHOU-HAN-TYPE-C-6P-073_C668623.pdf) | `98756b6026c3ad625679d384f382df5910246c3bf98a7d85897eb9f5d603b504` |
| [Luckfox-Pico-Mini](../reference/pdfs/Luckfox-Pico-Mini.pdf) | Original URL not recorded | `67d8730d4d636df3dd4d8df2ac8d0c1615a35092b8cdcdd11e98d76b2934461d` |
| [SEC1210-DS00001561D](../reference/pdfs/SEC1210-DS00001561D.pdf) | [Manufacturer/supplier PDF](https://www.microchip.com/content/dam/mchp/documents/UNG/ProductDocuments/DataSheets/00001561D.pdf) | `f3e8c11a747c3d15fe684662938342763b81943b84ff9c41fe3bf6255255515d` |
| [Waveshare Pico-ResTouch-LCD-2.8 schematic](../reference/pdfs/Waveshare-Pico-ResTouch-LCD-2.8-Schematic.pdf) | [Manufacturer/supplier PDF](https://files.waveshare.com/upload/d/dc/Pico-ResTouch-LCD-2.8_Sch.pdf) | `c4dd50fdb36ec299424a879c321e91a6f5ea74bf296ea9fffb3feccd0471c1e2` |
| [HOTHMI HTM-TFT028A16-SPI module](../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf) | [Manufacturer/supplier PDF](https://www.hothmi.com/wp-content/uploads/2026/08/2.8-inch-display-high-brightness-st7789-spi.pdf) | `f83b8c12452eb9bd504ea3b6e7fac35ae2564f12ed56d7fd8f638771509fe002` |
| [Diodes AP2112 regulator](../reference/pdfs/Diodes-AP2112.pdf) | [Manufacturer/supplier PDF](https://www.diodes.com/datasheet/download/AP2112.pdf) | `ef8d376f2ec356e29172eb9e053819a0ebdcc576dba7fc9ab0505c568427920f` |

The [pill guide](LCD-MODULE-VARIANT.md) states the selected module, electrical limits and drawing discrepancies. The [standard FPC BOM](BOM.md) records its separate panel qualification. Update the JSON index when retaining/replacing documents.

Self-assembly indicator reference: [Kingbright APT2012LZGCK](../reference/pdfs/Kingbright-APT2012LZGCK.pdf), [manufacturer source](https://www.kingbrightusa.com/images/catalog/SPEC/APT2012LZGCK.pdf), SHA-256 `e0ef6d7073f40ce3a3db6a61ccb87fafd056bf00026942ada2fbe177b1fc49a8`.

Mechanical substitution reference: [C&K PTS636 tactile switches](../reference/pdfs/CK-PTS636.pdf), [Manufacturer datasheet, archived 7 October 2020 edition, retained from LCSC](https://datasheet.lcsc.com/datasheet/pdf/229e2204c94be8eac226511395a363de.pdf?productCode=C2689642), SHA-256 `2015aeeef741ee7eff1ec5bdb3c2229233d4b0605be9a8cfe73bff851ef5dceb`.

Mechanical substitution reference: [GCT USB4125 mechanical drawing](../reference/pdfs/GCT-USB4125.pdf), [Manufacturer drawing rev A6, 20 November 2025](https://www.gct.co/files/drawings/usb4125.pdf), SHA-256 `ea33e0b40545e545bf698cbac3bb1c0f5a3fc7ca6b5b7fda83a63134d4affaa7`.

Mechanical substitution reference: [GCT USB4135 mechanical drawing](../reference/pdfs/GCT-USB4135.pdf), [Manufacturer drawing rev A2, 13 September 2024](https://www.gct.co/files/drawings/usb4135.pdf), SHA-256 `96941ffad52b3ee61a6388db4229b02cba07e2a47bb2bf9f94a3d751dfc20ac4`.
