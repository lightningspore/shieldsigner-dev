# Full-ISP32 measurement decoding

The pinned RV1106 driver assigns `rv1106_isp_match_data.isp_ver = ISP_V32` in `hw.c`. Its `isp_stats_v32.c` chooses `ALIGN(sizeof(struct rkisp32_isp_stat_buffer),16)` for that version. The lite branch is assigned to RK3562 (`ISP_V32_L`); it must not be selected merely because the board is called Luckfox Mini. Both driver sources are pinned by URL/hash in `artifacts.json`. Earlier reconstruction notes called this target ISP32-lite; those references were corrected after checking the actual driver.

`statistics::Statistics` borrows one full-ISP32 buffer and exposes uncalibrated measurements without allocation. The packed payload is **13,036 bytes**, with an aligned driver buffer of **13,040 bytes**. Measurement mask, frame ID and parameter ID sit at offsets `0x32e0`, `0x32e4` and `0x32e8`. Other sizes are rejected, including lite and multi-ISP allocations. A matching size is not a runtime format identifier: the caller must supply bytes from the correct statistics endpoint and pinned driver.

Supported fields:

| Measurement | Layout | Validity mask |
| --- | --- | --- |
| AE0 grid | 25 packed RGB samples at `0xab0` | bit 7 |
| AE1/AE2/AE3 grids | 225 samples at `0x390` / `0x720` / `0` | bits 8 / 9 / 10 |
| Histogram 0/1/2/3 | 256 u32 bins at `0x1000` / `0x1400` / `0x1800` / `0xc00` | bits 11–14 |
| AWB grid | 225 packed u64 blocks at `0x2b00` | bit 5 |
| AWB light sums | four 32-byte records at `0x3210` | bit 5 |
| AWB luma histogram | eight u16 encoded bins at `0x3290` | bit 5 |

AE packed channels use 12 green bits, 10 blue bits and 10 red bits, in that order from the low end. AWB blocks use 18 blue, 18 green, 18 red and 10 white-point bits. Light sums preserve normal/big red and blue gain counters, normal/big point counts, and the second point count. Luma-histogram entries with bit 15 set decode to `(value & 0x7fff) << 3`, as in the original translator. Invalid measurements are exposed as absent rather than reading stale counters.

This is not the full resource translator. It does not copy configuration metadata, choose light sources, calculate AWB gains, subtract BLS, normalize AE values, apply exposure weights, translate AF/dehaze, or synchronize queues. AE subwindow sums and AWB exclusion sums are not yet exposed by this API.

## Verification

`camera:rust:layout` cross-compiles pinned kernel UAPI headers to verify sizes, offsets and counts. Host tests cover packed channel boundaries, encoded histogram expansion, validity gating and malformed lengths.

`camera:rust:statistics` executes the original `RkAiqResourceTranslatorV32::translateAwbStats` instructions (ELF `0x8818c`, Ghidra `0x9818c`) against 100 deterministic full buffers. Buffer-access methods and the multi-ISP predicate are explicit stubs; actual single-ISP unpacking, sum copies, histogram expansion, frame propagation and smart-pointer reference counting execute as ARM instructions. The comparison checks all 225 RGB/point blocks, four light-sum records, eight luma bins and frame ID. Calibration/configuration portions of its output are outside this Rust reconstruction. [Report](statistics-equivalence.json).

The 100-buffer comparison covers AWB only. AE raw decoding is supported by the pinned field layout and local tests, not by a claimed comparison with the complete native AE translator. `camera:rust:smoke` repeats the AWB corpus using the compiled static ARM fixture runner under Docker emulation. Real queue acquisition, actual sensor statistics, exposure response and white-balance behavior remain untested.

`camera-probe stats FILE` provides a JSON dump for a saved statistics buffer. It works offline and makes no device changes. `camera-probe capture-statistics` now acquires a bounded sample from the existing full-ISP32 metadata queue, using at least two buffers and verifying RK1S/13,040-byte format first. It does not configure measurements or start the image pipeline. See the hardware guide for the two-terminal procedure. This new acquisition path has only ABI/guard checks so far; real queue operation is pending.

## Configuring the measurements

The corresponding selected AE-grid/histogram result-to-parameter conversion now exists in `isp_ae_measurement`. It matches native ISP32 routing and cache updates, including duplicated configurations across hardware channels. [Measurement configuration](AE.md#measurement-parameter-configuration). It does not yet choose calibrated windows/weights, configure AWB measurements, synchronize the loop or provide complete initial ISP setup. Capturing a buffer without the proper measurement configuration still does not establish useful/qualified statistics.
