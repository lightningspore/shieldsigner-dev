# Optional self-assembly with DigiKey parts

**JLCPCB remains the primary route:** order the existing assembled pill carrier, then fit the headers and modules using the [assembly guide](MODULAR-ASSEMBLY.md). Revision 0.0.6-dev adds shared-supplier switches and USB-C. Use matching revision files.

For self-assembly of the revised 0.0.6-dev board, use the separate [DigiKey sourcing table](../variants/lcd-module-2.8/self-assembly/BOM-DIGIKEY.md) and [purchase CSV](../variants/lcd-module-2.8/self-assembly/bom-digikey.csv). The CSV gives exact cut-tape/tray order codes, reference designators, electrical specifications, original JLC identities, and installed quantities for one or five boards. It is a shopping list, not a JLC upload file.

## What is covered

| Population | Self-assembly status |
|---|---|
| 11 capacitors, 10 resistors, indicator LED and TVS | All 23 pieces / 12 lines have selected DigiKey parts using the existing footprints |
| SEC1210/PV-UR2, Amphenol card socket and AP2112K regulator | Exact original MPNs listed at DigiKey; three more pieces / three lines |
| Eight C&K PTS636 switches and GCT USB4125-GF-A-0190 connector | Exact MPNs shared by JLCPCB and DigiKey; revised native lands |
| LCD, camera and Luckfox | Outside this supplier list |
| Customer headers, fasteners, card, microSD and supply | Follow the existing shopping/assembly and enclosure specifications |

**All 35 fitted SMT pieces are listed at DigiKey across 17 lines.** The remaining-parts CSV now contains only its header. The two new MPNs require revision 0.0.6-dev; do not fit them to the prior board by assumption.

## Commodity substitutions

- Resistors retain 0805 dimensions, resistance, ±1% tolerance and 125 mW rating. Bourns supplies the 5.1 kΩ USB-C pull-downs because the comparable Yageo cut-tape part was out of stock.
- Capacitors retain 0805 dimensions, capacitance, voltage rating, tolerance and dielectric. The 33 pF and 100 nF parts retain their exact original MPNs; the 10 µF and 1 µF selections use stocked equivalents.
- The Kingbright green indicator uses the existing 0805 lands and 560 Ω resistor. Match its cathode to native K/pad 1. Brightness differs by device; the illustrative current is about 4.2 mA at 5 V and typical forward voltage.
- Littelfuse SMF5.0CA retains the bidirectional 5 V stand-off, 200 W pulse class and SOD-123F package. It is transient suppression, not an overvoltage disconnect.

Each selected part links to its DigiKey page in the sourcing table. Stock was checked on **2026-10-17** and is not reserved. Prototype effective capacitance, LED brightness and powered behavior remain bench measurements, as with the JLC population.

## Assembly process

Self-assembly of the whole carrier includes a **24-pin exposed-pad QFN**, SMT card socket and two-sided population. A controlled paste/reflow process and inspection are appropriate; this requires more equipment and technique than the header soldering needed after JLC assembly. Use native paste, silk and placement information with the original reference designators. Replacements keep their existing footprints and net assignments; confirm LED polarity and IC pin 1 before heating.

After assembly, follow the [staged rail and module checks](MODULAR-ASSEMBLY.md), then [reader bring-up](BRINGUP.md). Use C&K PTS636SK25SMTR LFS and GCT USB4125-GF-A-0190 on revision 0.0.6-dev. USB4135 is not selected.

Use the [enclosure hardware list](ENCLOSURE.md) when printing the case. M2.5 thread and spacer length alone do not establish clearance: a 5 mm-across-flats hex spacer has approximately 5.77 mm across corners and does not fit a 5 mm circular envelope.

See the [dimensioned switch and USB-C comparison](MECHANICAL-SUBSTITUTIONS.md) for the candidate land patterns, slot mismatch and button-height tolerance findings. The selected USB4125 and C&K switch have dedicated revised footprints. Physical fit remains unqualified.

## Bottom-only outsourced assembly option

An intermediate route uses the **same 0.0.6-dev PCB**: an assembler fits the 24 bottom-side pieces (15 catalog lines), including U601, J601 and J301; you fit the eight switches, U701 and C701/C702 on top, then headers. This leaves 11 top-side SMT pieces for local hand soldering. It is more work than buying a complete PCBA, but avoids personally reflowing/inspecting the QFN and avoids an obligatory two-sided outsourced assembly process.

Run `mise run variant:lcd:bottom-quote` to produce `dist/lcd-module-2.8/bottom-only/shieldsigner-bottom-only-quote.zip`. It includes the release-pinned full Gerber ZIP, reduced bottom-only BOM/CPL, separate customer-top population and an itemized quote-request JSON. The task checks PCB/parent-file hashes, native sides, coordinate datum and exact BOM/CPL reference equality. The [option record](../variants/lcd-module-2.8/manufacturing/bottom-only-option.json) lists questions and stock observations. Do not substitute this BOM/CPL into a full-assembly order by accident.

The 2026-10-22 JLC snapshot covers one board's installed bottom-side quantities; it is neither reserved stock nor allowance for assembler attrition/minimums. The out-of-stock JLC switches are outside this assembly scope. Two top-side 10 µF capacitors still need sourcing; a partial PCBA does not solve that customer-parts requirement.

Request **one populated first article**, itemized setup/minimum charges, QFN via/paste/inspection review and USB shell-stake solder-fill confirmation. Ask the supplier to state any minimum assembled quantity separately. Do not populate repeat boards before acceptance. No request has been sent, no quote obtained and no order placed; whether this route saves money remains unproven.

## One-board assembly process review

Build **one first article**, then decide whether to populate two more. The [first-article release gate](MODULAR-ASSEMBLY.md#first-article-before-repeat-builds) replaces a batch-size assumption. A fabricator's bare-board minimum can stay unpopulated.

A candidate process is one bottom-side reflow (24 parts), followed by local hand soldering of the top-side eight switches, U701 and C701/C702 (11 parts), then ordinary module headers. This avoids an obligatory second full-board reflow with the smartcard socket hanging underneath. Verify iron access and the exact switch/socket/component heat limits before adopting it; this is a process proposal, not a proven assembly recipe. Whole-board hotplate heating after the bottom is populated needs separate clearance/temperature review.

`mise run variant:lcd:first-article` measures the actual native geometry into [the process report](../variants/lcd-module-2.8/manufacturing/first-article-process.json). On the current board:

- U601's 3.4 × 3.4 mm ground pad has four rounded paste windows, giving approximately **63.1% paste coverage** after corner rounding. Copper area alone is not deposited solder volume; stencil thickness and paste transfer matter.
- A **0.3 mm drill / 0.6 mm diameter ground via** remains at its center. No filled/capped manufacturing process is established. Review solder wicking and hidden-pad voiding; opposite-side solder-mask tenting is not a filled via. Do not assume a functional UART proves a good exposed-pad joint. An isolated KiCad 10.0.7 trial removing only this via creates one unconnected item after zone refill, compared with zero on the reference board; [the experiment record](../variants/lcd-module-2.8/manufacturing/via-removal-experiment.json) rejects simple deletion. The working PCB remains unchanged.
- **USB4125-GF-A-0190 has 1.9 mm shell stakes.** Inspect insertion and solder wetting/fill on the 1.6 mm PCB.

[Microchip AN2089](../reference/pdfs/Microchip-AN2089-QFN-assembly.pdf), especially pages 3–5, explains generic exposed-pad, stencil, measured reflow-profile and moisture-handling considerations. It is not SEC1210-specific process approval. Record paste/alloy, stencil thickness, measured component temperatures, moisture-label handling and inspection/rework method with the first article. No universal oven setpoint is prescribed here.

An iron alone does not establish a process for U601's underside pad. Include any missing reflow/rework/inspection equipment or outsourced assembly in the first-article budget before comparing the $19.16 component-only baseline with PCBA pricing.

## Available DigiKey capacitor

Use **TDK C2012X5R1E106K125AB**, DigiKey [445-5984-1-ND](https://www.digikey.com/en/products/detail/tdk/C2012X5R1E106K125AB/2443462), for C201, C302, C701 and C702. It matches the original 10 µF, 25 V, ±10%, X5R ratings and standard 0805 footprint; maximum height is 1.45 mm, matching the original envelope. [TDK specifications](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012X5R1E106K125AB) confirm the dimensions and ratings. No PCB changes or separate supplier are needed. Native/JLC selection remains unchanged.

DigiKey showed 1,000 available on 2026-10-22: $0.34 at one, $0.202 at ten, $0.1305 at 100, $0.10202 at 500. This is an available small-order option, not a lowest-cost production selection. Normal first-article supply startup/transient checks still apply. See the [costs page](/costs/) for current totals and exclusions.

## Live bare-board calculator baseline

The 2026-10-22 [JLC calculator observation](../variants/lcd-module-2.8/manufacturing/jlc-calculator-estimate.json) used **five bare 160 × 70 mm, two-layer, 1.6 mm, green FR4 / 1 oz boards**, without uploading files. It showed **$10.80 lead-free HASL** or **$27.30 ENIG**, before freight. A US Global Standard Direct Line estimate was **$9.77, 8–13 business days**, with package/value limits; faster courier estimates were higher. These are dimensional estimates, not reviewed manufacturing quotes.

Using that slower shipping estimate and the DigiKey component/module subtotal, the identified partial cash outlay is **$76.62 for lead-free HASL** or **$93.12 for ENIG**. This counts the entire five-board purchase against the first article; it does not pretend five working units exist. It still excludes assembly, stencil/consumables, the other suppliers' freight/taxes, headers/hardware, microSD/card/case, missing tools and labor.

The optional epoxy-filled/capped-via setting increased the ENIG bare-board estimate to **$83.15**, including a required plating upgrade. It is not established as necessary, and the low-cost freight option's goods-value limit would no longer apply. Ask the assembler to review the QFN process before choosing this expensive option; the UI offering it does not establish factory acceptance of our two-layer via-in-pad design. Assembly pricing in the live form requires a Gerber upload; upload approval is pending. Nothing has been uploaded or ordered.

## Cost and button setup

The original $19.16 component estimate is retained as a 2026-10-17 historical snapshot. The 2026-10-22 public-page refresh gives the following **component-only baskets**, calculated by `mise run bom:first-article-budget`:

| Basket | Parts subtotal USD | Meaning |
|---|---:|---|
| One first article | $17.58 | Installed quantities, allowing cheaper quantity-break purchases |
| One first article with illustrative spares | $33.47 | At least 10/two extras per passive line, two extra switches, one extra per other fitted line |
| Three boards | $45.43 | Shared quantity breaks, no planned assembly spares; only populate repeats after acceptance |

The capacitor substitution above resolves the known unavailable line. Stock observations remain dated and must be checked at checkout. The revised USB4125-GF-A-0190 cut-tape observation is $0.61; Digi-Reel adds a reeling fee.

[Current pricing and per-line source URLs](../variants/lcd-module-2.8/self-assembly/pricing-current.json) and [the first-article budget](../variants/lcd-module-2.8/self-assembly/first-article-budget.json) retain purchase quantities, packaging, spares and availability. The historical native/JLC part selections are unchanged. The [capacitor review](../variants/lcd-module-2.8/self-assembly/capacitor-review.json) records the selected TDK substitution and its matching ratings and dimensions.

The selected [no-touch HOTHMI LCD](https://www.hothmi.com/product/2-8-inch-display-high-brightness-st7789-spi/) is $15.47, a working [Mini A without pins](https://cryptoguide.tips/product/luckfox-pico-mini/) is $10, and the [10 mm SC3336 camera](https://cryptoguide.tips/product/luckfox-pico-camera-module-3pm-sc3336/) is $13 in the 2026-10-22 observations. The identified first-article components plus these modules total **$56.05**, or **$71.94 with the illustrative component spares**. These exclude the remaining costs below. The seller's $5 Mini option explicitly has a faulty microSD slot and is excluded from this microSD-build budget. See [module price observations](../variants/lcd-module-2.8/self-assembly/system-pricing-current.json).

For context, an [existing ShieldSigner display/reader hat including LCD](https://cryptoguide.tips/product/seedsigner-plus-display-hat-usb-c-power-smartcard-luckfox-pico-mini/) is listed at $36, or $38 with the pin-socket option. Our fitted carrier components plus the module LCD are already **$33.05 before bare PCB, freight, assembly or tools**. That does not prove any saving for a custom first article. The existing hat is a different design, and its listing has inconsistent Luckfox/Pi wording that needs clarification before purchase; it does not provide our pill/module construction. Build this variant for those desired features and learning, not on an unsupported promise that one-off fabrication is cheaper.

The **landed first-article cost remains unknown** until bare-PCB minimum order, stencil, consumables, headers/supports, microSD, enclosure, test card, shipping, tax/tariffs and any missing assembly/test equipment or labor are filled in. Missing amounts remain null, not zero. Compare full DIY with bottom-only outsourced SMT plus top-side hand assembly and full PCBA on the same basis. Do not divide a speculative batch cost by 20 to justify the first article.

C&K height tolerance is ±0.2 mm. The SCAD button now has a measured-height parameter and a 0.15 mm gap, with 0.40 mm nominal total travel. Its conservative default assumes a 2.7 mm switch and avoids preload across the specified height range, but a shorter switch may not actuate. **Measure each soldered switch and generate a matching plunger using `-D button_switch_height=...`**, use the coupon for bore fit, then test travel in the assembled retainer. The parameter excludes print/solder variation and does not replace physical first-fit testing. Do not order eight identical default plungers assuming they work for every tolerance extreme.
