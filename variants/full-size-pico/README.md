# Full-size Luckfox Pico / Pico Plus prototype

The full-size Pico connects directly to the existing 160 × 70 mm carrier through
**two XKB X6511WVS-20H-C60D48R2 SMT male headers (JLCPCB C2883777)**. Two Harwin
M20-7822042 female sockets are soldered onto the underside of an **unheadered**
Pico or Pico Plus. There is no adapter PCB. The module's component side and
microSD slot face outward.

The selected factory headers replace the earlier Harwin SMT socket study,
which had insufficient JLCPCB stock. The old board is retained in
`history/harwin-socket-study.kicad_pcb` for provenance only; do not order it.

The current native schematic/layout is in `kicad/`. Native ERC, DRC, connectivity
and schematic parity pass with zero findings or exclusions. The source audit
preserves the main Mini board, its front artwork, outline, rules and all retained
part nets. C701, JP701, JP702 and TP905 have documented local moves.

## Ten-board manufacturing package

**Ten prototype carriers have been ordered.** Final factory review and physical bring-up remain open.

Read [manufacturing/ORDER.md](manufacturing/ORDER.md) for the matching build settings.
The matched BOM/CPL contain **46 factory placements, 19 catalog lines**: the
previous 44 components plus two SMT headers. J203 and J204 are explicit physical
assembly entries expanded from the logical native U202 interface; their exact
contact mapping and centers are in `manufacturing/header-placement-map.json`.

JLCPCB's fresh catalog snapshot showed 73 C2883777 headers: 20 installed parts
for ten boards, with a provisional six spares. Stock is not reserved. The
ten smartcard sockets were already pre-ordered into the JLCPCB parts library.
The saved assembly quote selected those sockets and the SEC1210 chips from My Parts.
Final factory production/placement approval and physical first-unit checks remain open.

## Mechanical interface

The XKB drawing specifies 2.2 × 1.27 mm alternating SMT lands, 2.54 mm contact
pitch and 5.8 mm overall land span. The native GLB audit checks both bottom-side
R2 tail patterns and all 40 contact positions. Header rows remain 17.78 mm apart.

The male insulator top is nominally 3.14 mm above the carrier. The 8.5 mm module
sockets place the module underside at 11.64 mm. Nominal maximum rear height is
16.74 mm for Pico and 26.04 mm for Plus. These are drawing/model dimensions,
not a physically verified mating assembly. The sockets are on the module;
the JLCPCB BOM populates only the SMT male headers on the carrier.

The Pico is 21 × 51 mm and Plus is 21 × 72 mm. The Plus manufacturer model's
Ethernet jack mouth projects about 4.4 mm beyond the carrier edge in this
placement. Its plug, boot, latch access, enclosure and insertion-load support
still need physical verification; edge placement was not a requirement.
The current enclosure and full-size-module firmware are not qualified.

## Display pinouts and manufacturer documents

See the [display and host pinout review](PINOUT-REVIEW.md) for the exact
HOTHMI, Waveshare **2inch LCD Module / SKU 17344**, ILI9341 and Pico/Plus
mappings. The Waveshare section links the retained official schematic,
dimension drawing, rear connector photograph and source/hash record.
Its eight signal assignments match J701; its smaller mounting pattern and
PH2.0 cable connection require a separate physical mounting/wiring review.

## Review and provenance

`source.json` records vendor revisions/hashes and the Mini-to-full pin map;
`audit.json`, `study-status.json` and `manufacturing/` record the current checks.
Local symbol/footprint/model snapshots retain their upstream attribution.
Nominal locally built STEP models are named `*-nominal.step`; they are not
manufacturer-certified CAD.

```sh
mise run variant:pico-full:check
mise run variant:pico-full:build
mise run variant:pico-full:fab
mise run variant:pico-full:open
```

Native KiCad is authoritative. The isolated extracted/compiled tscircuit data
is experimental and does not replace the fabrication files. No website release,
component purchase or PCB order has been placed by this work.
