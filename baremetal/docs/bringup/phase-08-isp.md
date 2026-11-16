# Phase 8: ISP and Rust 3A

Evidence: [evidence/phase-8.json](../../evidence/phase-8.json).
Hardware run: `logs/phase-8/20261114T163158Z/`.

The RV1103 DUT captured SC3336 RAW, processed it through the ISP into 640×480
NV12, and ran the existing calibrated Rust AE/AWB sessions for 32 feedback
frames. All 31 gain/configuration submissions were applied in the ISP frame-end
IRQ. Sensor controls were read back, with two frames discarded after a change
before processing the third. Six ISP gain words matched after every update
(186 checks); the two gain 2 readbacks remain unresolved and excluded explicitly.

AE stayed within 5% of its final exposure from frame 10, AWB within 2% from
frame 7. Both decisions were identical over the final 12 frames:816 exposure
lines, gain code1065, WB gains1.2180655/1/1/2.1525512. Normal VTS1360 and live
HTS2500 produced33333us frame periods, implying an effective102.00102MHz pixel
rate. This replaces the slow32767-line diagnostic timing for the 3A feature.

Eighty selected fixed configuration readbacks matched successful REF writes.
The comparison preserves explicit hardware interpretation: RAWAE DONE/reserved
bits, CCM11-bit coefficient readback versus16-bit sign-extended writes, and
AWB1's12-bit-spaced readback versus16-bit-packed writes. Thirteen offsets with
no observed reference write are listed without an equivalence claim. The
normal AWB scheduling mapper also passed an independent82-write REF oracle
comparison and unsupported-field rejection tests.

The private side-by-side PNG was decoded and inspected: the same carton/barcode
is recognizable, with similar overall exposure and neutral colour. The two
cameras have different framing and remaining tint/noise; this is a qualitative
comparison. Optional denoise/sharpen modules were disabled on both paths.
The comparison is saved; REF no longer needs to be held in position.

## Scope and remaining work

This passes the bounded linear-profile gate, not unrestricted ISP support or
production hardware qualification. The driver uses stop/configure/start and
RAW readback, not uninterrupted streaming. Initial static tuning still uses
observed register facts; arbitrary module updates, HDR, changing VTS and ISP
exposure digital gain are not implemented. The current monotonic heap grows
about 3–6KiB/frame and must be replaced before an unbounded interpreter/control
loop. Phase 9 interpreter work is now authorized by this hardware gate; Phase 10
fast boot remains separate.

## Implementation and checks

`mise run baremetal:isp:3a:build` builds the normal-timing feedback image.
`baremetal:isp:build` and `baremetal:isp:stats:build` retain smaller diagnostics.
All overwrite the same RAM download image; inspect the manifest before loading.

- Eight host evidence/transport tests and eight observer/emulator tests passed.
- Existing Rust library:114 regression tests and ARM no_std profile build passed.
- AWB mapper:three tests passed, including 82 observed register writes.
-301 task definitions validated.

New shared-library `profiles` feature exposes existing calibrated sessions with
alloc-only serde_json. Host diagnostics retain std. Integer validation uses
libm truncation where bare-metal core lacks `fract()`; numerical controller
algorithms remain unchanged.

The initial64KiB gap between SVC and IRQ stacks failed with larger3A records.
IRQ now grows below2MiB, SVC below4MiB, with 2–3MiB unmapped as a guard. Normal
sensor timing also exposed a stop during the next MIPI packet: stop now occurs
at the last frame boundary before UART logging. Both fixes passed the final run.
One overlapping-UART-reader run was discarded and repeated cleanly.

## Reference build inputs

Ignored `.tools/` inputs are pulled read-only from REF and checked by exact
length/hash before building. Private images, logs and downloaded tools remain
ignored. No SD/flash writes were made; REF's original modules/storage remain.

| Local input | REF source | Bytes | SHA256 |
|---|---|---:|---|
| sc3336-iq.json | /etc/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json |432259|8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a|
| isp-initial-parameters.bin | /tmp/bm-p8-observed-auto.nv12.initial.bin |11145|25fa983c0dfc6313290336d25614db461be205cafaf9aa7598274be80fdded82|
| isp-awb-sdk.bin | /tmp/bm-p8-observed-auto.nv12.awb-sdk.bin |1204|4c081c95fe115f1c52ca84223e7a75cf647e64d3573accdcf5fa6c9c6352ccd1|

The partial live observer covers27 sites including nine ISP helpers. Fixed
capture 1365 events and automatic capture 16374 events had no drops/errors;
restore/unload and subsequent original captures succeeded. Unobserved direct
ISP stores are not claimed as traced. `generate_isp_replay.py` derives explicit
DMA-role profiles from first-trigger writes, never raw register readbacks.
The harness now retains a matching build manifest alongside serial evidence.
