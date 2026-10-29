# Camera GUI bring-up status

**The current diagnostic setup has passed a three-minute real ScanView run and three fresh one-minute launches with the PyO3 LCD driver.** The runs use compressed RAM swap, pinned native code and bounded transport recovery. Physical QR acquisition, visual confirmation, user-driven navigation and a persistent image remain open. See [current measurements and results](CAMERA-MEMORY.md).

The earlier failure investigations below are retained as historical evidence. Working ADB, headless checks and host tests alone did not establish a working GUI.

The [trial ledger](../reverse-engineering/rkaiq/gui-camera-trial-ledger.json) separates saved observations from operator reports. It contains hashes and selected metadata from ignored private traces; it does not publish scene images or decoded payloads. Several trials lack a mapped terminal owner log, so their exact native failure remains unknown here. An exited/zombie process alone does not identify the cause.

## Confirmed findings

The [co-residency test](../reverse-engineering/rkaiq/gui-camera-memory-pressure-validation.json) hit a real OOM: the kernel killed GUI PID 2951, whose anonymous RSS was about 23 MiB. Normal free memory reached its minimum watermark, only 60 KiB remained on the file LRU, and no swap was configured. The subsequent 104 native frames were **not** a concurrent GUI success. The next 20-second, 106-frame run was headless because the GUI was already gone; the requested paused-GUI comparison was therefore invalid.

Later lower-memory trials still failed according to the operator. The latest saved real-time trace independently confirms SCHED_RR policy 2, priority 20, roughly 5.6–6.2 MiB available memory and a native process exit. The operator reports no OOM and a remaining event/parameter-pool failure in that trial. Its terminal owner log is not mapped in this ledger, so that error classification remains an operator report.

## Trial ledger

This is a set of investigated changes, not a claim that each was independently isolated or that they all failed identically.

| Trial/change | What is established | What remains unverified here |
|---|---|---|
| Frame publication gate | Saved trace includes `pipe_write`, `squashfs_cache_get` and teardown waits; native process later disappears. | Exact terminal native error. |
| Compact runtime logging | Trial reported unsuccessful. | Saved trace is empty; no terminal log mapped. |
| Discard owner log output | Trial reported unsuccessful. | Exact sink configuration and terminal log per trial. |
| Nice -10 | Trial reported unsuccessful. | Recorded scheduler settings and terminal log. |
| Static/prewarmed spinner | Trial reported unsuccessful. | Saved trace is empty; no terminal log mapped. |
| Requested 6 FPS | Trial reported unsuccessful. | Actual sensor/publication cadence and terminal log. |
| Eager/resident GUI | Kernel OOM killed the GUI. Separate headless 20-second capture passed. | Concurrent GUI stability; paused-resident comparison was invalid. |
| Small-RAM imports plus IQ-tree release | Native RSS snapshots 8,272–8,424 KiB; available memory 2,740–4,104 KiB before exit. | Exact terminal error and attributable heap savings. |
| Small preview | Running native snapshot followed by zombie; available memory rose sharply. Operator reports OOM. | This trace contains no OOM record or identified victim. |
| Luma plus Small-RAM | Available memory settled around 6 MiB in later samples; native process subsequently exited. | Exact terminal owner error; operator reports event/pool failure. |
| RR20 plus Luma/Small-RAM | Policy 2 / priority 20 confirmed; available memory 5,784–6,340 KiB before exit. | Terminal owner log; operator reports failure without OOM. |

A separate compact/direct trace records native `pipe_write` and `do_task_dead`, but its intervention mapping is uncertain. It is retained without assigning it to the discard-log experiment.

## Memory setup versus code improvements

Archived diagnostic files also consume scarce tmpfs RAM. Removing the four inactive B/C directories after host archival freed exactly 1,620 KiB of Shmem. The coordinator separately archived and removed the inactive client-parent proof and moved the verified candidate ELF off tmpfs to a read-only executable bind from `/userdata`; the base userdata mount remains `noexec`. These are diagnostic setup savings, **not** evidence that the code heap shrank. Source changes that release IQ data or reduce imports require their own measured comparison.

The selected kernel uses an XZ SquashFS with one data-cache entry and a single serialized decompressor. A `squashfs_cache_get` wait can indicate cache-slot or pending-decompression contention; it does not by itself prove OOM or establish the cause of an event/pool timeout.

Subsequent event/phase instrumentation identified blocking logging and repeated code-page faults. Quiet production logging, a bounded code-pinning experiment and compressed RAM swap are documented in the current memory report. The historical OOM evidence remains valid; the new bounded GUI passes do not by themselves establish release qualification.
