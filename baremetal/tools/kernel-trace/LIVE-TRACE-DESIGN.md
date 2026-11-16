# Live write-call tracing: implementation constraints

REF is restored. Do not unload/unregister camera components again. The two failed teardown attempts are diagnostic text artifacts, not deployment scripts.

The exact original module ELF files contain relocations identifying calls to `arm_heavy_mb`, `regmap_write`, and the sensor's `i2c_transfer_buffer_flags`. The first is the out-of-line I/O barrier used before MMIO writes; the other two expose register writes directly. This provides a candidate for observing existing drivers without changing their graph.

A host survey of original `.rel.text` entries found15 selected CIF calls and 3 D-PHY calls; the sensor has one write-transfer call. Most MMIO sites have up to four simple loads/arithmetic operations before the store. One CIF barrier belongs to a read path and must be excluded. Survey: local logs/phase-7/live-write-callsite-survey.json.

Before application:

1. Generate a whitelist from exact original module hashes and ELF relocations; reject every unsupported instruction sequence. Include every store-site load/shift/add needed to predict its destination/value. Never execute the predicted store in the recorder—the original instruction still performs it.
2. Use only a same-size Thumb2 call redirection at validated callsites. Validate the live original branch destination. Pin original modules for the hook lifetime, apply/revert under stop_machine and flush instruction caches. Check all displacements before making any change.
3. The MMIO wrapper must invoke the original barrier, preserve integer registers, flags and stack, and return to the original store. Verify branch encoding and register preservation with host ARM emulation before REF application.
4. Sensor/regmap wrappers must call their original APIs and record successful writes without changing return values. Do not patch closed DDR or loader blobs; inspection concerns GPL camera modules only.
5. Resolve logged virtual MMIO destinations to physical addresses without reading device FIFOs or making additional hardware writes. The kernel hashes `/proc/vmallocinfo` addresses; its text is not a usable physical mapping table.
6. Keep recording bounded; report omitted/unsupported sites and overflow. A partial hook trace is not proof of a complete ordered trace. Capture and verify original Rust raw frames before, during, and after observation. Revert all redirections before unloading the recorder.

No live call redirection has been applied yet. No DUT raw capture has passed. This design is not a hardware gate.

## Implemented offline components

`live_ir.c` is the C prediction/branch core checked against original Thumb instructions. `live_sites.h` is generated into ignored build output directly from original ELF data and checked after C compilation. `live_io_wrapper.S` preserves the observed register/stack/flag state in emulator tests.

`live_translate.c` walks ARM short descriptors, supporting ordinary sections, large pages and small pages; unsupported supersections and missing mappings fail. It reads table words through a callback, never mapped device targets. `live_memory.c` adapts this to the exact REF configuration: non-LPAE, no highmem, physical RAM0–64MB, PAGE_OFFSET from the kernel. It requires TTBCR0 and uses TTBR1's retained swapper directory, as established by pinned `arch/arm/mm/proc-v7-2level.S`. Prediction loads must translate to DDR before they can be read through `copy_from_kernel_nofault`. The adapter and walker compiled with the matching vendor GCC8.3/kernel configuration; they have not been executed on REF. Validate known DDR and device translations before using them for trace interpretation.

Remaining: original-module pinning, live branch validation and transactional patch/restore, regmap/sensor wrappers, recorder integration, runtime translation validation and complete coverage evidence. Offline tests do not establish these properties.

Hardware translation check subsequently passed using `memory_probe.c`: allocated RAM translated to its independently computed `__pa`, RAM word read matched, an ioremap of VICAP translated at both range ends, device-data reads and user-space addresses were rejected. The temporary mapping was never dereferenced. Probe loaded from `/tmp` and unloaded successfully; original Rust raw capture passed before and after (3,981,312 bytes). Local logs: `memory-probe-runtime.txt`, `pre-memory-probe-capture.txt`, `post-memory-probe-capture.txt`. Loading sets expected out-of-tree taint4096; this is distinct from a crash. No call redirections or camera graph changes occurred. Runtime observation coverage and patch/restore remain unverified.

## Live validation and first usable capture

`live_preflight.c` pins all 3 original modules through their public bus devices, checks names/text bounds, decodes each live branch and compares its target/link mode and post-call instruction bytes. All 18 sites passed on REF. It unloaded cleanly, released module references and original capture passed afterward. Logs: `live-preflight-runtime.txt`, `post-preflight-capture.txt`.

`live_observer.c` integrates the predictor, wrapper and recorder with explicit A/apply and R/restore controls. Original targets are checked again at apply. `live_patch.c` validates all words before any writes, under stop_machine; halfword writes support Thumb call alignment, followed by instruction-cache maintenance. A self-reference keeps the observer loaded while hooks exist. Restoration refuses in-flight wrappers. Exact verified configuration is single-core, PREEMPT_NONE, writable kernel text; compilation rejects incompatible settings. Apply/restore without streaming passed on REF, with refcount1 while active and 0 after restore; unload and subsequent raw capture passed.

First observed capture succeeded but reported 45 failed observations. Root cause: guarded translation incorrectly rejected kernel module data below PAGE_OFFSET. Changed the lower bound to MODULES_VADDR, retaining user-address/device-data rejection. Second observed capture (`live-observer-capture-2.txt`, `live-events-2.txt`) passed:201 events, dropped 0, errors0. Counts:148 sensor,50 MMIO,3 regmap; MMIO covers VICAP, CSI and D-PHY. All hooks restored, observer unloaded; subsequent original raw capture passed (`post-observer-capture-2.txt`). Seven whitelisted sites were not exercised by this stream configuration; runtime coverage is not proof of every possible mode.

MMIO entries are observed **before** the original store. Regmap/sensor entries follow successful API calls. Interrupt interleaving can distinguish this order from completed bus-write order; do not label it an exhaustive bus trace. Clock/power-controller writes and complete idle/streaming register snapshots still need separate evidence before replay. No DUT raw image has passed. Current REF modules are original, no observer remains loaded, taint4096 is the expected historical out-of-tree flag.
