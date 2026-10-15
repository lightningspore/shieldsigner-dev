# ShieldSigner eight-pin pill — 0.0.4-dev

Open `kicad/SeedSigner-Plus-smartcard-pico.kicad_pro`. The inherited basename preserves hierarchical annotation paths; this is an independent native project. See [design and exact wiring](../../docs/LCD-MODULE-VARIANT.md), [customer assembly](../../docs/MODULAR-ASSEMBLY.md) and [quote instructions](manufacturing/README.md).

The **160×70 mm capsule** centers a 2.8-inch HOTHMI HTM-TFT028A16-SPI between the controls. A single eight-pin 2.54 mm socket follows the user's existing Luckfox carrier numbering. There is no Pico-format LCD connector or projecting rectangular bay. A dedicated AP2112K-3.3 supplies LCD_3V3 independently of the Luckfox's 3.3 V output.

There are **47 footprints**: 35 SMT placements, J701/U202 customer module/header positions, four supports and six copper jumpers. The old bare-panel parts and J302 are removed. Native ERC/DRC/connectivity/parity pass with zero exclusions. JLCPCB receives 35 placements across 17 catalog lines. Customers install ordinary headers, modules and screws.

Run `mise run variant:lcd:fab` for native/model/footprint checks and matched Gerbers/BOM/CPL. `variant:lcd:review` renders both sides and exports assembly STEP/GLB; `variant:lcd:package` bundles the portable project and pins release hashes. Manufacturing uses the shared auxiliary origin (50,130) mm. Standard carrier files do not apply.

Nineteen local STEP models have source/hash records. LCD, socket and threadless supports are dimensional envelopes. `mechanical.json` records the stack, mounting centers and drawing discrepancies; `header-map.json` records both numbering conventions. Run `git lfs pull` in a fresh checkout.

This is a prototype quote/review design, not a physically qualified signer. Assembler preview/DFM, purchased-module fit, rail/thermal measurements, firmware/display behavior, smartcard transactions and enclosure fit remain to be tested.
