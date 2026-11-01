# Memory: measured results and limits

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Acceptance](ACCEPTANCE.md)

The memory-cleanup goal is complete for the measured workloads. It removed
unnecessary eager work and allocations while preserving original wallet logic;
it did not remove CPython or turn the application into a Rust-only program.

| Workload | Python private anonymous RAM plus swap |
|---|---:|
| Home | 11,012 KiB (10.75 MiB) |
| Live scanning | 13,576 KiB (13.26 MiB) |
| Settings, separate startup fixture | 10,860–10,880 KiB |
| Transaction flow, maximum sampled | 16,704 KiB (16.31 MiB) |

Home/scan numbers are medians after each phase's first three seconds. They exclude
camera, QR and native renderer processes. These are process/workload measurements,
not total-system memory, exhaustive object accounting or guaranteed global peaks.
Sequential samples retain run-order and allocator effects. RSS, PSS, private
anonymous RAM and swap answer different questions; compare matching definitions.

## What improved

- Deferred unused tools, optional wallet/QR/parser backends and legacy Decimal
  rendering imports until their actual consumer needs them.
- Released disposable inspected source strings and inactive native preview input
  capacity. Native Home private RAM fell from 216 to 92 KiB in the measured pair;
  releasing preview input returned another observed 132 KiB after stopping.
- Shipped checked-hash ordinary source bytecode so first-boot imports avoid
  compiling those sources into temporary Python objects.
- Measured repeated camera/QR use, worker cleanup and retained resources rather
  than treating one fresh Home sample as the entire application.

These improvements overlap. Do not sum separate experiment savings into a claimed
total reduction. The original upstream classes/functions and public fixture
payloads were checked as part of the cleanup.

## Why bytecode matters

The final package includes 142 ordinary CPython 3.12 cache entries for unchanged
app/LVGL/camera sources, alongside transformed-module caches. It adds 1,726,498
file-storage bytes; the final payload totals 5,469,515 bytes across 253 files.
The launcher selects the read-only cache prefix with `-X` and retains `-B`.

Without ordinary caches, isolated source-compilation controls measured
12,308/14,084 KiB at Home/scan. With the shipped cache, they measured
11,012/13,576 KiB: 1,296/508 KiB lower. Both processed 57 real previews and stopped
the camera owner cleanly. This simulated first-boot compilation with isolated
prefixes; it was not a physical reboot comparison. CPython checks source hashes
and falls back to source if caches are stale, including same-size/same-mtime edits.

## What still consumes memory

CPython, loaded application modules, strings/classes, wallet data and live worker
state remain. Shared wordlists have active wallet consumers. Pillow remains for
original still-image/entropy consumers and optional scaling; its presence does
not mean every LVGL widget still renders through PIL. The active native preview
needs its input pixels while scanning. Wallet libraries and typing support retain
real consumers; deleting dependencies without tracing those consumers would break
behavior. Storage size alone does not establish resident Python memory.

## Evidence and diagnostics

- [Cleanup acceptance](../validation/memory-cleanup-acceptance.json)
- [Packaged source cache comparison](../validation/packaged-source-cache-memory-summary.json)
- [Repeated-use audit](../validation/retention-memory-summary.json)
- [Native buffer observations](../validation/native-preview-memory-summary.json)
- [Earlier cleanup summary](../validation/memory-cleanup-summary.json)

`mise run lvgl:app:memory-maps` reads process metadata from an existing interactive
session; `lvgl:app:resources` summarizes matching receipts. Hardware diagnostics
are documented by `hardware_check.py --help`. Object-by-object attribution is a
separate future exercise; it is not required to interpret these scoped results.
