# JLCPCB placement review — PCB 0.0.9-dev

Assembly package **0.0.9 r1** is an artwork-only first-article kit with
**review_required** status. Exact protected-tree comparison against the 0.0.7
board preserves component poses/identities, pads, copper, outline and the export
datum. This supports retaining the reviewed compensation; it does not establish
a new supplier preview, cart update or assembler placement approval.

The former 0.0.7 preview/quote is preserved under `../history/0.0.7-preview/`.
No order/payment is submitted by generating these files.

## Upload and confirm

1. Upload this package's Gerber ZIP, BOM and **compensated `cpl-jlcpcb.csv`**
   together. Select 1.6 mm, both-side assembly. Expect 35 SMT placements across
   17 catalog lines, with customer-fitted modules and through-hole headers.
2. Do not repeat old manual rotations/offsets: they are already in the upload
   CSV. `cpl-native-reference.csv` is diagnostic only.
3. Explicitly include J301 **USB4125-GF-A-0190 / C5246813** if the importer leaves
   it unchecked. Verify every matched reference and quantity.
4. Inspect USB mouth outward, six tails on their lands and all four stakes in
   slots; inspect every numbered smartcard contact and U601 pin 1.
5. Keep **Confirm Parts Placement: Yes**. Obtain new assembler DFM, panel/tooling
   and placement review before approving assembly. Record the new preview against
   the new PCB/output hashes; leave historical claims attached to their old board.

| Ref | Corrected Mid X (mm) | Mid Y (mm) | Rotation | Correction from native |
|---|---:|---:|---:|---|
| J301 | 46.510000 | 9.830000 | 0° | +0.84 mm Y; +180° |
| J601 | 88.620000 | 20.050000 | 0° | −0.8 mm X; +180° |
| U601 | 85.000000 | 60.700000 | 0° | +180° |

Other 32 placement rows are unchanged. The exporter verifies current board hash,
artwork compatibility proof, identities, bottom side and native datum before
applying compensation exactly once. D302's native/catalog pad-1 baseline needs
no extra rotation; a blanket bottom-side rule would be wrong. U701 stays on top
with its original pin-1 orientation; D301 is bidirectional.

## Smartcard numbered-contact review

The retained [contact audit](smartcard-contact-audit.json) is a manufacturer/
catalog coordinate comparison of the unchanged connector footprint. Its library
agreement is not a physical assembly tolerance or new supplier-preview approval.

In the bottom/component-side view, the tapered socket edge is up and notch down.
The upper row runs C1–C4 left to right; lower row C5–C8 left to right. Detection
pads are NO then COM left to right, between rows and to their right. Locating
holes are lower left and upper right. Two holes alone do not resolve the
180-degree ambiguity; inspect the asymmetric numbered contacts.

| Contact | Net / role |
|---|---|
| C1 | SEC1210_SC_VCC |
| C2 | SEC1210_SC_RST |
| C3 | SEC1210_SC_CLK_PostR |
| C4 | RFU, unconnected |
| C5 | GND |
| C6 | SEC1210_SC_VCC, tied to card VCC in this design |
| C7 | SEC1210_SC_IO |
| C8 | RFU, unconnected |
| NO | SEC1210_SC_PRSNT |
| COM | GND |

The catalog origin differs from the native connector-local origin by +0.8 mm X.
The retained comparison matches contact centers/land sizes and both locating
holes within 0.001 mm after translation. That exact coordinate agreement justifies
the origin correction; final assembly and first powered hardware remain pending.
