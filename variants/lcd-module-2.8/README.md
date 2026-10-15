# Modular 2.8-inch ShieldSigner — 0.0.3-dev

Open `kicad/SeedSigner-Plus-smartcard-pico.kicad_pro`. The inherited project basename preserves hierarchical annotation paths; this is a separate native project. See [design and wiring](../../docs/LCD-MODULE-VARIANT.md), [customer assembly](../../docs/MODULAR-ASSEMBLY.md) and [manufacturing instructions](manufacturing/README.md).

The PCB has 58 footprints: 32 SMT assembly placements, customer header/module/support positions, copper jumpers and DNP bare-panel lands. All four mode straps in the two inherited courtyard exclusions are DNP. JLCPCB receives 32 placements across 16 sourced catalog lines. Customers install only ordinary headers and modules; the smartcard QFN/socket and USB contacts are assembled by JLCPCB.

Run `mise run variant:lcd:fab` for independent native checks, mechanical/land-pattern/model assertions and matched Gerbers/BOM/CPL. Run `mise run variant:lcd:review` for assembly PNGs and STEP/GLB outputs. Manufacturing outputs use the auxiliary origin (50,130) mm for every file. The primary purchasing files are under `manufacturing/`, not the standard carrier directory.

The 17 local STEP models include manufacturer/supplier data with a hash/provenance index and clearly labeled card-socket/spacer envelopes. `mechanical.json` records the modeled header stack and four manufacturer-derived mounting centers. `git lfs pull` hydrates model/PDF content in a fresh clone.

This is a prototype quote/review package, not a claim of manufactured or electrically qualified hardware. First-article header fit, firmware/display behavior, smartcard transactions and assembler placement review remain to be performed. Source/native checks report their exact scope.
