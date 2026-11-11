# Current 0.0.12-dev order-review status

The four-layer working pill revision has **44 factory SMT placements / 18 SKUs**,
including nine Keystone 5015 / C2906768 service points. The four new bracket
holes are optional M2.5 hardware anchors; modules/headers/screws remain customer
assembly. J302 is removed. Use the freshly generated order ZIP; all 0.0.9 and
0.0.7 release/preview files below are historical.

**First-article fabrication and assembly review package prepared.** Submit the
matched files for sourcing, DFM and a prototype quote. Physical first-article
results are acceptance work **after delivery**, before repeat builds; they are
not a prerequisite to ordering the prototypes. Checkout still requires supplier
confirmation of exact parts, tooling and placement.

The 2026-11-09 public catalog snapshot reports:

| Selected component | LCSC | Per board | Standard-assembly stock |
|---|---|---:|---:|
| Keystone 5015 | C2906768 | 8 | 77,077 |
| C&K PTS636SK25SMTRLFS | C2689642 | 8 | 0 |
| Microchip SEC1210/PV-UR2 | C633309 | 1 | 0 |
| Amphenol 7312P0225A13LF | C5417011 | 1 | 0 |

These are dated public fields, not a stock reservation. Overseas inventory is
not confirmed assembly allocation. Resolve exact-MPN sourcing and attrition with
JLC before paying or substituting parts. Supplier placement/DFM review must use
the current board hash and matched compensated CPL, including all nine loops.
Confirm the nominal 1.6 mm four-layer stackup. Native ERC/DRC and pinout checks
are software gates; first-article fit, power/thermal/rail tests, correct carrier
firmware, display operation and smartcard transactions remain required.

Rebuild with `mise run variant:lcd:service:review` and
`mise run variant:lcd:fab`. The generated `manufacturing/readiness.json` records
current stock blockers and file hashes. No order or account change is implied.

## Historical 0.0.9 artwork review record

# PCB first-article order readiness

The target is the **main eight-pin pill carrier, 0.0.9-dev**, with added
`denver.space` artwork and the existing always-on backlight topology. This is an
artwork revision of `hardware/`, not promotion of the separate
`variants/lcd-backlight-pwm/` candidate. The target remains 35 fitted SMT pieces
across 17 supplier SKUs; LCD, Luckfox, camera, headers and supports are separate.

**Status: stock review required for five assembled boards.** This document tracks the regeneration and assembler
review gates. A new PCB hash invalidates the old package/preview association even
when every electrical item is preserved. No order, payment or newly approved
supplier placement is implied.

## Current local regeneration result

The final artwork board SHA-256 is
`59abf9a976ff8960a9f1f4c37245fe000f67a4bdce78db8634145cc372b2ace5`.
`branding-audit.json` proves the exact protected PCB tree matches the preceding
board: all 60 footprints/200 pads, 538 tracks, 234 vias, zones, edge geometry,
net assignments and export setup remain unchanged. Only permitted top-level
silkscreen artwork differs.

Native ERC/DRC, unconnected and schematic-parity counts are zero. The refreshed
geometry gate verifies 22 portable models and the retained manufacturer land
patterns. Matched Gerber/drill/BOM/CPL generation passes at 35 placements across
17 SKUs; the three compensated positions remain the same. Fabrication screening
and first-article process reports now carry this board hash. The power-budget
report remains a planning calculation, not new physical evidence.

This closes local file/geometry regeneration gates. A new supplier upload/quote,
placement/DFM approval, stock reservation and physical first article remain open.

## Starting evidence

The pre-artwork 0.0.7 board has SHA-256
`b4eb7a7cef3f026bfc332a19980727a165de9ea826e4eb25dcc68e2c458004b7`.
Before the artwork edit, this hash matched the native check report, fabrication
capability report, first-article process report, assembly-fit report and supplier
placement-correction record. Its Gerber ZIP, BOM, compensated CPL and population
CSV matched the recorded file hashes. The BOM and CPL each identified exactly
35 fitted references across 17 BOM lines: 24 bottom-side placements and 11 top.

Those are file-consistency and geometry results, not evidence of powered hardware.
The saved 0.0.7 supplier preview/quote is historical. Stock snapshots are dated,
unreserved observations; they do not establish current orderability or pricing.
Older `feasibility-audit.json` and `power-input-review.json` deliberately retain
their original board identities and must not be relabeled as new audits.

## Current supplier stock blocker

An exact-MPN lookup of all 17 selected SKUs on **2026-11-01 UTC** found the
following public standard-assembly fields. The socket record was checked at
01:17:44 UTC; these are dated observations, not a reservation. Proposed quantity remains **five**; no lower assembled
quantity has been silently substituted.

| Part | Installed requirement for five | `canPresaleNumber` | `overseasStockCount` | Decision |
|---|---:|---:|---:|---|
| C5417011 / 7312P0225A13LF smartcard socket | 5 | 2 | 9 | Short by 3 before attrition; supplier sourcing confirmation required |
| C2689642 / PTS636SK25SMTRLFS switches | 40 | 46 | 2,377 | Installed count covered; final attrition/loading requirements unconfirmed |
| C633309 / SEC1210/PV-UR2 | 5 | 46 | 65 | Installed count covered; final assembly sourcing unconfirmed |

`canPresaleNumber` and `overseasStockCount` describe different supplier fields.
Do not sum them or assume overseas inventory is available to this assembly job.
Raw minimum/patch/loss fields are retained in `stock-for-five.json`; their final
application to the actual quote must be confirmed by JLC.

**Five fully assembled boards are not checkout-ready until JLC can source enough
exact sockets and confirms attrition.** Two visible sockets are not a promise of
two assembled units. Manufacturing exports remain useful and internally matched
despite this stock shortage. No substitute part or footprint change is proposed.

## Gates before submitting the new package

| Gate | Required action |
|---|---|
| Exact target | Record final 0.0.9 PCB hash and prove footprint/pad poses, nets, tracks, vias, outline and manufacturing datum are unchanged by artwork |
| Native checks | Re-run schematic ERC, board DRC, connectivity/parity, pinout and mechanical gates; resolve findings rather than transferring old pass labels |
| Supplier compensation | Re-review the three existing corrections against the preserved geometry and identities, re-pin the board hash, and reset the new-preview claim |
| Matched outputs | Export Gerbers/drills and BOM/CPL from that same board; confirm 35 pieces/17 lines and exact reference/MPN agreement |
| Artwork | Inspect top/bottom at fabrication scale for mask/pad overlap, clipping, readability, polarity labels and connector access |
| New supplier preview | Upload the new Gerbers, BOM and compensated CPL together; inspect orientations and model origins without reapplying old manual moves |
| Factory preparation | Obtain final DFM/placement review and rail/fiducial/tooling/stencil plan for double-sided assembly of this capsule |
| Parts | Confirm exact selected MPNs, stock/attrition and all matched rows; explicitly include USB J301 if the uploader leaves it unchecked |

The current exporters intentionally reject a changed PCB until placement
compensation has been reviewed. Do not bypass that guard merely to obtain files.

## Placement details to preserve

The CPL datum is `(50, 130)` mm in the native board. Exported X is native X minus
50; exported Y is 130 minus native Y. Bottom X is not mirrored in the CSV.

| Ref | Exact selected part | Supplier compensation from native |
|---|---|---|
| J301 | GCT USB4125-GF-A-0190 / C5246813 | +0.84 mm Y, +180° |
| J601 | Amphenol 7312P0225A13LF / C5417011 | −0.8 mm X, +180° |
| U601 | Microchip SEC1210/PV-UR2 / C633309 | +180° |

The generated upload CPL already contains these changes. The diagnostic native
CPL does not. Do not apply a blanket bottom-side rotation: the green LED D302
needs no extra rotation, D301 is bidirectional, and U701 now uses its native bottom-side position/rotation. The prior top-side regulator preview is superseded.
Confirm USB mouth/tails/stakes, all numbered smartcard contacts and SEC1210 pin 1
in the new preview. Retain the old preview as explicitly historical evidence.

## Saved manufacturer checks and physical limits

- **USB:** the saved [GCT drawing](../reference/pdfs/GCT-USB4125.pdf), page 1,
  identifies suffix `0190` as 1.90 mm shell stakes and provides the recommended
  six-contact land/slot geometry. This power-only connector has CC1/CC2, VBUS
  and GND contacts; its connector current rating is not the board's thermal or
  USB-negotiated supply budget. Review solder fill and the 1.6 mm PCB stack.
- **Switches:** [C&K PTS636](../reference/pdfs/CK-PTS636.pdf) lists
  `PTS636 SK25 SMTR LFS` as 2.5 mm high with G-type terminals and 250 gf nominal
  actuation. Retain the selected exact part and matching footprint; a similar
  family name does not prove the plunger height or terminal geometry.
- **Controller:** [SEC1210 datasheet](../reference/pdfs/SEC1210-DS00001561D.pdf)
  specifies the 24-pin QFN and grounded thermal slug. Preserve the `/PV-UR2`
  purchase suffix. The hidden pad needs an assembly/inspection plan; electrical
  functionality alone does not inspect its solder joint.
- **LCD supply:** [AP2112](../reference/pdfs/Diodes-AP2112.pdf) specifies 600 mA
  output capability and a SOT25 thermal figure under its stated conditions.
  That is not a guarantee of 600 mA at this board's voltage drop or enclosure
  temperature. The retained planning calculation reaches about 119 °C at 200 mA
  using 5.25 V input, 3.1 V output, 40 °C ambient and 184 °C/W; those assumptions
  are not a measured junction temperature.
- **LCD:** [HOTHMI drawing](../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf)
  specifies the 88 × 53.3 mm module, eight-pin J1 interface and nominal 3.3 V
  operation, with operating supply limits of 3.1–3.6 V. Its 120 mA typical
  backlight figure is not the whole module current. BL_E high enables and low
  disables the backlight; always-on is the selected main-board default.

The existing geometry gate checks manufacturer land dimensions and portable
model hashes. Drawing-derived envelopes are still approximations, not measured
production assemblies. The LCD drawing's stack sums to 10.9 mm while other
product prose gives 7.7 mm; verify the purchased revision physically.

## Headers, power and first article

**Before carrier power-up, use a reviewed carrier-profile image.** The working
`base-fork` bench image drives GPIO56/57 as LCD outputs, but those are Left/Up
switch nets on this PCB. Pressing a switch can ground a driven output. See the
included [PCB/software compatibility audit](PCB-SOFTWARE-COMPATIBILITY.md) for
the exact mapping and LCD/reader configuration; no PCB rewiring is indicated.

Exact female/male header purchase MPNs and their contact-depth tolerances remain
unselected. The CAD stack assumes 8.5 mm female housings, 2.54 mm pitch, 12 mm LCD
spacers, approximately 5.04 mm LCD pin insertion and 6 mm Luckfox insertion.
Those dimensions need a dry fit with the actual module headers before enclosing
or repeating assemblies. Customer header work is not included in the SMT BOM.

J302 is an optional customer-fitted 2.54 mm 1×2 header: pin 1 is regulated +5 V,
pin 2 GND. Use one supply source at a time. The design has no input source
isolation or reverse-polarity protection. USB-C is a 5 V power input here; do not
infer USB data support or higher-voltage PD negotiation from the connector.

A first article must establish LCD total current, LCD_3V3 startup/load-transient
limits, regulator temperature at intended ambient/enclosure conditions, stable
camera/display operation and reader behavior. The QFN paste pattern includes a
central through-via: review wicking/voiding, stencil thickness and hidden-pad
inspection. Do not remove that via casually; the retained removal experiment
caused a native connectivity regression.

Order prototype quantities only after the file/factory gates above. Validate one
physical unit before populating repeats. Software boot/QR results from the
240×240 bench setup do not qualify this carrier, LCD or smartcard circuitry.

## Regenerate after the final artwork edit

First review/re-pin the placement-correction board hash and new package revision;
then run from the repository root:

```sh
mise run variant:lcd:check
mise run variant:lcd:pinouts
mise run variant:lcd:models
mise run variant:lcd:fab
mise run variant:lcd:fab-audit
mise exec -- uv run python scripts/audit-first-article.py
mise run variant:lcd:power-budget
mise run variant:lcd:review
mise run variant:lcd:faces
mise run variant:lcd:package
mise run variant:lcd:stack
```

`package` must precede `stack`, which checks the exported GLB against the package
manifest. After refreshed fit/check metadata is included in portable sources,
run `variant:lcd:package` again so the final ZIP hashes cover those records.
Do not publish a stale manifest copied from the previous board revision.

If distributing fit/case assets, also regenerate the hardware mesh cache,
case-aligned fit kit, printable mockup and enclosure fit checks using their mise
commands. Recheck the final package manifest after that sequence. Rebuild the
static website from the new release metadata and review both PCB faces before
uploading the new order bundle. Uploading the files and accepting the assembler's
new preview remain separate from these local regeneration commands.
