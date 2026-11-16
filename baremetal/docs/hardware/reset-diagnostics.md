# USB-readable warm-reset evidence

DUT1 releases UART2 for its LCD backlight, so the existing UART fault text is not
available there. Runtime-board images now write a small numeric record before
known software reset/fatal paths. After RAM reload, inspect:

```python
import machine
machine.last_reset()                 # dict, or None if no valid record
machine.clear_reset_record()         # preserve evidence on host before clearing
machine.set_reset_marker(0x50414745)  # optional nonnegative run identifier
```

The64-byte record is at DDR `0x03c10000` (60MiB+64KiB), in the existing
noncacheable48..64MiB camera/USB mapping. It is outside USB's16KiB DMA area,
RAW48/52MiB, NV1256MiB, statistics58MiB, both heaps and UI shadow32MiB.
Reserve this region when changing memory layouts. The writer allocates nothing,
uses no Python/C++ exceptions or USB calls, and commits the magic last after a
barrier. A version, complementary magic, reserved word and FNV checksum reject
partial or corrupted data. This is integrity checking, not authentication.

| Reason | Recorded path |
| --- | --- |
| 1 | Generic software reset fallback |
| 2 | USB Ctrl-] request |
| 3 | Interpreter fatal/NLR-failure callback |
| 4 | Native UI fatal/process exit, including C++ abort |
| 5 | ARM exception handler |
| 6 | Rust panic handler; this handler still halts rather than automatically resets |
| 7 | Wired UART recovery request |

The first marked cause in a boot wins; the generic reset fallback cannot erase
it. The record also holds a caller-supplied marker and raw generic-counter value.
ARM exceptions include LR, saved status, mode and raw DFSR/DFAR/IFSR/IFAR. These
registers are latched hardware state: not every field belongs to every exception.
Use the relevant mode/status and the exact failing image's ELF when interpreting
addresses. The diagnostic gate saves its matching ELF and image; its real guard
fault resolves back to `bm_reset_probe`.

This is the last valid *software-written* record, not an authoritative hardware
reset-cause register. An unmarked hardware reset may leave an older record, or
lose DDR contents. Cold-power retention and recovery from a halted panic are not
qualified. None means no valid record, not proof that no reset happened. Save and
clear before a monitored run. The format contains numbers, not exception strings,
passphrases, seed material or camera pixels.

The paged-review wrapper now saves the previous record before clearing, marks the
run as PAGE, archives the current build manifest/ELF and checks the record again
after a successful run. If transport or execution fails it preserves evidence and
stops, so a reset can be inspected after recovery before another test overwrites
its context. Older firmware without this API is explicitly marked unavailable.

Deliberate fault injection is opt-in and RAM-only:

```sh
mise run baremetal:reset:check
mise run baremetal:reset:probe:dut1:build
# Load using the explicit DUT1 RAM loader, then:
mise run baremetal:reset:probe:dut1:gate
```

The diagnostic image alone enables `machine.fault_probe`:1 reads the unmapped
stack guard,2 calls actual C++ abort,3 calls the interpreter-fatal callback,4 damages
a simulated record checksum. The gate resets/reloads the same selected DUT1,
checks retained causes/markers, validates actual guard fault registers and saves
the exact ELF. The separate USB warm-reset gate also proved DDR retention.
The normal `baremetal:ui:dut1:build` disables these probes; calling one raises
NotImplementedError. `machine.fault_probes_enabled()` reports the build state.
No SD/flash writes or REF/DUT0 reset occur in the DUT1 diagnostic gate.

These probes prove the diagnostic paths, not the cause of the earlier unexplained
review reset. That incident predates these records and cannot be reconstructed
retroactively. Subsequent instrumented review runs can provide useful evidence
if it recurs; until then the original stability issue remains open.
