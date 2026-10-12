# Saved reference PDFs

All nine downloaded supplier/manufacturer reference PDFs are retained in `reference/pdfs/`. They are tracked through Git LFS by the project `.gitattributes`. Generated KiCad schematic PDFs remain in `dist/kicad/` and can be regenerated. The private build SDK checkout is excluded from this reference archive.

The JSON index records byte sizes and SHA-256 hashes. These identify the retained documents; they do not certify that a supplier specification is correct. Missing original download provenance is marked explicitly.

| Document | Source | SHA-256 |
|---|---|---|
| [AO3400A](../reference/pdfs/AO3400A.pdf) | Original URL not recorded | `9c60d0b6c1ddc7609a4b788a91181468d8ffe6c3e9ba425c3d8ffc5ba88c5033` |
| [SMF5.0CA](../reference/pdfs/C19077498.pdf) | [Supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312041000_hongjiacheng-SMF5-0CA_C19077498.pdf) | `c8f137df222c1c36b0356096e10d601434b420c2f65407c222229dbd725df74a` |
| [62684-402100ALF](../reference/pdfs/C2931360.pdf) | [Supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2201201700_Amphenol-ICC-62684-402100ALF_C2931360.pdf) | `db5cce2a20ec2c04c545dfe7316ac220e8210442845547f6cad3ed8a1697fea3` |
| [HS280S010B](../reference/pdfs/C2939938.pdf) | [Supplier PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2401291705_HS-HS280S010B_C2939938.pdf) | `96811636f099962f48140096ebce2ac228e62cb0e421ca2ecea0bd7f14bad168` |
| [TS-1101-C-W](../reference/pdfs/C318938.pdf) | [Supplier PDF](https://www.lcsc.com/datasheet/lcsc_datasheet_2002271735_XKB-Connection-TS-1101-C-W_C318938.pdf) | `e7d601aea4c19a0afadd6818dda3136957abf0371b422559d55dd991920e8151` |
| [7312P0225A13LF](../reference/pdfs/C5417011.pdf) | Original URL not recorded | `12a17d19f8a76b04b896529b786c3208bc36fdb336a24522f9b309150fb0dd2f` |
| [TYPE-C 6P(073)](../reference/pdfs/C668623.pdf) | [Supplier PDF](https://www.lcsc.com/datasheet/lcsc_datasheet_2006181823_SHOU-HAN-TYPE-C-6P-073_C668623.pdf) | `98756b6026c3ad625679d384f382df5910246c3bf98a7d85897eb9f5d603b504` |
| [Luckfox-Pico-Mini](../reference/pdfs/Luckfox-Pico-Mini.pdf) | Original URL not recorded | `67d8730d4d636df3dd4d8df2ac8d0c1615a35092b8cdcdd11e98d76b2934461d` |
| [SEC1210-DS00001561D](../reference/pdfs/SEC1210-DS00001561D.pdf) | [Supplier PDF](https://www.microchip.com/content/dam/mchp/documents/UNG/ProductDocuments/DataSheets/00001561D.pdf) | `f3e8c11a747c3d15fe684662938342763b81943b84ff9c41fe3bf6255255515d` |

LCD qualification is recorded in [BOM.md](BOM.md). The downloaded HS280S010B is rejected as a drop-in; saving a datasheet does not select its part for assembly.

Future supplier downloads through `scripts/download-review-datasheets.py` go to the same PDF folder. Update `pdf-references.json` and this index when replacing or adding documents.
