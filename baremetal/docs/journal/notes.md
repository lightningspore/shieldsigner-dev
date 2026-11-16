# Working notes

> **Engineering journal.** This is a dated, chronological record. Statements
> describe the state when they were written and may be superseded. For the
> current state, see [../status.md](../status.md).

Updated: 2026-11-13 (host local date). **Phases 0–6 passed on hardware. Phase 7 raw camera capture is next.**

## Devices and boundaries

- REF: **standard Luckfox Pico, RV1103** (user-confirmed), ADB `0a523b8b23110ffc`, Linux 5.10.160 `seedsigner-os`. Its live DT model string says Mini, but physical board identity is standard Pico. SC3336 camera detected as `0xcc41` at I²C bus4 address0x30. REF's own camera stays attached.
- DUT: **Pico Mini, RV1103**, former ADB `ec9eda0a3c175664`; USB `2207:110c`, location 201. No microSD. RAM downloads only. User connected a **separate SC3336 camera** and confirmed DUT is powered back on; sensor ID was verified by our code.
- Host: macOS26.5.1 arm64, official rkdeveloptool commit `304f073752fd25c854e1bcf05d8e7f925b1f4e14`, GCC arm-none-eabi16.2.0, mise Rust1.93.1/armv7a-none-eabi, uv Python3.13. Tool checkouts live in `.tools/` (ignored).
- Never write REF boot partitions, flash DUT, or install/write DUT SD without further authorization. Do not infer later-phase hardware success from compilation or earlier gates.

## Wiring

Existing UART: REF UART3 → DUT UART2, **115,200 baud**, raw8N1. Red REF TX (`GPIO1_D0`, standard Pico header 19) → DUT RX (`GPIO1_B3`, Mini header 5). White REF RX (`GPIO1_D1`, standard Pico header 20) ← DUT TX (`GPIO1_B2`, Mini header 4). Brown common GND, exact REF ground pad unspecified. These paths are proven on hardware.

GPIO: blue REF **GP5/GPIO1_C4/header7** ↔ DUT **GPIO1_C4/header10** (DUT output → REF input). Orange REF **GP4/GPIO1_C5/header6** ↔ DUT **GPIO1_C5/header11** (REF output → DUT input). Linux GPIO52/53. All sixteen transitions passed. Test cleanup returned both DUT pins and REF pins to inputs. On REF GPIO52/53 remain exported through sysfs, input direction. Do not assume both boards share physical header numbering.

## REF runtime bridge

Display supervisor/frontend stopped with SIGTERM; all its periphery GPIO ownership released. Runtime status-only UART3 overlay `baremetal-uart3` enables `/dev/ttyS3`, MMIOff4d0000, GPIO1_D0/D1. Debugfs mounted for pin ownership checks. No startup files changed. Reboot clears this setup and restarts UI; re-check live process IDs and ownership before reapplying overlay.

Never call `S99seedsigner stop` (the script unconditionally starts the app). To restore UI: close captures, disable/remove only our UART3 overlay, then start `/start-seedsigner.sh`, or reboot REF.

## Passed gates and evidence

| Phase | Evidence | Result |
|---|---|---|
|0|`logs/phase-0/doctor-20261114T053121Z.json`|REF shell, UART opens, DUT maskrom, wiring confirmed|
|1|`logs/phase-1/20261114T054010Z/`|Readable stock DDR/USB loader banner at 115200; RV1103,64MB DDR2,528MHz DDR|
|2|`logs/phase-2/hello-gate-20261114T054519Z.json`|Ten consecutive original Rust hello runs and automatic UART resets|
|3|`logs/phase-3/phase-3-gate.json`|96.45x cache speedup with equal checksum;1000 timer IRQs in1s;47/47 IRQ echo bytes;heap check|
|4|`logs/phase-4/gpio-gate-20261114T060114Z.json` and `20261114T060058Z/`|16/16 opposite-level transitions matched in both directions; GPIOs released afterward|

Ignored logs are local evidence. [history.md](history.md) retains attempts and corrections, including the initial wrong-baud diagnosis and REF model correction. [project brief](../project-brief.md) is the original user plan and retains its original two-Mini assumption; this file supersedes that hardware detail.

## Builds, recovery, CPU base

`mise run baremetal:build` builds minimal hello; `mise run baremetal:cpu:build` adds CPU base; GPIO build uses `uv run --python 3.13 python baremetal/tools/build_hello.py --features gpio-test`. All currently output `build/hello-download.bin`; inspect `hello-manifest.json` for features/hash. Phase 2/3 baselines preserved under `build/phase-N-baseline/`. Source is original MIT Rust; vendor DDR blob unchanged, not disassembled; GPL drivers studied for register facts only.

Current DUT image before power-off: gpio-test, with CPU base, IRQ UART and commands0/1 for GPIO, Z to release GPIO, R to warm-reset. R via REF UART returns maskrom; stock usbplug supports `rkdeveloptool rd 3`. A stale USB device may still list Maskrom while payload runs—reset before repeated db. No actual USB power controller/hub is exposed; software reset cannot guarantee recovery from a hard hang.

CPU DDR map and register references: [cpu-base.md](../hardware/cpu-base.md). MMU maps64MB DDR cacheable and peripherals device; ACTLR.SMP enabled before cache maintenance. Heap4–8MB, monotonic/no reclaim yet. Provisional camera reservation48–64MB; DMA coherency and actual size remain Phase 7 work.

## Latest result: Phase 5 passed

Original I²C4 combined register reads return SC3336 ID0xcc41 at address0x30/register0x3107 in polled and interrupt modes (GIC INTID54). Controller parent explicitly24MHz, SCL100kHz. Camera MCLK configured27MHz from detected GPLL1188MHz /2 ×1/22; GPIO3_C5 releases sensor power-down/reset. Live REF registers and pinmux were studied; REF camera remains untouched.

Hardware evidence `evidence/phase-5.json` and full local `logs/phase-5/20261114T060918Z/`. Wrong address0x31 NAKs correctly in polled and IRQ modes. Deliberately masking the I²C IRQ triggered a ~2ms timeout; cleanup was followed by a successful IRQ sensor read. This validates the software deadline and recovery path, not every possible physical bus fault.

DUT currently runs i2c-test, remains recoverable through UART R, and has its separate camera attached. Blue/orange GPIO lines remain inputs; REF GPIO52/53 were exported inputs during the test; see latest reboot state below. Next Phase 6 needs a DUT MOSI-to-MISO jumper for SPI loopback; pin assignment/test code not yet prepared. Do not start Phase 7 camera capture until Phase 6 gate passes. User requested a commit after each completed phase; Phases0–4 checkpoint is33d0926.

## Latest result: Phase 6 passed

Receipt `evidence/phase-6.json`, full local logs `logs/phase-6/20261114T061524Z/`. External SPI0 loopback DUT header 8/MOSI/C2 → header 9/MISO/C3, 4096 pseudorandom bytes with zero mismatches at configured0.996/9.96/49.8MHz (nominal1/10/50MHz, -0.4%). No DMA or controller-internal loopback. Actual clock configuration derived from inherited CPLL996MHz /5 and dividers200/20/4; PLL was not retuned. Driver clock/register facts from official SDK. DUT currently spi-test with UART R reset; camera stays attached. GPIO blue/orange unchanged. Next Phase 7 reference capture and camera register replay; no raw image passed yet.

User requested RustPython be evaluated as a potential Phase 9 interpreter. Preliminary source findings and required decision tests are in [phase-09-runtime.md](../bringup/phase-09-runtime.md). No interpreter selection or bare-metal RustPython support is claimed. Keep all original Phase 9 peripheral/camera hardware gates.

## Phase 7 current work and REF recovery

REF raw capture works through the existing Rust camera-probe at /dev/video0, compact RAW10 2304×1296,stride 3072,3,981,312 bytes. /dev/video11 is ISP NV12. User cannot hold cameras and turned off lights; do not request ongoing manual positioning. Exposure changes are authorized. VBLANK31471 (VTS32767), current exposure 4096/gain256; use >=5s per-frame capture deadline. A maximum-exposure32759 comparison strongly increased signal but overexposed the scene. Raw/private scene files remain local/ignored under logs/phase-7.

Exact SDK commit0b5c1f30ca6333b7ec5af70d26511da9ef8d39af fetched into .tools/kernel-reference; original driver hashes all match REF ABI proof. REF config hashb210dc5fca942dc4725c6644b9b141d4a881c062e2c5f409bb9166020c92f9c6 also matches. FTRACE/KPROBES are disabled. A bounded GPL runtime recorder and narrow tracing hooks compiled with matching vermagic; added undefined symbols were only recorder hooks. Build artifacts stay ignored. Preparation/build sessions have completed; do not restart them based on old session notes.

**The attempted unload sequence crashed stock CIF notifier teardown before any modified camera module was loaded.** It is retained only as tools/kernel-trace/failed-unload-sequence.sh.txt; do not execute/retry it. Full crash log: logs/phase-7/ref-unload-crash-dmesg.txt. Investigate teardown ordering or choose another tracing strategy before further swaps.

**REF is now recovered.** Standard ADB reboot request did not reset it; sync plus direct RV1103 CRU warm reset did. Original boot/module files were unchanged. REF re-enumerated, taint0, original Rust raw capture succeeded (logs/phase-7/ref-recovery.json). Display frontend stopped again; debugfs/UART3 overlay restored, serial configured115200. No recorder or modified camera modules remain loaded. GPIO52/53 are no longer sysfs-exported after reboot; frontend released them, so they are inputs/unclaimed. Red/white/brown UART and blue/orange test wires remain physically connected; SPI jumper stays in place on DUT. DUT still runs spi-test with UART R reset.

No DUT raw frame has passed. Phase 7 still needs ordered writes, idle/streaming MMIO dumps, replay/raw image and ten consecutive frames, followed by named original driver code. Do not advance to Phase 8 or claim Phase 7 completion from REF-only frames. Commit after completed gates as requested; Phase 6 commitb7248a7 is the latest completed checkpoint.

Latest correction: the public-API detach helper also faulted in notifier cleanup (logs/phase-7/ref-detach-crash-dmesg.txt). REF was warm-reset a second time, frontend stopped, UART overlay reapplied, and original 3.98MB raw capture passed again with taint0 (`ref-recovery-2.txt`). Current controls exposure 8192/gain512,VBLANK31471 for lights-out operation. Do not repeat any graph teardown. Failed helper source is retained as `.c.txt`; commandD removed from active recorder source. A host ELF callsite survey found a possible live write-call observation route, documented in tools/kernel-trace/LIVE-TRACE-DESIGN.md. No such redirection has been applied. Its mechanical safety/coverage must be validated offline first.

Offline observation progress: `mise run baremetal:trace:check` passes 3 tests, including 448 original-instruction/address-value comparisons and actual assembly register/stack/flag preservation. Generator tools/live_trace_sites.py produces ignored logs/phase-7/live-write-sites.json with 18 whitelisted calls (14 MMIO,3 regmap,1 sensor), plus one explicitly excluded read barrier. The hardware observer has not been installed; physical address translation, module pinning/validated patch/restore, and complete runtime coverage remain to be implemented/verified.

Latest offline check now passes 4 tests. The same narrow C predictor/branch codec intended for the kernel passes the 448 instruction comparisons. `generate_header()` emits `build/kernel-trace/live_sites.h` from original ELF data; a new test compiles the generated table with warnings as errors and compares all 18 compiled site records and instruction operands against the decoded whitelist. No live redirections have been applied. Remaining implementation is unchanged: guarded memory reads/physical translation, module pinning, validated apply/restore, wrappers and runtime coverage. Current low-light controls remain exposure 8192/gain512; user again confirmed lights are going out.

Latest check passes 6 tests after adding actual C short-descriptor translation tests (sections, large/small pages, fault paths, no target-device reads). `live_memory.c` uses retained TTBR1 swapper directory only with TTBCR0, validates DDR-only table/prediction reads and uses copy_from_kernel_nofault. Both new C objects compiled successfully under exact REF kernel config/vendor GCC8.3; log `logs/phase-7/live-memory-build.txt`. Initial object-build attempts lacked a populated external-module Makefile; fixed in ignored staging and reran successfully. Read-only ADB health check confirmed taint0 and System RAM0–03ffffff. Adapter has not run on hardware; validate known translations before tracing. No live patch/restore code or recorder integration yet.

Hardware translation probe now PASSED: loaded temporary bm_memory_probe from /tmp, independently compared RAM physical address and value, translated VICAP mapping0xffa10000 and end0xffa1fffc, rejected device data read and user address. No device mapping dereference. `memory-probe-runtime.txt` shows both PASS markers and load status0. Unload status0, module absent afterward, original Rust3,981,312-byte raw capture passed before/after. Expected out-of-tree taint4096 now persists until reboot; no fault occurred. Current original module text bases saved in `live-module-identities.txt`: CIFaf81b000, PHYhwaf887000, sensoraf814000. Public driver/module symlinks match all 3; these are runtime addresses and must be refreshed/pinned before use. No graph teardown or call redirection occurred. Next implement module pinning/live callsite preflight and transactional restore.

Latest: live preflight and observer now exercised successfully. All 18 original calls validated against expected kernel APIs and post-call bytes while all 3 camera modules pinned; standalone preflight unloaded/refcounts restored, capture passed. Observer applies/restores under stop_machine with batch validation before any code writes; self-reference prevents unload while active. Idle apply/restore/unload and subsequent full raw capture passed. Actual trace capture 1 succeeded but45 observation errors exposed a lower-bound bug: ARM module data lives below PAGE_OFFSET. Fixed bound to MODULES_VADDR. Capture2 logged201 events (148 sensor,50 MMIO,3 regmap), dropped 0/errors0. Raw3,981,312 bytes, restore/unload statuses0, post-restoration raw capture also passed. Files: `live-preflight-runtime.txt`, `live-observer-idle-cycle.txt`, `live-observer-capture-2.txt`, `live-events-2.txt`, `post-observer-capture-2.txt`. REF healthy, original modules, no observer remains loaded, historical out-of-tree taint4096. All 7 offline tests pass including fail-closed batch apply/restore. Added module-data regression case to memory_probe.c, but this revised standalone probe has not been rerun; corrected reads were exercised by zero-error live observation. Next: analyze/normalize trace, validate mode coverage and GRF regmap bases, collect idle/streaming register snapshots including clocks/power, implement DUT raw replay. No DUT frame yet; Phase 7 incomplete. MMIO log is pre-store observations, not a bus-completion trace. Do not retry camera module teardown.

## Latest: DUT raw frames captured; Phase 7 still open

`ref-dumps/idle-clocks.json` and `streaming-clocks.json` contain108 source-reviewed CRU/PLL/VI-reset/PHY-GRF registers. Streaming snapshot accompanied a full Rust REF capture, runtime_status active; clk_summary saved. Changed gates: top3, VI0/1, VEPU0. These are partial config reads, **not** the full CRU/GRF/IOC/PMU/DPHY/CSI/VICAP/ISP ranges required by plan. REF remains healthy/original modules/no observer, taint4096.

`reference_camera_data.py` validates zero-error/restored trace, normalizes PHY GRF to ff050014, remaps both REF DMA addresses to DUT48/52MB, and emits original Rust replay facts. `camera.rs` configures only camera clock/reset branches, initializes sensor with bounded I2C writes, polls alternating frame-end bits with 5s deadlines and returns 192×108 RGB preview. DMA slots48–56MB map normal noncacheable under camera feature. Camera peripheral IRQs remain disabled; polling clears W1C statuses. Rejects FIFO errors, out-of-range replay writes, failed stream stop and unchanged DMA. This is developmental replay, not final named driver code.

DUT runs `camera-pattern` diagnostic now (latest run below), has finished streaming and retains UART R warm reset. Real-camera runs `logs/phase-7/20261114T072933Z` and `20261114T073140Z` each captured 10 consecutive alternating frames with statuses0x101/0x202, no stalls.933120 changed words equals the expected2880×1296 compact RAW10 payload, excluding stride padding. Frame period ~709968us. First RGB PNG inspected but too dark. Second used exposure 32759/VTS32767, analogstage0x5f/digital4x and remained mostly dark; PNG `dut-low-light-preview.png`. No recognizable scene gate claimed. User was asked asynchronously to leave DUT facing a lit scene when convenient, without holding either camera; independent work continues meanwhile.

Pattern run `20261114T073406Z` passed 10 frames but high gain clipped most of pattern (PNG `dut-pattern-preview.png`). A subsequent build to reduce pattern gain hit an inline IRQ-stack literal-pool range error. That command's shell erroneously continued with the preceding image: run `20261114T073531Z` is a stale-image repeat, **not proof of new source**. Fixed initialization using MOVW/MOVT, rebuilt successfully, and started a fresh unity-gain pattern run `20261114T073621Z`; inspect its result/preview before claiming it. All prior capture/build sessions finished except that fresh harness may still be running; verify its handle/status rather than restarting. Host4 tests and observer 7 tests pass; tasks:check295 passed. Generated data in src is reviewable/retained; raw/private image data stays ignored. No Phase 7 completion or commit yet.

Fresh unity-gain pattern run `20261114T073621Z` has now FINISHED and PASSED:10 frames, clean statuses,933120 changed words, complete RGB transport. Decoded/inspected `dut-pattern-unity-preview.png`: visible black-to-white vertical gradient. This verifies synthetic pattern delivery/packing/preview in darkness, not natural-scene or true-color fidelity. IRQ-stack MOVW/MOVT change also exercised through timer/UART initialization. All live harness/build sessions are finished; no need to poll old handles. DUT sits in completed camera-pattern payload, streaming stopped; UART R reset available. Pending user physical-light question remains optional while independent register/dump work continues.

## Latest register snapshots and REF-matched clock run

Built/loaded `bm_snapshot_clocks` from /tmp using public clock APIs, holding12 CIF,2 CSI0,1 PHY and 4 ISP clock references and original module owners. No device detach/reset/rate requests. Pre-capture passed. Full VICAP/CRU/GRF reads passed. IOC declared resource0xff538000+0x40000 faulted in the userspace read at0xff570000 (external abort), after 229376 bytes. Scan stopped, clock helper automatically unloaded, REF stayed responsive/taint4096 and original 3.98MB capture passed. No reset was needed. Evidence `ioc-range-read-health.txt`, `post-ioc-read-capture.txt`. Do not retry that address or call the original IOC range complete.

Updated helper rejects full IOC request; `ioc-prefix` reads0x38000 bytes and records the tail gap. Reloaded clock references, collected complete PMU/DPHY/CSI0/ISP resources and IOC prefix. Captured all 8 profiles during a30-warmup REF raw stream; each block's state receipt confirms runtime active, CIF capture bit set, taint4096. All framed payloads pass length/CRC validation. Clock helper unloaded successfully and original post-capture passed. No bm modules remain on REF. Files `ref-dumps/{idle,streaming}-full/{manifest.json,registers.txt,*.bin}` plus raw framed data/state receipts in `*-full-frames`; generated root `idle.txt`, `streaming.txt`, and `idle-streaming-diff.json`. Full resource bytes except IOC tail; status/read effects and non-atomic block times remain relevant. Snapshots are not unconditional replay tables.

Snapshot comparison exposed actual REF sensor-clock mux at 24MHz despite driver mode's nominal27MHz. Camera replay now explicitly selects xin24m after initial I2C init; Phase5-only I2C setup retains its original27MHz. Added selected configuration readbacks after stream-on. Run `20261114T075157Z` FINISHED/PASSED10 frames at ~799203us steady interval, no FIFO error statuses. `dut-selected-comparison.json` validates32 readbacks against manifest-checked REF binaries: zero mismatches after documented register masks, DMA remaps and polling INTEN0. Dynamic W1C status excluded. PNG `dut-pattern-reference-clock.png` decoded/inspected: same sensor-generated gradient. Source+manifest hashes retained in comparison. Not full-state/scene qualification.

Current DUT is this completed camera-pattern image, stopped streaming, UART R works. REF healthy/original modules, no helper loaded, taint4096 persists historically. All current build/capture sessions finished. Host check now 6 tests passes; CRC/resource/truncation checks and comparison mismatch/manifest sensitivity covered. Phase 7 still needs recognizable real scene (optional light question pending), documented handling of IOC resource gap, and named driver replacement maintaining the raw gate. Do not begin Phase 8 yet. No phase 7 commit yet.

## Latest: named driver verified; real-scene gate blocked by darkness

Normal camera builds now use original named modules `src/camera/{sc3336,receiver,sensor_mode}.rs`, not timestamped trace replay. Sensor reset/mode preset, VTS/exposure/gain/orientation/pattern control and streaming are explicit; one-byte combined I2C register reads verify9 actual controls before start. Receiver names RAW10 fields, sizes/stride, DMA slots, lane/packet configuration and D-PHY settings. Capture rejects both-end/missed-frame conditions, repeat slots and >1.2s intervals after the initial5s deadline, in addition to FIFO/timeout/stop errors. Manifests now hash nested Rust modules. Prior working image retained in `build/phase-7-replay-baseline/`; optional legacy feature compiled successfully (unused named-code warnings), not reloaded. Its Cargo ELF changed, but packaged hello-download.bin/manifest remain the last named real-camera build; always use the build task before a new load.

Pattern run `20261114T080339Z` and real run `20261114T080816Z` FINISHED/PASSED10 clean alternating frames, expected933120 changed payload words, complete preview, nine sensor controls correct and 32 selected receiver/config matches. Pattern PNG inspected: same synthetic gradient. Real PNG `named-driver-low-light.png` inspected: still unrecognizably dark, despite readback proving exposure 32759, VTS32767, gain stages0x5f/0x03/fine0x80 and pattern disabled. No recognizable real-scene gate, Phase 7 receipt/commit or Phase 8 work is authorized by these results alone.

Added separate PMU IOC/GPIO0 resource0xff388000+0x1000 to both snapshot states; CRCs validated during original REF raw capture, helper removed, post-release full raw capture passed (`post-pmuioc-capture.txt`). REF no temporary modules, original stack healthy, taint4096 unchanged. `audit_ioc_coverage.py` ties source hashes and actual snapshot hashes to all SDK-known GPIO drive/pull/Schmitt fields and conservative IOMUX bounds: covered at idle and streaming. Main IOC last source-known GPIO4 field offset0x300a8 fits within captured 0x38000 prefix; faulting/unprobed tail remains explicitly excluded, never synthesized. See [camera-registers.md](../hardware/camera-registers.md) for scope.

All current build/capture processes finished. Host6 tests and task295 validation pass; observer 7 tests checked again. [phase-07-camera.md](../bringup/phase-07-camera.md) contains requirement-by-requirement state and exact resume steps. The same physical scene blocker has persisted through the initial replay, range-snapshot/comparison and named-driver goal turns; it was revalidated by the latest real-camera PNG. Remaining Phase 7 visual qualification requires the pending physical lighting/orientation action. Do not substitute the pattern or start DUT Phase 8 work. The plan explicitly permits reference-capture work on REF in parallel, so the full goal remains active while preparing that comparison evidence; do not mark it blocked while that meaningful work is available. No phase 7 commit yet.

## Allowed parallel REF ISP reference capture

Inspected installed camera-probe help, current pipeline plan and local Rust source. Pipeline is CIF raw TX0 → raw RX18 → ISP3, params20, image 11, stats19, SOF subdev0. Factory IQ exists at `/etc/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json` (432259 bytes). `configure-pipeline ... --dry-run` passed without writes. Reference capture is explicitly allowed in parallel by PLAN; **DUT Phase 8 has not started**.

REF ISP image 11 was native 2304×1296 NV12/4,478,976 bytes. Set normal V4L2 output format640×480 NV12/460800 bytes for this board's12MiB CMA budget. Ran installed Rust `first-frame-sc3336` with pipeline/IQ/params20/image11 and output`/tmp/bm-isp-fixed.nv12`, environment `SHIELDSIGNER_IQ_MODULES=none` (optional bay3d/ynr/cnr/sharp disabled). Succeeded: three raw bridge completions, no cleanup errors, held Rust-generated11145-byte parameter buffer completed, fixed ISP frame saved, taint4096. Explicitly automaticExposure/WhiteBalance=false, coldStartProven=false, frameApplicationVerified=false—do not upgrade those claims. Saved frame/metadata/initial params/report under local ignored `logs/ref-isp/`; command log `logs/phase-7/ref-isp-fixed-capture.txt`. Existing Rust frame-preview decoded luma; PNG inspected, very dark (mean 1.7465/255). Not an image-quality or3A-convergence gate.

Original raw capture after fixed ISP run succeeded (`ref-raw-after-fixed-isp.txt`), so REF remains healthy/no helper modules. ISP output stays VGA now; sensor controls were changed by the fixed-startup tool—latest actual controls are `ref-controls-after-fixed-isp.txt`, not the previous low-light reference values. Pipeline changes are runtime-only; normal capture APIs used, no module teardown or storage writes. DUT remains stopped in named real-camera payload with UART R. All current tasks finished. Next useful allowed work: reference statistics/automatic Rust3A capture, with bounded outputs/CMA and no vendor processes, plus records needed for eventual DUT ISP comparison. Keep the real-scene question pending and Phase 7 unpassed.

## Latest reference baseline and physical blocker audit

Automatic REF AE/AWB capture FINISHED successfully: `logs/ref-isp/auto-capture.txt`,33 raw completions, dropped 0,22 statistics,21 parameter submissions, clean teardown, taint4096. Pulled10 frame/parameter/stats/AWB artifacts. `auto-summary.json` validates output length, saves hashes and preserves qualification limits. AE has 14 exact exposure lookups/22 records,19 decisions; final record lacks exact association. CLI physicalApplicationVerified=false; no convergence claim. Auto luma PNG inspected: mean 31.23/255, mostly noise versus fixed mean 1.7465. No usable natural-scene qualification.

Held normal clock references again and ran fixed capture-cif-with-parameters using the original fixed 11145 byte parameter buffer, sensor VBLANK64/exposure122/gain128 and VGA output. Saved full32512 byte ISP resource while runtime active/CIF enabled, framed CRC/hash validated (`fixed-registers.jsonl`, `fixed-register-snapshot`).91 raw completions/no drops/cleanup errors. Helper unloaded; subsequent original 3,981,312 byte raw capture passed. Final REF state healthy/no bm modules, taint4096, controls64/122/128; ISP output640×480. DUT remains stopped in named real-camera image from20261114T080816Z, unchanged, with UART R available. All current jobs finished.

Reference AWB audit identified read/write representation differences: SDK writes packed16-bit channels, while AWB1 reads at 0x530/0x534 show12-bit spacing. SDK hw.c explicitly excludes these from ordinary restore. Six channel pairs/enable state match after interpretation; gain 2 pair readbacks remain unresolved, not silently accepted. Do not blindly copy ISP register dumps into writes. See [reference-isp.md](../hardware/reference-isp.md) and fixed-awb-audit.json.

The explicit parallel-reference-capture exception has now produced the fixed frame/parameter baseline, automatic statistics/control records and active ISP register snapshot needed for later comparison. Repeating dark captures adds no visual evidence. The same illumination/scene blocker has persisted over more than three consecutive goal turns and was revalidated in both named DUT and REF automatic previews. Remaining Phase 7 visual gate needs the user's pending physical lighting/orientation action; one-phase-at-a-time rule prevents starting DUT Phase 8. Mark the full goal blocked rather than keep producing repeated dark captures. This is not completion or a user-requested pause. Resume from [phase-07-camera.md](../bringup/phase-07-camera.md) when the scene is lit; no phase 7 gate commit yet.

## User resumed: lighting changed; colourful target still needed

User said “ok go ahead.” Treat as a fresh resumed blocker audit; do not reuse the old three-turn count. REF reachable after~30600s uptime, original modules/no bm helpers, taint4096. Rebuilt and RAM-loaded named real-camera payload. Run20261114T150900Z passed 10 frames but night profile now clips completely white, proving scene illumination changed. Preserved that image/manifest under build/phase-7-night-baseline.

Separated night settings behind camera-low-light feature/task. Normal camera-test now uses unity gain; run20261114T151123Z with 1024 exposure lines was dim but showed real edges. Increased to 8192 lines at unity for run20261114T151455Z:10 clean alternating frames,9 control readbacks,933120 changed payload words and 32 selected register matches. Raw PNG inspected: pale/greenish surface with edges and a small circular feature, not a clearly identifiable high-contrast colourful scene. Do not claim Phase 7 passed. Asked user asynchronously to rest DUT aimed at a colourful book/box/printed card/lit screen; no holding. This is a physical target/orientation request, not an electrical rewire.

Added audit_raw_capture.py for independent frame/control/marker checks; its output is mechanical evidence only and always requires visual review. Negative test initially changed the first frame's allowed startup interval, so corrected it to mutate the second frame; all 7 host tests now pass.296-task check passed. Low-light feature compiled only after this change, not reloaded; it changed the Cargo ELF but not the packaged current unity/8192 camera-test image. All current processes finished. DUT remains stopped in that payload, UART R available; REF unmodified by these tests. No new blocked-status update or phase 7 gate commit in this resumed turn. Next: recapture the colourful target, inspect actual PNG, then finish receipt/commit if the full gate is satisfied.

## Latest: Phase 7 passed; user requests8 then 9

User repositioned target and asked “how bout now.” Rebuilt/RAM-loaded run20261114T152545Z:10 clean alternating frames,9 sensor readbacks,933120 changed payload words, complete preview,32 selected register matches. Decoded/inspected PNG: printed carton label/barcodes and contrasting surrounding material recognizable, real scene (pattern register0xc4, bit3 clear). Raw Bayer tint is uncalibrated, as expected before ISP. Recorded evidence/phase-7.json with firmware/serial/preview/snapshot hashes and explicit limits; private scene pixels stay ignored/local. Current DUT stopped in this named camera-test payload, UART R recovery works. Phase 7 passed; no claim of ISP/3A/interpreter qualification.

User explicitly said to keep going on8 and 9 after final checks. Finish Phase 7 checkpoint commit, then implement Phase 8 ISP/YUV/stats/parameter path using existing Rust3A; do not stop at a plan. Phase 9 follows its hardware gate, with RustPython feasibility consideration already in [phase-09-runtime.md](../bringup/phase-09-runtime.md). Preserve original full mission/Phase10 and RAM-only restriction; no SD/flash writes without explicit approval. REF original stack healthy/no temporary modules, historical taint4096. Reference captures/parameter buffers/stats/active ISP snapshot available in logs/ref-isp. Key trap: AWB1 read/write representations differ; do not blindly replay readback bytes. Main IOC faulting tail remains explicitly excluded with all SDK-known fields covered. Goal tool metadata may still show old blocked status; user has explicitly resumed work—do not infer current physical blockage from stale metadata.

## Phase 8 in progress: first offline ISP image

Phase 7 committed as73fa249. Expanded live observer with 9 pinned ISP helper sites (27 total),8-op bounded prediction and 4 module owners. Offline emulator tests cover selected sites; actual idle apply/restore/unload and original capture after restore passed. First fixed traced capture:1365 events,1160 ISP writes, dropped 0/errors0, clean restoration and subsequent original capture. Automatic REF capture:16374 events, dropped 0/errors0, clean restoration/unload,33-frame CLI success. These are partial helper traces, not every direct ISP register store. No original camera modules unloaded. REF taint remains historical4096.

Generated explicit first-trigger fixed 1103 and measurement1483 write profiles; never replay readbacks. Buffer roles remap Y/UV/RAW/stats, preserving other literals. Added original bounded offline ISP diagnostic, gated feature/task, normal noncacheable DMA48–64MiB, ISP-only CRU reset/gates and internal clock enable learned from SDK register definitions. DUT run logs/phase-8/20261114T155539Z completed raw10, ISP main-path output,115182 changed NV12 words, MI status0.160×120 luma preview decoded/visually inspected: carton/barcode clearly recognizable. This is only fixed-parameter offline processing; no Phase 8 pass, no automatic3A claim. Raw sensor remains stopped after capture; UART R recovery available.

Existing shieldsigner-rkaiq compiled for armv7a-none-eabi with default-features=false (libm only); integrated actual library as optional dependency. Measurement/ISP+MI IRQ diagnostic is currently being hardware-tested. Kernel stats metadata is software generated; derive validity from real per-block DONE bits before using existing statistics decoder. Do not treat arbitrary DMA trailing bytes as valid metadata. Phase 9 runtime porting waits for Phase 8 hardware gate; RustPython assessment remains [phase-09-runtime.md](../bringup/phase-09-runtime.md). No flash/SD writes.

## Phase 8 progress: calibrated decisions and first feedback

Actual DUT stats/IRQs passed20261114T155848Z. Calibrated AE/AWB decisions passed20261114T160411Z; HTS read1250×2=2500, measured frame803112us at VTS32767 implies effective pixel clock102.0001MHz. Existing library profiles now compile without std through alloc-only serde_json; host diagnostics retain std. Necessary small shared-library changes expose existing profile/session code (no algorithm replacement); seven fractional-integer checks use equivalent libm truncation.114 host library tests passed.

Feedback runs160849Z/160959Z failed timing validity: u64 frame_us became corrupt. Offline emulation verified division helper; disassembly showed ISP's >64KiB stack frame crossing IRQ stack3f0000. Moved IRQ stack to 200000 with SVC400000 and unmapped 2–3MiB guard; fault entry switches to known SVC stack for reset. Run161302Z then passed six feedback frames/five frame-IRQ gain updates, sensor gain/exposure readbacks and discarded two settling frames. AE last two proposals816/gain901; AWB still changing. Partial FAST-only diagnostic, not full Phase 8.

Extended normal time-share mapping: original pure ISP32 packed-parameter adapter,82 writes independently compared to traced REF configuration, unsupported changes rejected before output. First longer run161808Z stopped after frame 1 because block XY selector0x238 also changes; added its 0x5004 mapping and rechecked. Latest32-frame retest pending. Stage9 still waits Phase 8 gate. Current captured images/logs private/ignored, no storage writes.

## Latest: Phase 8 bounded linear gate passed, continue Phase 9

Final run20261114T163158Z passed 32 normal-timing feedback frames: VTS1360, HTS2500, measured 33333us (~102.00102MHz effective pixel clock). Initial sensor122-line exposure now agrees with the calibrated session instead of starting at 8192. Stop the last raw frame before UART printing; otherwise30fps's short blanking interval allowed the next packet to be truncated and left a receiver size error. The final test passed after that fix.

Normal AWB mapper now handles82 writes, including block XY selector and secondary-region enables; three offline tests pass.31 IRQ-applied parameter updates,186 matching gain readbacks,80/80 selected fixed config matches after explicit hardware masks. CCM readback11-bit coefficients and control high bit also match saved REF raw register snapshot; RAWAE config mask uses only SDK-defined config bits.13 unobserved offsets explicitly not compared. Final controls unchanged over 12 frames:816/gain1065, WB1.2180655/1/1/2.1525512. Within5% AE fromframe10,2% WB fromframe7. Heap used3268384→3407664 bytes; monotonic leakage remains unsuitable for unbounded runtime.

User aimed REF at same target, then explained it must be held. Captured/saved Linux reference immediately and told user to put it down. Final comparison-final.png inspected; recognizable carton/barcode, similar overall brightness/neutral colour with differing angle/sensors and remaining tint/noise. No need to request more holding. Receipt evidence/phase-8.json marks passed-bounded-linear-profile, with explicit exclusions (continuous streaming, general VTS/ISP gain/HDR/module tuning, gain 2 readbacks, long-run allocations).8 host tests,8 observer tests,114 library tests,3 mapper tests,301 task validation.

Commit Phase 8 now, then proceed Phase 9: actual RustPython ARM feasibility build, choose a viable original-plan runtime without forking algorithms, replace monotonic allocator, UART REPL/peripheral/camera bindings and actual script gate. Keep RAM-only, original REF modules/storage and full Phase 10 scope. All harness processes finished; current DUT is stopped after successful normal ISP3A payload and UART R recovery remains.

## Phase 9 runtime implemented; final checkpoint checks

Phase 8 committed df466fe. Evaluated RustPython1d17957399ef02dab4a3ed90622d44437acc6fc1: itsMSRV1.99 required installing a separate unactivated1.99 toolchain/ARM target. Actual no-default-features+compiler VM target check failedE0463 in either:std absent onarmv7a-none-eabi. Explained Ruststd versus Pythonstdlib; user accepted MicroPython. CoreMicroPythonv1.27.0 revision78ff170de9e32c79db6e64d3e33d2bd60002bdcd linked unchanged withoriginalport/CFFI. Newlibbuild-onlyheadersUbuntu22.04libnewlib-dev3.3.0-1.3 extracted locally; no hostlibc linked.

PureREPL loaded164739Z; nonce script console-164900Z passed arithmetic,uppercaseR,allocations,GC,exception. Initialbootcapture omitted script output because its captureexpired; retain as REPL-only boot, notscriptfailure. Added single-reader/writer pasteconsole withbase64UARTframing toavoidADBPTYnewlinechanges. Runtime reset isCtrl-] (0x1d), notR. IRQring4096 bytes.

Reclaimingbuddy_system_allocator0.13.0(MIT),Rustheap4–16MiB,PythonGC16–24MiB,cameraDMA48–64MiB. Legacybump remainsconditional. CPUallocatorhardwarecheck64fragmentedcycles+8MiBcoalescing+OOM passed. NativeThumb2GCregister/stack andNLR helpers; softfloatC/RustABI. Runtime-board skipsstartupcamera/SPItests and provides PythonPin52/53,I2C4sensorread/write,SPI0mode0,hardwaretime,cameraNV12readonlyviews,AEtarget/seedsettings. Cameraoperationssuppressdiagnosticspambutreturnerrors; gain/settingsvalidationand32 framefeedbackstillrun. RepeatedcapturesresetISPbookkeeping, reclaimallRustsessionallocations.

FirstfullREPLscript console-20261114T170029Z PASSED: GPIOpadreadback,cc41ID+samevaluewrite/read,4KBphysicalSPI1/10/50MHz+inplace(alias-safecopy),timer,twoactual460800 byteNV12captures,contrastcheck,target48/seed160settings+sensorreadback,Rustheap0before/afterbothcaptures,GCcyclesandexceptions. Finalcleanbuild/gatewithreadonlyviewtestandbase64consoleinprogress; noPhase9receipt/commituntilcompleted. Imagecurrentlyfitsoriginal1MiBimagebound; stackguardpreserved.

User addedremainingmilestones: microSDstandaloneboot;ADB orUSBdebug/REPLwithoutUARTwires;portSeedSignercodeonREFtoMicroPythonandusePCB LCD/buttons/camera. Recorded [milestones.md](../bringup/milestones.md). Do notcallprojectcompleteatPhase9. Keepknown-goodREFLinux/carduntouched,readactualappbeforeporting,andaskphysicalcard/PCBactionswhennextconcretestepneedsit. REF cameracomparisonalreadysaved;usercanputitdown. NoSD/flashwritesauthorized.

## Phase 9 final verification: capture-window correction

Shortbootcaptures170714Z(8s) and 171755Z(6s) ended duringIRQstartup/DDRbanner respectively. Initially suspectedfirmwareIRQstall; UARTprobe returned@@RESET andRKUART, so no physicalreplugneeded. Downloadtimeconsumes thetotalUARTcapturewindow; these shortwindows areinsufficientfor~830KiBimage. Correctedbootgate to 18s andrecordcommandwalltimes. Do notclaimanIRQfailurewasproven. GICinitializationwasalsohardened toclearallROM/previousenable,pending,activestate andUARTresetnowEOIsitsinterruptbeforewarmreset; finalfivebootcheckisrunning. No cameraaimorrewiringneeded.

Phase 9 checkpoint: five repeated RAM boots and final console-20261114T172550Z hardware API script passed. Receipt: evidence/phase-9.json. Rust heap returned to zero after two camera captures; Python GC/OOM and read-only frame checks passed. No storage writes. Short capture windows were insufficient evidence of a hang; measured RAM handoff/self-test timing is not SD cold-boot timing. Standalone microSD, USB debugging and full SeedSigner/PCB integration remain open.

Phase 10 preparation: fast-start RAM boot173336Z reached initialized MicroPython13153us after payload entry (excludes ROM/DDR). Full runtime hardware API script173414Z passed. Generated validated2MiB raw SD candidate with unchanged DDR plus original runtime; exact stage/header hashes checked and 12 host tests/307 task checks passed. No SD write/insertion; awaiting a spare card and explicit authorization. [phase-10-boot.md](../bringup/phase-10-boot.md) records candidate, size uncertainty and measurement limits.

Phase 10 independent REF GPIO observation173649Z:13094.375us high pulse vs DUT13112us, max within-pulse sample gap130083ns. Whole-capture Linux scheduling gaps retained separately; no power-on/SD claim. Spare-card/erase authorization requested asynchronously; none connected at last read-only disk inventory. REF source-inventory helper was OOM-killed (no other killed process observed); moved all AST analysis to Mac. Original REF raw camera subsequently captured3981312 bytes successfully, taint remains 4096 and original modules remain loaded. Read-only /opt/src snapshot contains 113 Python source files/2,904,054 bytes; local ignored inventory records actual fork/version and imports. No app code changed.

User corrected the interpretation of 13.1ms: current boot and app launch take at least about 30s. Acknowledged that payload-to-initialized-MicroPython is not boot-to-app, and the replacement does not run SeedSigner yet. Updated primary performance reporting to power-on→usable app screen/input and camera readiness, while retaining original power→REPL gate and clearly secondary internal timing. No end-to-end speedup established.

Phase 10 camera timing instrumentation passed on DUT174525Z: init21ms; first processed output702300/765364/710672us; full32-frame captures5320135/5377477/5326094us. Outer Python timer agrees. Full8-marker peripheral/camera/GC regression174614Z passed. These exclude boot/app and are not FPS. User reports 10+FPS Linux and clarified this was just checking; do not rewrite streaming solely for this comparison. No streaming changes made. API metadata and initial-ISP timeout/error rejection added, latest regular-file SD candidate revalidated. Card/erase request remains unanswered; no external card found and no storage written.

User connected spare4GB card (host disk 7,4060086272 bytes) and authorized continuing after image-size explanation. Verified source image/stages and target identity. macOS denied direct administrator helper access before write; staged retry also denied raw-device open with writeAttempted=false. Used installed balenaEtcher through UI, explicitly selected runtime-sd.img and disk 7, accepted expected missing-partition-table notice for raw ROM image. UI reported Flash Completed/1 Successful target. User moved card to DUT before independent host readback; no claim of our own byte verification. Card no longer appears in host disk list. SD-only UART-reset capture180701Z underway, no USB db issued.

Standalone SD runtime confirmed: controlled reset180943Z produced DDR/hello/REPL with no USB db, about 192ms reset request→REPL marker; full API gate181415Z passed. User requested fast onboard LED then 50% slower. Original GPIO3_C6 LED implementation verified at 10Hz in RAM, changed to 5Hz (100ms on/off); final RAM test181916Z showed10 transitions/second and 0 pad errors. Etcher hit a helper-spawn failure; app restart/reselection recovered and final image9406c4fcc7c795ecf519bc4a3b810b7d2b2a06c9bf2bc6ff8643a9917bc7a6b8 flashed successfully. User reinserted card. Controlled SD reset182159Z passed at 195140.75us request→REPL. Full gate182256Z passed all 8 original markers plus LED-during-camera:108 transitions/10801ms,0 pad errors. No independent raw host readback; real SD boot and APIs verified. Cold power-edge/first-frame and app readiness remain open. Current DUT is SD-booted atREPL,LED5Hz, GPIO52/53 released, SPI loopback still installed. REF remains powered/reachable.

Phase 10 cold-rail fixture preparation: verified Mini schematic H2 pin 3=3V3_OUT (pin 1=VBUS5V), REF inputGPIO1_C5/physical6. Added input-only power observer, native32-bit MMIO access, temporary C4/C5 pull-downs, UART TX high-Z plus both UART pull-ups disabled until sensed power rise, exact saved-state restoration, bounded capture and negative timing audits. Real REF TX isolation/restoration and 300ms logic-pulse dry runs passed;17 host tests/312 task checks pass. Orange role is power-sense-pending, original GPIO gate disabled in devices.json and REF helper guarded by/tmp/bm-orange-power-sense. Asked user to unplug DUT, move orange DUT end11→3, then power DUT; other wires and SD unchanged. Live capture process/session85387, folderlogs/phase-10/power-20261114T183856Z, armed for 300s. No real power timing result yet; UART TX can remain isolated if timeout sees C5low. Read POWER-ON-TEST.md and recheck live handle/current GPIO before any follow-up; do not drive REF C5 or clear interlocks while orange may be on3V3.


User deferred cold-power benchmarking and prioritized SeedSigner buttons/LCD/camera, excluding smartcard software. No physical wire was moved. REF UART mux/pulls/direction restored exactly (0x55/0xaaa5/0x300); console-20261114T184604Z confirmed DUT REPL and 5Hz LED. Power observer finished without a power edge; it is not a cold-boot measurement. Unused preparation/tools/tests archived under ignored logs/phase-10/deferred-power-tools. User confirmed the existing board that ran Linux, not the current HOTHMI carrier: bench LCD DC56/RST57, 240x240; button mapping follows PCB-SOFTWARE-COMPATIBILITY.md. Remove SPI loopback and resolve UART2/button pin conflict before connection/output tests.


App/USB checkpoint: user confirmed a third Luckfox Pico Mini A without onboard flash as the app target, preserving the existing wired REF/DUT fixture. USB debugging is explicitly important; implement and verify USB console/script transfer and reconnect before relying on the third board without UART. Existing Linux-tested 240x240 LCD/buttons profile selected; smartcard software excluded. Added app-runtime build feature retaining fast CPU startup while suppressing all GPIO52 timing-output writes (GPIO52 is the bench center button). mise baremetal:app:build succeeded; all 12 baremetal host checks passed. This is preparation, not a running SeedSigner app or USB implementation. No new payload downloaded, SD written, or pin output enabled. Shared build/hello artifacts now contain app-runtime; the existing runtime-sd.img and installed card remain the previously verified fast-boot build. Rebuild fast-boot before regenerating that diagnostic SD image.


USB console preparation checkpoint: original no_std Rust DWC3 device driver and CDC descriptors added behind usb-console feature; foreground servicing at REPL/VM branches/output/delays, bounded buffers/backpressure, Ctrl-C pending exception and Ctrl-] warm reset, retained UART recovery. DMA60MiB reserved outside camera buffers. Host USB paste uploader selects matching development device and saves nonce completion evidence. 3 descriptor tests, cross-build, uploader CLI and 12 existing host checks pass; evidence/phase-11-usb-preparation.json is explicitly HOST-ONLY. No USB payload loaded and no storage written. Last enumeration showed REF ADB only, no maskrom DUT (the verified SD runtime still runs). Asked user to power off DUT, remove spare SD and repower, keeping all wires/REF unchanged, for RAM-only USB testing; no acknowledgement yet. Shared build/hello artifacts now contain usb-console; installed SD remains the verified5Hz runtime. Hardware gate remains open; do not claim usable USB or remove debug wires yet.


USB review checkpoint: still no maskrom DUT on read-only enumeration; no payload download/storage write. Extracted the actual endpoint-zero phase transitions into usb_control.rs and hardened completion direction validation. Five control tests cover descriptor IN/data OUT/status/no-data and wrong-direction/duplicate events;3 descriptor tests and cross-build pass. Updated host-only preparation receipt. Current blocker for hardware proof remains DUT SD removal and repower (request already pending); no new wiring change requested.


USB hardware blocker revalidated20261114T190106Z: host USB inventory exposes only REF2207:0019/ADB0a523b8b23110ffc; rkdeveloptool ld finds no maskrom target and no external card is present on Mac. Actual DUT UART LED gate console-20261114T190106Z passed (10 transitions,0 pad errors), confirming the existing SD runtime remains alive. USB candidate has never been loaded. SD removal/repower request has remained outstanding across three goal turns; no live capture/download process is running. Mark goal blocked pending physical DUT power-off, spare SD removal and power-on; REF/jumpers unchanged. Resume with enumeration, then RAM-only USB candidate load and UART capture; preserve existing wired fixture. No USB, app or cold-power completion claim.


Phase 11 RAM USB milestone passed. DUT0 native macOS CDC enumerated; initial host TX reached REPL but IN stalled because bulk endpoints were configured before bus reset/host configuration. Moved non-control resource/config commands into SET_CONFIGURATION and added full-packet ZLP termination. Final DUT0 boot191709Z/full API USB191721Z passed GPIO/I2C/SPI/two460800 byte camera captures/settings/GC (Rust heap 0). Exact USB output audit191928Z passed46593 bytes with 32768 byte largest block. Ctrl-C from infinite Python loop and 3 serial reopens passed 191911Z. One stress script initially used unsupported slice syntax in minimal MicroPython; fixed the test to exercise transport without slicing, not a USB corruption finding. User added DUT1 Mini A atUSB101 with existing Linux-tested LCD/buttons and aimed DUT0 camera at its screen. Added GPL host-tool patch selecting RAM db by explicit USB location, requiring2207:110c maskrom; storage commands remain unavailable through selector. DUT0 remains 201; REF originalADB untouched. DUT1 USB-only build uses unique rv1103-dut1 identity; USB script192141Z proves actual UART pads input/mux0, IER0 and IRQdisabled. Three reopens/Ctrl-C and USB Ctrl-]→maskrom 101 passed 192218Z. DUT1 currently maskrom, ready for next RAM load; DUT0 remains running tested UART+USB build and camera. Evidence/evidence/phase-11-usb.json (path baremetal/evidence/phase-11-usb.json). No SD write or working SeedSigner app claim. User is leaving; continue autonomously with current hardware and use software reset/reload, no new wiring/aiming requests. Next: LCD/buttons on DUT1, observe via DUT0 camera; preserve all 3 devices and REF source/card.


Phase 12 partial app I/O checkpoint in progress: read [phase-12-app-io.md](../bringup/phase-12-app-io.md) before continuing. USB milestone committed9a9556a. User is away; work autonomously with existing 3 devices, no new wiring/aim requests. DUT1 bench-ui native LCD/button backend implemented, software writes/readbacks pass but camera previews show no recognizable pattern/white/red; optical gate remains OPEN (view close/oblique/cropped, face visibility uncertain). HardwareSPI10MHz config, full ST7789 init, proper len-1 counter, full240x320 backing-RAM fill and optional slow softwareSPI tried. Actual pressed mask 64/Key2 low stable 200 samples; suppress held inputs until release. Frozen seedsigner_port.buttons imports and on-device debounce/repeat/wrap/MPZ256-bit/slice/format/negative display guards pass195043Z.19 host tests pass. Source/runtime uses CORE_FEATURES+MPZ+source lines; freeze manifest selects only own port package; pinned mpy-cross/lib toolchain recorded. No filesystem, full app, physical press or LCD qualification claim. Ccore full peripheral/two-camera/GC USB gate onDUT0 passed 194629Z (before frozen import addition). Latest final frozen-core DUT0 build/boot is running session66646; poll that handle, then run the guarded phase9_gate over USB serialrv1103-dev-001. Do not restart a live handle. Latest DUT1 image/manifest preserved logs/phase-12/dut1-frozen-tested (source current full-RAM clear, test195043Z); DUT1 still running, hardware SPI initialized and solid-red fill requested195100Z. Observer capture195107Z showed no clear fill. One USB reset194311Z did not reach maskrom; liveness194449Z proved DUT1 healthy, helper flush+150ms fixed delivery and reset194512Z passed. USB-only reset no longer waits on unused UART TX. Both targets RAM-only; spare SD untouched. All source changes after9a9556a still uncommitted; finish final check, record receipt/history and commit a clearly partial app-I/O checkpoint.


Phase 12 checkpoint completed for bounded software scope, full app/optical gates remain open. Frozen imported seedsigner_port.buttons passed 195043Z; core MPZ/slice/format/timerwrap, held-Key2 suppression and six display guards passed on realDUT1. Native register readbacks: input directions/pulls/mux matchbench, LCDDC56/reset57 outputs, SPIdivisor20. Full ST7789 profile, len-1 TX counter, complete240x320 backing-RAM fill and optional100kHz-or-slower GPIO SPI diagnostic implemented; no recognizable optical output in current close/oblique/cropped camera view. Don't claim LCD success or infer a proved board fault. Independent observer pixel hashes differ (no stale-frame evidence). Further safe probe found DUT1 ALSO has a responding SC3336: ID195559Z and actualRGB camera195651Z passed (different carton scene fromDUT0's LCD view). Camera is available locally; earlier no-confirmed-camera assumption superseded. Reinitialization/fill after camera195824Z passed; preservation without LCD reinit/continuous preview still untested. Final frozen-core DUT0 boot195253Z and full GPIO/I2C/SPI/two-camera/settings/GC USB195410Z passed; session66646 and 90177 are terminal. All tool sessions terminal, no active captures.19 host tests pass. Receipt evidence/phase-12-app-io.json; [phase-12-app-io.md](../bringup/phase-12-app-io.md) is the current handoff. Current shared build artifacts are final frozen-core usb-console forDUT0, matching its running firmware. DUT1's matching bench-ui image/manifest saved logs/phase-12/dut1-frozen-tested. Both devices reachable via uniqueUSB identities; REF untouched. Preserve originalwiredDUT0fixture, no physical actions needed for independent work. No SD writes. The full SeedSigner app is NOT running: actual controller/views/rendering/models/crypto/QR and app boot/navigation still need porting/verification. Next useful work: native camera→RGB565 app display adapter and actual app rendering/controller integration; keep optical check open and use software reset when reloadingDUT1. User is away and explicitly requests continuing with existing setup; don't stop for re-aim/rewiring while software work remains.


Native camera/display checkpoint: realDUT1 gate 201402.499624Z passed two read-only460800-byte NV12 captures→nativeRGB565→SPI submissions without display reinitialization. GPIO/mux/divisor preserved; Rust heap baseline restored; conversion/blit233/232ms, capture 5255888/5256468us. Not previewFPS, appboot or optical proof. Receipt evidence/phase-12-camera-blit.json;2RGB tests+19 bringup tests pass. DUT1 remains running bench-ui boot201148Z; DUT0 remains committed frozen-core usb-console, REF untouched, no SD writes. Host USB log timestamps now include microseconds after two rapid scripts collided at folder creation (no board script ran on failed attempt). Pinned official Arm14.3.rel1 C++/newlib toolchain installed only in ignored local cache, SHA verified; existing pinned SeedSigner LVGL corpus and existing portability patches compile542objects. Archive/bridge are NOT linked/running yet: allocator, constructors, unwind metadata, memory layout, MP UI module and actual screen/controller gates remain next. Keep native UI initial testing on wiredDUT0 with UART recovery; don't disturb DUT1 button/UART pads or DUT0 GPIO loopback. Current LCD optical view remains inconclusive; user away, continue independent app software. All build/upload sessions terminal at checkpoint. No full app completion claim.


Native Home renderer checkpoint: native-ui firmware runs on wiredDUT0 boot logs/phase-12/20261114T202608Z. Genuine locked main_menu_screen renders, exports read-only240x240 RGB565, and produces Scan index 0 / Right+Enter Seeds index 1 callbacks. Decoded native-home.png visually inspected: correct title/powericon/4tilelabels/icons/orangefocus. Real gate logs/phase-11/usb-20261114T202711.768518Z passed;20 error/render/GC cycles202742.154315Z returned nativeheap42015 bytes exactly; fullGPIO/I2C/SPI/two-camera/settings/GC gate 202747.583864Z passed with samebaseline. Rawimage1486708 bytes/BSSend0x177618 below4MiB; relocatedSVC27..28/IRQ29..30MiB, guards26/28, heaps/DMAunchanged, shadow32MiB. Newlib C allocator uses Rustbuddyheap, constructors invokedafterheapinit, EHtablespreserved. InitialmalformedJSON resetdiagnosed byUART instructionabort202346Z; LLD TARGET2 defaultwasincompatiblewithGNUbaremetalEHABI, --target2=rel fixedrealcatch/recovery (LLVM D149458 reference). Input firstpressdrop fixed by settling releasedkeypad afterscreenhandoff, matchingexistinghost. Initialframeexport20stimeout gave219rows;60sbound yieldedcompletevalidated115200 bytes. First hostprobe usedunsupported time.ticks_diff, correctedtest;5scaptureendedbefore~12sloaderdelay, later20scapturepassed. One UARTprobe overlapped bootcapture and hadsplitoutput; rerun202436Z cleanpassed, don'ttreatmixedlogasproof. Receipt evidence/phase-12-native-ui.json.19hosttests pass. No storagewrites, REF preserved, DUT1 remains nativeRGB bench-ui201148Z. Allsessions terminal. Fullcontroller/app and physicalLCD/buttons notqualified; next moveactualrenderer toDUT1 preservingUSB-onlyUARTpadrelease, thenfreeze realcontroller/viewadapters andexpandactualregistry. Don'tclaim11msrenderasappboot/coldpower. Useraway; continuewithoutrewiringrequests.


DUT1 actual-native-renderer milestone: final app-ui boot logs/phase-11/dut1-20261114T203237Z, frozen cooperative adapter+camera/Home-restore gate 203256.506883Z, final nativeHomeframe203317.045222Z allpassed. Native framehash6d46d67b07a7be9a35e87012261466fb05fd3ca06e3ac7a759fae4562bf62aac matchesDUT0; render+SPI194ms, notappboot. Frozen ScreenSession usesrealMPJSON, debouncedinput→completeLVGLpulses, timers and screenhandoffheldsuppression; constructor initializesbackendbeforedefaultbuttonread. Actualheldmask64 suppressed; injectedacceptededges selectSeeds1. Capturesubmission and Home restorewithoutLCDreinit preserveheap42015 bytes andUARTpadmux/output/IER/IRQzero.22hosttests pass. FoundnativeINVOFF0x20 differedfrominstalledST7789.NORMAL_COLORS_REQUIRE_INVERSION=True; correcteddefaulttoINVON0x21, nootherpins/clockchanged. Opticalobserver203317.045224Z stillhasno recognizableHome incloseobliqueview. Imagesdifferhashesacrosscaptures; notstale-frameevidence. Don'tclaimphysicalLCDsuccess/switchqualification orfullapp. Native registryHomeonly; actualController/View/screencontracts, longhold/lifecycle/models/QR/crypto andstandaloneappbootstillopen. DUT0 remains38bf1edheadlessUI withcameraobserver, REF preserved. Sharedbuild/hello nowfinalDUT1app-ui; wiredharnessnewguardrejectsDUT1/appbuildsbeforeenumeration/db (negativegate logs/phase-12/20261114T203342Z). NoSDwrites, noactiveprocessesatcheckpoint. Receipt evidence/phase-12-dut1-native-ui.json. Nextusefulwork: realappController/View compatibility and configurationadapters + genuine screenregistryexpansion, preserveunsupportederrorsinstead oftoywalletflows. Useraway: continueindependentsoftware, no rewiring/aimingrequiredfornextsteps.


Original navigation/native registry checkpoint: full43lockedbuilders registered on wiredDUT0 native-ui, introspectionui.screens() andmanifest/cachekeyincludeexactlist. Finalboot logs/phase-12/20261114T204128Z; frozenoriginalDestination/BackStackgate usb-20261114T204159.328829Z passed; actuallistDown/Enter,topBack1000,2tileRight/Enter,Homecleanupgate204159.863413Z passed. Sourcegeneratedwholeclassesfrompinned3rdIterationapp, annotations/dataclassruntime removed, equivalent4argconstructor andlistbase; routing/redirection/equality/recursive_sensitive_repr methods unchanged. app/navigation-provenance.json recordsclass/filehashes/transform/output.3differentialtestsagainstactualCPython/dataclassclasses+realfrozengatepassed;25 hosttests total, noskips. Registryavailabilityisnot43workflowqualification. Originalfirstregistrycyclefailedstrictcoldheapcheck; isolated4cycleprofilesstabilized at 52553 afterfontcaches. FinalafteractualtextwidgettestcoldHome43018→warm53300, fivefurtheridenticalnavigationcyclesfixed53300. Textcallbackreviewfoundoldsharedcopyhelpercouldsilentlytruncate>255 bytes; nowexplicitRuntimeError,consumedbufferisvolatilecleared. Actualseed_add_passphrasewidgetKEY3gate204158.658955Z provedexact255ASCII/254UTF8and explicit256 byteerrorsfollowedHome recovery. Widersupportedtext andsinglependingeventslot/lifecycle/contractsremainincomplete; notseed/signingflowqualification. FinalfullGPIO/I2C/SPI/twocamera/settings/GC gate 204221.658896Zpassed withheapbaseline53300. Raw1817316 bytes,BSSend0x1c76d0below4MiB. DUT0runningfinalnewimage; DUT1unchanged54bfdcaHome-onlyapp-ui, opticalLCDstillunconfirmed. Sharedbuildnowwirednative-ui(defaultdevUSBidentity);DUT1loaderrejectswrongbuild. NoSDwrites/REFchanges; allsessions terminal. Receipt evidence/phase-12-navigation-registry.json. Next: actualController/View sourcecompatibility/configuration/resultadapters, settings/model/crypto/QR/storageandstartup;don'tsubstituteatestView/menu/demoappforrealSeedSigner. Useraway, continuewithcurrenthardware.


Basic original Screen contract milestone: frozen screen_contracts mapsButtonList/LargeButton/MainMenuarguments toactualnativebuilders andvalidateschoice/back/powercodes. Originalinheriteddefaults generatedfrompinnedappAST, sourcehashprovenanceapp/screen-defaults-provenance.json. DifferentialtestsagainstexistingLinuxcontracts+originaldataclassfields pass fordefaults/layout/scroll/colors/icons/translationoptout;29 hosttests total. Correctoriginalaccent#FF9F0A nowinappconfig(previousdirectHomefixtureusednative#FFA500default). UnreviewedScreen subclasses, Button_cls styling andconfiguredlong_press_keyraiseUnmigratedScreen; NULtext rejected. ScreenSession show_screen/screen_result/run_screen exposes class+kwargsdictboundary; rawshowclearsbuttoncountvalidator. FullController/View NOTyetwired/importable, fullwalletlogicnotreplaced. RealDUT0 boot logs/phase-12/20261114T204642Z /frozengate usb-20261114T204714.964041Z passed3basicclassconfigs, ButtonOptionfixtureobjects and actualnativecallbackindices/back1000 throughdebouncedinjectededges. Thesearetestfixtures, notproductionViewsorphysicalswitchproof. Rawimage1821140 bytes;nativeheapaftergate53037(onlycurrentfixturemix, notanewglobalbaselineclaim). Finalsharedimage/runningDUT0 native-ui containadapters;DUT1unchanged54bfdcaHome-onlyapp-ui,opticalstillopen. NoREFchanges/SDwrites;allsessions terminal. Receipt evidence/phase-12-screen-contracts.json. Next integrateactualController/Viewrun_screen/servicesandremaininggenuinecontracts/dependencies; alsoQRdecoder/models/crypto/settings/storageandcompleteappboot. Preservefullscopeandavoidtoyappsubstitution; userawaycontinuewithcurrenthardware.


Original settings dependency checkpoint: source-derived wholeSettingsConstants/Entry/Definition(60 entries) andoriginalSettings.parse_settingsqr frozen asportSettingsQR. Originall10nmarkerretained; noLinuxOS/peripherymock:explicitrealhardwaremetadata+English-onlyfrozenlanguage discovery. ExplicitEntryconstructor/eqNotImplemented/repr replaceCPdataclassruntime, methods/provenancepreserved. Parserloggingremoved; realfloat64conversion or explicitunsupported error, nofakefloatparser. NativeUI/appUI MicroPython nowdouble+fullpinnedlibm; globalNotImplementedconstantenabled. Originalschemafloatconstantswouldbreakminimalfreeze, sohostMakefileexportsBM_NATIVE_UI andmanifestonlyincludeschemaforappbuild. MinimalMParchive+configuredusb-consolelink andfinalnativeUIbuildpassed. Initialbaselinecargo--manifestfromrootdidn'treadbaremetal.cargo config; reranpropercwdconfiguredcheck, useonlylogs/settings-baseline-link-configured-check.txt asbaselineproof. Nativefreeze/source changeschangedimagehashaftermatrixbuild, soexplicitlyreloaded/retestedfinalartifact. Finalboot logs/phase-12/20261114T205505Z; actualschema/parser/double/30GCcyclesgate usb-20261114T205541.162242Zpassed, entirepublicschemaauditedexact60 entries SHA d029fa08de4ecfefdefe1805ac712c1efa5a8bc2ebf1a081e62ffa8c0be5b1a9. Nativeheap1120beforeUIfontinitfixedacrossparsercycles.32hosttests(3newagainstactualoriginalschema/parserclasses)allpassno-skips. Screenadaptergate205544.153536Z andfullGPIO/I2C/SPI/twocamera/settings/GCgate205544.787006Zpassed. NoSettingssingleton/apply/setter/persistence/platformeffects portedyet; rawSettingsQRFREE_ENTRYdoesnotenforceminmaxuntilsetter, metadatafloor10/ceiling1000preservednotclaimedcryptovalidation. Schemahardwarechoicesinertupstreammetadata, noall-driverpromise; smartcardsoftwarestillexcluded. Finalraw1879284 bytes/BSSend0x1d76d0below4MiB; currentDUT0/sharednativeUIartifactsupdated, DUT1unchanged54bfdcaHome-onlyappUI,opticalopen. NoREF/SDchanges, allsessions terminal. Receipt evidence/phase-12-settings-schema.json. Next actualSettingsnativeRAMstore/platformservices+Controller/Viewstartup/model/QR/cryptoprereqs; keepfullappscope, nofakeproductionViews orcryptofallbacks.


User supplied actual PCB path in sibling seedsigner-luckfox-pico repo. Read-only PCB pads/schematic pin names establish LCD reset 51/DC52/backlight43, CS48/SCK49/MOSI50; keys57/59/56/54/58/55/4/53. This differs from earlier assumed bench profile; prior dark-LCD/stuckmask64 observations were wrong-board configuration, not a proved panel fault. Reset DUT1 to release wrong56/57 outputs after restricted Pin API could not quiesce them directly. Added explicit mini-pcb-ui/mini-pcb240, GPIO0_A4 input forKey2 and high backlight43; old profile and fixtureGPIO/SPI APIs reject on app target. Physical white/Home/static-camera images now visible; user ready+k and exercised every key, monitor usb-20261114T211837.412363Z sawmask255 plus real selection/powercallbacks. Native UARTmux/IER/IRQ0; GPIOB3 intentionally backlight output0x800, so old all-input assertion superseded. FinalDUT1boot dut1-20261114T212458Z and gates 212601/212602/212603/212604/212605 passed white/Home/guards/RAMsettings/camera→Home restore. Same src/display.rs hash as physical button-tested image. Current source/artifacts app-ui forcorrectMiniPCB; DUT0 still headless observer. Source board unchanged, noSDwrites. Receipt evidence/phase-12-mini-pcb.json; [mini-pcb-io.md](../hardware/mini-pcb-io.md) is current pin authority. Background RAMSettings port also passed36hosttests, original numeric/multiselect/update/getter comparisons, real board bounds/atomic native-action rejection and 30GC cycles. No persisted settings or device-side effects; source prefix and explicit native policy only. FullController not wired. User now explicitly requests working preview: prioritize persistent sensor/ISP and repeated display updates, not repeated5s captures. Commit checkpoint before streaming work.

2026-11-14 preview/QR continuation: persistent local camera→Mini PCB LCD now
passed90 frames at 3.769FPS, with Home/heap recovery and USB Ctrl-C cleanup.
Checkpoint1b83f0e; receipt evidence/phase-12-continuous-preview.json. Demo exited
294 frames/88036ms via its early button-exit path. New native QR foundation uses
pinned Linux ZXing-C++3.1.1 (same source, no Linux, automatic scratch vectors).
Real DUT0 fixture gate usb-20261114T215146.102523Z passes exact text/binary,
rotation/inversion/bounds/no-code and heap stability after 36616B immutable cold
lookup-table allocation. No real optical QR yet:20 attempts of DUT1 public QR
failed; observer usb-20261114T215123.438611Z shows small/oblique/blurred panel.
Full-frame decode220–261ms vs small fixtures3–13ms. DUT1 Home restored, still
1b83f0e app-ui preview firmware. DUT0 headless native-ui includes QR. Shared
build artifacts are wired DUT0 identity; do not load them on DUT1. No SD writes.
Next: actual original DecodeQR/ScanScreen/View model integration and optical
qualification; do not replace original app workflows with a fixture menu.

2026-11-14 original Scan dependency checkpoint: native app builds now provide
proper Unicode strings/UTF8 validation and PCRE2-backed re matching/groups for
original decoder patterns. DUT0 boot 215832; regex gate 215951.910578Z passed
CPython pattern/group/span outputs, invalidUTF8, capture/flag/type limits and
per-operation heap baseline. QR/UI/RAMsettings regressions and36hosttests pass.
[regex-unicode.md](../app/regex-unicode.md) documents exact API/limits and the two-local-type PCRE2 ARM
portability patch. Receipt evidence/phase-12-regex-unicode.json. Sharedbuild is
wired DUT0 native-ui; DUT1 unchanged working preview app-ui, Home restored.
NoSDwrites. Original DecodeQR/ScanScreen model/Controller integration still next;
do not confuse dependencies or fixtures with complete general Scan readiness.

2026-11-14 original Scan integration: all 27 original DecodeQR classes generated
from pinned source that matches REF snapshot byte-for-byte, plus original
ScanScreen._run with explicit cooperative camera/clock/input boundaries.44host
checks pass. Pixel→ZXing→original model/loop public fixture gates pass on both
boards; DUT1 final usb-20261114T221552.594573Z. Real camera scan interrupted cleanly
on DUT0 after 7 frames and DUT1 camera/LCD after 19 frames; heap returns and Home
restores. NativeDataImport FeatureUnavailable guards prevent missing crypto/UR/
Seed/Controller deps becoming false INVALID; these features remain unported.
[scan.md](../app/scan.md) has full contract/gaps. Shared artifacts are app-ui/DUT1 serial;
DUT1 boot 221157. DUT0 headless native-ui boot 220856. NoSDwrites.
User put a printed QR in DUT1 frame: native 30/240 frame passes failed. Full snapshot
user-qr-dut1-latest.png retained in ignored logs; contains wholecode. Earlier
clipping diagnosis was wrong, corrected to user. Desktop pinned ZXing also finds
QR but fails Reed-Solomon checksum;29image variants fail. Quirc diagnostic finds0.
No decoded payload logged or committed. Asked via async input for flatter/more
front-facing/larger QR; software work can continue if user unavailable. Original
opticalknown-code qualification still pending, along with scan overlay/instructions,
real BaseScreen/View/Controller routing and all wallet/crypto/UR/SD app workflows.

2026-11-14 hash prerequisites: no_std RustCrypto core + native MicroPython
hashlib/HMAC/PBKDF2 now hardware-proven on DUT0. [hash.md](../app/hash.md) and hash-core/UPSTREAM.md
have API/bounds/provenance.3Rust tests include216upstream PBKDF2 comparisons;
44 host tests pass. Finalboot224658, vector gate 224802.460807Z all6algorithms and
empty-buffer/copy/GC cases pass; public BIP39 SHA512/2048=56ms derivation-only.
Million-round KDF Ctrl-C recovery gate 224932.534807Z passed (~0.11shost bound,
0.1sread resolution), with no double exception, fresh hash and native heap baseline.
UI224951.332648Z and originalQR225049.291412Z regressions pass. Shared artifacts
are now wired DUT0 native-ui/defaultUSBID; DUT1 remains16b2986 app-ui/Home.
NoSDwrites. Pending physical QR reposition/larger known-code question can wait;
no optical success claimed. Next real model dependencies: actual NFKD normalization,
embit/BIP39/curve and UR components; do not substitute identity normalization or
fake crypto, or equate primitive vectors with complete seed/signing readiness.

2026-11-14 Unicode15 normalization prerequisite: native actual Unicode15.0.0
algorithms match REF CPython3.12.10's database. API/REF oracle gate 230549 passed;
all19074officialrows/381480relations passed in6380ms at conformance230617 with
native heap baseline. [unicode.md](../app/unicode.md) and evidence/phase-12-native-unicode.json
record scope. Unlisted scalar identity sweep230927 exceeded180s host capture;
no device terminal result yet, so full conformance remains pending. Follow-up
reader/query sends no Ctrl-C/reset; preserve running computation. Default future
sweep deadline1800s. Host44tests passed. New wiredDUT0 image a517f9bc... loaded
230443;20sec UART window too short, subsequent USB gates prove actual execution.
DUT1 demo stopped after user said done; Home restored via USB231220, cameraoff.
No further user aiming needed to continue dependencies. No SD/CAD/REFstorage writes.
Next: finish scalar sweep observation; original embit/BIP39/Seed dependencies,
including exact original passphrase escape handling, remain incomplete.

2026-11-14 BIP39 leaf: actual embit0.8.0 (MIT source/license/hash preserved),
English2048wordlist frozen; annotations removed and const imported directly from
micropython to avoid unrelated eager curve backend. DUT1 app-ui image9aac35e9...
boot 231820 appeared after 20s observation window; later API gates passed without
reload. Observer now 40s. BIP39 public24English vectors+5Unicode passphrases pass
231855; Unicode231905,hash231906,UI231908,originalQR/scan231935 regressions pass;
44 host tests pass. [bip39.md](../app/bip39.md) has scope; not Seed model/curve/signing readiness.

Unicode identity diagnostic: original chr(cp) test interns every codepoint in
MicroPython (modbuiltins.c:145 calls mp_obj_new_str_via_qstr). This grows persistent
qstr pools and slows sweep. Stopped via Ctrl-C based on this source diagnosis,
not timeout alone; recovery231940 shows cp258721/scalars239644/checks958578 and
responsive interpreter. DUT0 retains these qstrs until a clean RAM reload (runtime
has no actual mp_deinit soft reset); don't assume gc reclaims interned strings.
Corrected sweep creates UTF8 bytes then decodes without interning; uses fresh
DUT1 image and serial selection. Running identity231941; no terminal result yet.
DUT0 now idle prompt, DUT1 console exclusively owned by this sweep. NoSDwrites.

Unicode sweep completion: corrected DUT1 identity231941 passed1095035scalars /
4380140 relations in83586ms with Rustheapbaseline. Combined with19074published
rows/381480relations, supported UTF8 scalar normalization meets both published
conformance requirements. Receipt and [unicode.md](../app/unicode.md) updated. Native Unicode
version stays15.0.0 matching REF; no wholeunicodedata/Seed/wallet claim. DUT1 USB
reader now free. DUT0 idle but qstr-heavy until nextRAMreload.

2026-11-14 exact original passphrase boundary: native helper implements original
Seed.set_passphrase's regex+raw_unicode_escape/unicode_escape+NFKD result forUTF8
scalars. Malformed lower-u escapes restore wholeinput; upper-U/other escapes stay
literal; surrogate outcomes explicitlyfail (CPython cannotencodeUTF8 forseed).
10khost differential cases+515actualREF stdlib cases;47 host tests pass. Native
DUT1 finalgate232451 passes515REFcases+32fullpassphrase→embitBIP39 derivations,
heapbaseline. BIP39regression232455,QR/scan232524 pass; Home232458 restored,cameraoff.
[passphrase.md](../app/passphrase.md) and phase-12-passphrase receipt record provenance/scope.
DUT1 RAMimage60f75644...,load232400passed40senumerationwindow;sharedartifacts target
app-ui/DUT1. NoSD/CAD/REFstoragewrites. Allconsole readers finished. DUT0 remains
idle1d46a06 native-ui image withqstrs frombadchrtest; nextDUT0 workmustcleanRAMreload.
Next originalSeed blocker: secure_delete usesCPython ctypes/refcounts and cannot
be silentlystubbed; need realnative memoryownership/wipe policy. RealBIP39,
normalization andpassphrase boundaries nowproven, but originalSeed/alternate seeds,
curves/roots/UR,Controller/Viewrouting andopticalQR success remainunfinished.

2026-11-14 originalSeed/nativeclearing: all originalSeed classes/methods retained
fromguardedsource viaAST; actualBIP39Seedconstruction/regeneration/eq/disposal now
native. Sourcebindingsdeferredexplicitly, unavailablefeaturespropagate, passphrase
boundaryREF-tested. [seed.md](../app/seed.md) andphase-12-original-seed receipt scope details.
DUT1imageab515da0...,RAMload232910. Memorygate232932passesvolatileclearGC-owned
bytearray/bytes/UTF8str,2048wordlistguards,frozenbytes/text guards,neighborintegrity,
100GCcycles. FirstgateusedREPLliteralasfrozenprobe (wrong: heapconstant), corrected
byactualfrozenfixtures; nativeallocationguardwasworking. OriginalSeedgate232943
passes24publishedvectors+32REFpassphrasecases, regeneration/eq/invalidinputs, real
seedbytealiaszeroingandpostwipewordlistvalidity;48hosttestspass. QR/scan233015 and
passphrase 233016 regressionspass;Home233021,cameraoff. Allreadersfinished.
NoSD/CAD/REFstoragewrites. Cwipe accepts onlyGCHEAD-ownedobject/data; frozen/qstr/
externalbuffersskipped. NoCPythonrefcounts; callerdiscardsaliases andmustnotwipe
keys. Copies/temporaries/internsnotpromisederased. Noerase/walletqualification.
SharedartifactsDUT1app-ui. DUT0olderUnicodeimageidle/qstrheavyneedsRAMreloadbefore
futuretest. NextgenericQRdeps:PSBTframing,SLIP39wordlist/importboundary,Aezeedchecksum;
DecodeQRcompactbranchhasleftoverlogging.info toremoveviaexistingloggingboundary.

2026-11-14 originalPSBTframing/numericSeedQR: frozeactualembit0.8.0 base,compact,
hashes,networks,Base58/Bech32,script,transaction,EC/BIP32models,PSBTsource. Curve
moduleimportdeferred; actualmethods/NUMSpublicpoint expressionraiseFeatureUnavailable
untilrealbackendexists, nofakekey/signature/entropy. OriginaleagerNUMSinitialization
broke firstparserimageload ofSeed; correctedmodule__getattr__computes/cachesexact
originalpointwhenrequested, guardgateprovesexplicitfailure. Wholeoriginalstrict
framingmodule+actualRejectCode/InvalidPSBTErrorclasses ported. FullPSBTParser remains
unported. BytesIO.getbufferlen ->seek/tell/restore only; OrderedDictenabledactualC.
15 nativefixturescomparewholeoriginalCPythonchecker:2v0/v2roundtrips, strictduplicate/
nonminimal/mixedversion/impossiblecount/trailing/truncation/badmagic casespass.
Numeric12-wordSeedQRnowpasses ORIGINALgenericclassifier/SeedQrDecoder/Seedvalidation.
Noopticalsuccessclaim. Loggingboundaryalsoomitsleftovercompactlogging.info.
FinalDUT1image553bfe12...,RAMload233756;gate 233824,Seed233819,memory 233825,original
QR/scan233826 pass;Home233827,cameraoff.50hosttestspass. Sourceprep/provenance and
[psbt-framing.md](../app/psbt-framing.md)/phase-12-psbt-framing receipt recordall. SharedartifactsDUT1;
DUT0olderUnicodeidle/qstrheavyneedsRAMreloadbeforefuturetests. Allreadersfinished.
NoSD/CAD/REFstoragewrites. Next:actualSLIP39wordlist+importlibboundary for textseed
classification,Aezeedchecksumfor24-wordambiguity,compact/encrypted/URdeps, full
Controller/Viewrouting andrealcurves/entropy. Currentnumericgateinjectsdata only.

2026-11-14 — Original mnemonic recognition and SLIP39 recovery
REF's Shamir package is the OS-pinned 3rdIteration 0.3-setuptools fork (reported
version 0.3.1), not the PyPI 0.3.0 release. Downloaded archive matches the OS SHA;
read-only REF wordlist SHA matches exactly, saved under phase-12 logs. Full core,
share, cipher, wordlist, recovery and original Aezeed source are frozen with
licenses/provenance. Immutable record representation replaces unavailable typing/
dataclasses; native setattr/_asdict features, original _fields metadata and mutation
guards preserve parameter integrity. Initial gates found defaultdict.items,
_asdict and _fields gaps; parameter mutation probe found an additional real
immutability gap. Fixed those boundaries, kept all algorithm/refusal tests.
Native source remains unchanged; freeze_manifest wrapper fixes stale frozen C
when QSTR/manifest changes caused duplicate enums. USB capture exits early only
on traceback plus observed REPL prompt; timeout still doesn't terminate a script.

Final DUT1 RAM image 89da26d1..., load 235301; gate 235538 passes all 45 published
SLIP39 vectors via actual combination and RecoveryState, share round trips,
original generic classifier/Slip39ShareDecoder, immutable record/set checks;
26 BIP39 fixtures in mnemonic/four-letter/numeric formats (all5wordcounts),
35 original-CPython CRC32C cases and Aezeed/BIP39 ambiguity. Entropy generation
and Aezeed scrypt/Blake2B remain explicit FeatureUnavailable, never substitutes.
Seed235350, memory/both-wordlists235356, PSBT235357, QR/scan235606 regressions pass;
52 host tests pass. Old QR test incorrectly expected missing dependency for three
actual BIP39 words; now tests original INVALID word-count result. Home235607,
preview stopped, readers finished. [mnemonic.md](../app/mnemonic.md) and phase-12-mnemonic receipt
record scope. No SD/CAD/REF-storage writes. Shared artifacts target DUT1; DUT0
still older Unicode image/qstr-heavy and needs a clean RAM reload before work.
Next: real View/Controller scan routing and displayed results, remaining compact/
encryption/UR dependencies, curves/entropy and SD app assets. Actual printed-code
optical scanning and full wallet workflows remain unqualified.

2026-11-15 UTC — Actual native curves required by original result Views
The original SeedFinalizeView computes a real fingerprint, so the Controller/View
work required its actual curve backend first. Added pinned libsecp256k1 v0.7.0
(a660a497...) portable ARM32 C, small upstream precomputation tables, preallocated
context (actual180 bytes), preserved MIT license/source snapshot. Native binding
validates buffers and uses portable X||Y/R||S tokens, not untrusted C struct blobs.
Full embit EC/BIP32-required ABI resolves real operations; no fake key/signature.
Custom callbacks/external contexts/unported APIs fail explicitly. Context randomize
accepts actual caller input; PUBLIC gate seed reset afterward. No entropy-source,
side-channel, full-erasure or wallet qualification claim. secrets still unavailable.

Final DUT1 image3e476dbe..., RAMload001212. Gate001235 passes all17BIP32paths,
16invalidkeys,19BIP340vectors,24originalSeedfingerprints/roots,12ECDSAcomparisons,
6ECDHpairs, recovery/lowS/keypair/in-place operations, malformed input recovery;
elapsed2740ms excludes upload/boot/UI. Smoke gate 000647 proved actual generator.
Initial C compile errors were binding formatting/helper-name issues; fixed with
warnings enabled. Console control-byte guard caught an escaped fixture-generation
bug before upload; corrected fixture without weakening transport guard.
Seed001240,PSBT001245,mnemonic001246,memory 001315,QR/scan001316 pass;54 hosttests pass.
Home001318, preview stopped, readers finished. [secp256k1.md](../app/secp256k1.md) and native-curves
receipt record provenance/scope. No SD/CAD/REF-storage writes. Shared artifacts
DUT1; DUT0 older Unicode/qstr-heavy needs clean RAM reload before work.
Next: original View/Controller/SeedStorage and real screen contracts. Fingerprints
are now genuine, so SeedFinalizeView can be ported without a placeholder. Full
optical QR, compact/encrypted/UR, entropy and SD app work remain unfinished.

2026-11-15 UTC / original app storage + native overlay checkpoint
Original SeedStorage/opaque EncryptedQRStorage/Singleton and button/constants/key
clear helpers now frozen with source/output receipts. Native gate 003457 uses real
BIP39 FP73c5da0a, pending conversion/dedup/wipe, SLIP39 share collection and actual
LVGL toast/screensaver timers/wake.20warm cycles stable 93430 nativebytes after
memory 003443 and QRfixture003444 regressions;57 hosttests pass. image6cb48f65...,
DUT1 RAMload003354. Earlier fixtures exposed actual native API differences:
time.sleep absent (adapter nowuses sleep_ms), display.buttons requires ui.init,
original incomplete mnemonic with None words raisesTypeError (not changed).
[app-core.md](../app/app-core.md) documents interfaces/scope. Original full Controller/View paths
not wired yet; next connect actual ScanView→SeedFinalizeView→SeedOptionsView→Home,
using canonical navigation and real native screen builders, no placeholder Views.
Keep printed optical QR unresolved; no camera re-aim requested while user absent.
No SD/CAD/REF writes, DUT0 untouched/needscleanreload, shared artifacts DUT1.
Home restored 003533; preview stopped and all USB readers finished.

2026-11-15 UTC / original foreground Controller and View integration
Final DUT1imageb103b390..., RAMload004823. OriginalController+14 core/18scan/91seed
Views frozen behind lazy actual imports; all source methods retained, no fake
optional providers. Sourcefstrings converted to format forMPcompiler, dataclass
Viewctors explicit. Realrenderer/status/finalize/options and sharedbuttonservices.
Full original flowgate004904: Home→Scan→Finalize(FP73c5da0a)→Options→Home via
nativeQRpixel fixture and realLVGLkeyevents, sourceStorage and actualhistory.
Error/idle004907: realSourceErrorView recovers; originalwipe clears stored/pending
publicseed aliases and stops actualSC3336 stream(True,1)→(False,0). Startup004910
originalsplash+developmentwarning pass. memory 004916,QR004918,core004919 pass;
61 hosttests pass. Native exception_location reads actualtracebackmetadata without
printing. sys.print_exception streamcapture is NOTsupported bythisbuild; do notuse.
OldQR fixture expectedController missing; nowtests realmissingURprovider pixels.
[views.md](../app/views.md) recordsentrycommand, boundaries, tests, pendingwork. Productionentry
fromREPL: from seedsigner_port.controller import Controller; Controller.get_instance().start()
NoautoappSDstartup inthisstage. Coreflowdoesnotprove printedopticalscan. Next focus
optical camera decode and remainingoriginalmenus/passphraseentry; thenfullSDapp.
NoCAD/SD/REFwrites; DUT0stillold/qstrheavy, don'tloadsharedDUT1imageonwiredDUT0.
Final review preserves startup unavailable-provider error routing; native test
passes. Home restored 004955; preview stopped, all USB readers finished.

2026-11-15 UTC / optical follow-up and snapshot transport
Printed DUT1QR stillfails12AE/4manualframes; wholecodevisible anddesktop reports
checksum errors.1036boundedstandard sampling/binarizer variants fail; no payload
printed/committed. KnownpublicQRonLCDalsofails20DUT0attempts; observerimage is
badlyoutoffocus. Do notclaimcameraopticalsuccess orchangeQRalgorithms without
supporting evidence. Images remainignoredlocal artifacts under optical-current.
Newcapture_luma.py task copiesoneownedluma image and exports80-row scripts with
sameSHA256; hostrejectsmixedcaptures/corrupt/missing/conflicting rows andchecks
fullimage beforePNGsave. BothDUTs pass,69 hosttests pass. [camera-snapshots.md](../hardware/camera-snapshots.md) and
phase-12-snapshot-integrity receipt record usage/proof. Ownedcopy is best-effort
wiped/released andcamera/settingsrestore verified; no whole-memory erase claim.
DUT0 NOW clean headless native-ui image77589e73..., RAMload005424; oldqstr-heavy
state gone. Camera stopped, AEtarget0/seed122 restored 010000. Do NOTloadapp-ui
onDUT0 becauseSPIloopback jumper remains. DUT1 stillrunningb103b390... app-ui,
Home005720; camera stopped afternewcaptures withsettingsrestored. Sharedartifacts
are rebuilt DUT1app-ui fdd3eaa7... andNOTloaded (no firmware codechanges thisstage).
REFuntouchedexceptauthorizedUARTreset/capturetool. NoCAD/SDwrites. Nextcontinue
remainingactualappmenus/passphraseentry whilephysicalopticalsetup isunattended;
return toopticalqualificationwhenbetterfocus/aim evidence isavailable.

2026-11-15 UTC / original passphrase screen/View integration
DUT1now3fdbd762... app-ui, RAMload010612. New actual native keyboard/review facades
andoriginal labels/defaults support SourceSeedAdd/Review/ExitDialog views without
rewrittenwalletlogic. Nativeconfirm2/Back6 events snapshot realtextarea withbyte
length, includingNULviaexistingnativehost helper; Backretainscurrententry. Current
255-byteeventbound rejects oversizeexplicitly. Renderernewframe/consume clears
texteventbuffer; nontexteventsreturnemptytext. SourcePassphrase normalization /
realRootFP remainactualpriorqualifiedbackend. Publick→52e15a41,kl→e6a78bb8,
empty→73c5da0a agreeindependentCPythonembit0.8.0. Realnativekeys qualifiedaccept,
edit,preserveappend,discardafterBack,emptyskip,finalize/options/Home; final 011105.
UTF8/NUL/spaceconfirmandBack exact, sideKEY1/KEY2 produceK6; bounds010837 pass.
Scanregression011113,memory 011115,72 hosttests pass. Publicreviewpixel011225
visuallychecked: shortk/fingerprints/actions readable. Home011250,previewstopped,
USBreadersfinished. DUT0untouched(freshheadless77589e73...),REFuntouched,noSD/CAD.
[passphrase-ui.md](../app/passphrase-ui.md) and phase-12-passphrase-ui receipt recordscope. Importantremaining
UIwork: fixedfont's nonASCIIglyphcoverage andlongpassphrase3linereview overflow.
Do NOTclaim fullUnicodevisualreview orwholewalletqualification frombyteexacttests.
Nextimprovevisiblepassphrasereview, thenremainingactualmenus/seedentry/fullSDapp;
physicalprintedQRopticalqualificationstillopenwhileuseraway.

2026-11-15 UTC / paged character review + unresolved reset
DUT1image575dc79e... app-ui. Newreview_text.py puredisplay encoding and actual
SeedReviewPassphraseScreen facade pages values that don'tfit reliable shortASCII.
Legend+numberedranges+24col/4data lines; hidden/nonASCII usesexactUnicodeidentifiers,
backslashdoubled. No model/normalization/actionindex changes. SourceNFCdisplayvalue
positions, OriginalNFKDrootderivation; finaloriginalscreen showscount+realFP/actions.
Backrevisitslastpage, outoflegendreturnsoriginalBack. Service/idlewipe remainsreal.
Hostindependentescape decoder checksALLrenderedtext/ranges;1,112,064scalaridentities
roundtrip;80 hosttests pass. Native180ASCII,mixedUnicode/NUL/backslash/LF,63 emoji,
revisit,Backexit,wipe routespass. Pixel012512: fullASCII andUnicodeIDrowsreadable.
IMPORTANT: expandedrepeat012910 disconnected/resettomaskrom101 beforestressloop,
noUSBfaultmessage. CauseUNKNOWN, NOTresolvedbylaterpasses. RAMreloadedSAMEimage
013153; fresh013325/hot013430/after-regression013643 eachpass20stableheapcycles
andallpagedflows. Shortentry013633,memory 013641 pass. Capturefailedrunandpassing
receipts inphase-12-review-pages.json. [review-pages.md](../app/review-pages.md) recordsusage/limits.
NextPRIORITY addpersistent/USB-accessiblefault/resetcause diagnostics, investigate
accumulatedruntime BEFOREclaimingstability. Don'tsuppress/resetawaythisincident.
DUT0untouchedheadless77589e73...,SPIloopbackstillinstalled. REFuntouched,noSD/CAD.
SharedbuildDUT1app-ui575dc79e...,sameaslive; noinputuserphysicalactionneeded.
Home restored 013951; camera off, readers finished.

### 2026-11-15 UTC — Retained warm-reset diagnostics

- Added a versioned/checksummed 64-byte record at noncacheable DDR60MiB+64KiB,
  outside USB DMA. First marked cause per boot wins, with optional app marker and
  ARM fault registers; commit magic is written last. MicroPython exposes read,
  clear and marker APIs. Panic records evidence but keeps its existing halt policy.
- DUT1 controlled USB reset, guarded data abort, actual C++ abort and interpreter
  fatal callback retained the expected causes through matching RAM reloads.
  Corrupt records reject; saved probe ELF resolves the guarded instruction.
  Deliberate probes require an explicit build feature, disabled in the normal app.
- Normal image5f442574... loaded015513; disabled-probe check015552 passes.
  Instrumented review 015553 and 015903 pass with no recorded reset during either
  run. Original passphrase 015855 and memory 015917 regressions pass; Home020051.
  Four Rust record-format tests and80Python tests pass. Evidence receipt and
  [reset-diagnostics.md](../hardware/reset-diagnostics.md) document exact scope, API and retained-record limitations.
- Earlier unexplained reset 012910 remains OPEN. Controlled fault tests do not
  explain it; unmarked resets or cold loss can leave stale/no DDR evidence. No
  new optical/entropy/wallet qualification. DUT1 RAM only, no SD/CAD/REF/DUT0 writes.

### 2026-11-15 UTC — Original manual BIP39 word entry

- Reviewed SeedMnemonicEntryScreen arguments/text results now reach the actual
  pinned native keyboard. Original menu, word-entry, checksum-error, finalization
  and storage decisions remain generated upstream source. Default fields and
  provenance regenerated; host differential/result checks total 81 pass.
- DUT1 image8d72625d..., RAMload020307. Final native gate 020714 proves fresh
  12/15/18/21/24-word entry using real native keys and independent CPython embit
  public zero-entropy fingerprints. Candidate scroll/accept, hidden single-prefix
  rejection, saved-word reopening, DEL correction, invalid checksum discard/edit
  and Back #2→#1→cancel pass. Public seeds discarded; reset recordNone per flow.
- Test initially used unsupported starred tuple syntax, then tried a15-word menu
  item hidden by defaults. Both fixture issues corrected; timeout explicitly
  interrupted without reset, inspection020531 responsive/recordNone. Final gate
  enables lengths in RAM and restores defaults in finally; no production setting
  change. [mnemonic-entry.md](../app/mnemonic-entry.md) and evidence receipt retain scope and failed attempts.
- Actual framebuffer020638 visually checked: word number, prefix and highlighted
  candidate readable.20entry/Home rebuild cycles return native heap to133702 bytes.
  Original passphrase 020758 and paged review 020806 regressions pass; no recorded
  reset. Final state020827 confirms defaults12/24, empty storage, camera off;
  Home020828. No SD/CAD/REF/DUT0 writes, no push. Earlier reset remains unknown;
  optical QR, entropy, other app screens/signing and full SD startup remain open.

### 2026-11-15 UTC — Original seed-word backup review and quiz

- Added reviewed word-page and backup-prompt adapters using actual pinned native
  widgets and original Views. Prompt retains its original post-init text/Back
  policy. Fixed original SeedWordsView floor-page-count bug in guarded generation:
 15/18/21-word phrases now show trailing partial pages, with explicit4-word
  numbering offsets. Pinned source unchanged; reviewed changes in provenance.
- Seed Views bind their non-secret random import to quiz_random: actual pinned
  MicroPython Yasmarang plus rejection-sampled Fisher-Yates. Clock-seeded and
  predictable, NOT wallet entropy or CPython MT equivalence. No secrets/entropy
  health qualification. Native-only standard module is explicitly compiled/frozen.
- DUT1 final image dbbc054b..., RAMload021448. Native021558 passes all5BIP39
  lengths, every exact word slice/page/offset, Back/review, wrong-answer retry and
  all 12 quiz answers for stored/pending seeds. Original pending sentinel reaches
  finalization and storage; success clears stored-seed history. Forced inactivity
  during visible words clears stored/pending seeds and zeroes checked64-byte
  aliases before Home. Public generated phrases only, discarded after testing.
- Integration attempts exposed explicit module/source/feature flags and missing
  ticks_us (use actual ticks_ms). Pending fixture also needed the starting View's
  history entry before its skip-current transition. Failed logs retained in the
  receipt; no reset was used to conceal a running test or unknown failure.
- Actual partial-page pixels 021646 show13absurd/14math/15exhibit on4/4, all readable
  with Done/border.20word-page/Home rebuilds stabilize at155986 native heap bytes.
 81 host tests pass. Manual entry 021652, passphrase 021736 and paged review 021745
  regressions pass without recorded reset. Final021810 confirms restored default
  settings, empty storage, camera off, normal probes disabled; Home restored.
- [backup-words.md](../app/backup-words.md) and phase-12-backup-words receipt capture scope and matching ELF
  checkpoint 021747. No SD/CAD/REF/DUT0 writes or push. Earlier unexplained reset,
  optical QR, qualified entropy, remaining app/signing and SD startup remain open.

### 2026-11-15 UTC — Original standard/compact SeedQR export

- Generated all15original encoder classes with lazy providers/explicit dataclass
  constructors; qualified standard/compact BIP39 encoders. Pinned original
  python-qrcode7.3.1 matrix algorithms and full upstream license retained. Native
  PCRE2 regex/bisect/zfill/bytes.find boundaries preserve needed CPython behavior;
  standard math, class arithmetic and two-argument next enabled for native builds.
  No PIL/image stubs; unsupported image/terminal providers fail explicitly.
- Original format/warning/whole/zoom/confirmation-prompt Views now use actual
  native transcription widgets with the same original matrix in both QR views.
 25 independent CPython payload/matrix cases022814 pass
  all5BIP39 lengths and binary/segmentation edge cases; native ZXing recovers each
  symbol and original SeedQrDecoder returns expected words. Core workload5530ms,
  NOT boot timing. Final successful core log 022814, image 41abc7a732b8..., RAMload022750.
- Earlier core attempts exposed disabled Polynomial operators, next(iterator,None),
  then an overly broad bytes.find conversion for odd alphanumeric segments. Fixed
  boundary/feature support; failed evidence retained. Final source/image hashes
  checked.83host tests pass, including original class/hash and adapter differentials.
- Native export022821 and final 022927 pass 12/24standard+compact, overview pixel
  decoding, Back→format, zoom pan/exit and Done→options→Home with original history.
  Forced inactivity while private QR displayed wipes checked seed-byte alias and
  storage; Home pixels decode no QR. No whole-memory erasure claim.
- Actual overview pixels 023007 visually checked (title, QR, Begin25x25 fit 240 px).
 20 overview/Home rebuilds return native heap to152033 bytes. Backup023015,
  passphrase 023041 and paged review 023050 regressions pass. Final023142 confirms
  empty storage, camera off, restored settings, no reset record; Home restored.
- [qr-export.md](../app/qr-export.md) and phase-12-seedqr-export receipt include matching ELF checkpoint
 023125. No SD/CAD/REF/DUT0 writes or push. Optical camera/handwritten confirmation,
  entropy, encrypted/UR/xpub/PSBT export/signing and full SD app startup remain open.
  Earlier unexplained reset remains OPEN despite successful marked runs.

### 2026-11-15 UTC — Original SeedQR confirmation and format probes

- HardwareButtons.check_for_low now records activity for accepted debounced,
  unblocked lows, matching poll. Initially held keys stay blocked; a held stable
  level counts until release stabilizes. Host test exercises real debounce and
  timestamp behavior; native left/right cancellation verifies accepted activity.
- Original compact detection probes BIP38/KEF before choosing candidates. Ported
  original BIP38/WIF/encryption/KEF/Base43 bodies with lazy dependencies and exact
  source/output hashes. Real public AES mode IDs extracted at generation only;
  no native AES module supplied. Crypto methods preflight actual AES/scrypt and
  fail explicitly when absent. Preserved Krux MIT notice. Base43 local prepend
  buffer uses a list; UnicodeDecodeError maps to native UnicodeError as needed.
- Independent unmodified CPython format oracle and native 024137 pass118raw/Base43
  metadata probes, invalid UTF8 IDs, malformed envelopes and compact/encrypted
  candidate overlap. BIP38 fields/leading zeros and unavailable crypto verified.
  No encryption/decryption, key-generation or wallet qualification follows.
- Initial confirmation 023542/023620 reached standard match then missing BIP38;
  provider load 023847 exposed helpers-import-kef alias routing. Fixed actual
  dependencies, retained failures. First10flows024139 pass; final11flows024343
  add recognized complete Bitcoin-address rejection and decoder-state assertions.
  Native ZXing/original Views compare matching12/24standard/compact, wrong seeds,
  bad checksum/text, and cancel left/right. Error routes revisit zoom then Done;
  source seed stays unchanged, no pending seed substituted. Public pixel fixtures
  and timed logical masks only; physical optical/debounce wiring not requalified.
- Final image6564273b2b57..., RAMload024112.86host tests pass. Actual SC3336
  regression 024501 captures1preview frame then stops to(False,0) via idle cleanup;
  QR core024504 and paged review 024511 pass without recorded reset. Final024636
  confirms empty storage/default settings, sensor off and probes disabled, replaces
  test Controller/camera/buttons with normal adapters, restores Home. Matching ELF
  checkpoint 024732 and phase-12-seedqr-confirmation receipt saved.
- [qr-confirmation.md](../app/qr-confirmation.md) records scope. No SD/CAD/REF/DUT0 writes or push. Optical focus,
  hand-transcribed confirmation, qualified entropy/crypto/signing and full SD app
  startup remain open; earlier unexplained reset remains OPEN.

### 2026-11-15 UTC — Composited native scanner and PSBT retrieval

- Native LVGL scanner now uses the original camera instruction/progress/status
  widgets over an owned115200-byte RGB565 preview. Existing center crop/BT.601
  conversion retained, explicit little-endian image storage; no borrowed camera
  pointers retained. Image cache/widget/animation cleanup precedes buffer wipe/free.
  Generic screen replacement and ui.blank release the surface; Python renderer
  blanks the actual LVGL root/shadow. Camera stop failure keeps ownership for retry.
- Original scan runtime begins/ends the preview through completion, source errors
  and interrupts. Source decoder fixes preserve function-local import shadowing,
  adapt ASCII Base64 to native binascii buffers and original Base43 reverse byte
  traversal/assembly to MicroPython APIs. Original CPython differentials pass.
- New image b35f2a99be50..., DUT1 RAMload031420. Native031623 passes color vectors,
  source mutation isolation, progress/status changes, screen replacement, blank
  and20warmcycles with stable158191-byte native baseline. Earlier fresh-session
 20 cycles stable 56571 bytes; cache state differs across sessions. Public pixel
  flow 031635 passes repeat/miss/out-of-order fragment progress and complete PSBT
  serialization, standalone Base64/Base43 retrieval and error/interrupt cleanup.
- Retained failed attempts: native binascii string030127, local-base64 binding
 030405, Base43 stepped-slice031127. First confirmation 031511 failed allocation
  on case10 because prior gate retained multi-megabyte public frames in REPL;
  gates now explicitly release them. Cleanup031603 echoed public pop results and
  timed out; interrupted that cleanup and suppressed expression echo. Corrected
  full sequence passes:11confirmation031640, real sensor idle031711,25QRcore031714.
- Public native instruction/progress framebuffer images visually checked. Actual
  sensor+LCD scan 031729 runs 17 frames in10 seconds then deliberate USB Ctrl-C stops
  sensor to(False,0) and returns native heap to baseline. This is an app preview
  check, not a capture FPS measurement or optical QR qualification. No real scene
  pixels exported. Final031740 verifies empty storage/default settings, sensor off,
  probes disabled/no recorded reset; actual camera/buttons restored and Home drawn.
- 93 host tests pass. [scan-overlay.md](../app/scan-overlay.md), mise prepare/gates, matching ELF/image
  checkpoint 031526 and phase-12-scan-overlay receipt retained. Host-injected gate
  cleanup changed after image build; executed copies/hashes recorded separately.
  No SD/CAD/REF/DUT0 writes or push. Optical focus/reliability, qualified entropy,
  signing and full SD app startup remain open; earlier unexplained reset OPEN.

### 2026-11-15 UTC — Frozen foreground app startup and USB recovery

- User reported host power loss; both RV1103 targets observed in maskrom 101/201,
  no CDC ports or REF ADB. RAM firmware was lost as expected. Reloaded only DUT1;
  DUT0 remains in maskrom, no REF/SD/storage/CAD changes.
- New optional app-autostart inherits full DUT1 app-ui. After mp_init, runtime
  executes frozen seedsigner_boot.py and the reviewed boot.run wrapper, entering
  original splash/development warning/Home without a host Python start command.
  Normal app-ui keeps REPL startup. Generic DUT0 harness rejects new LCD profile.
- Wrapper releases camera and blanks actual LVGL screen on all exits, retains only
  entry/running/type/builder metadata, rejects reentry; cleanup errors recorded by
  type too.97host tests pass, including return/interrupt/stop-error/nested entry.
  @@REPL_READY now follows app exit in this optional profile; interpreter timing
  hook remains after mp_init and does not measure cold/app readiness.
- Initial load 042339 autoentry/recovery passed, but old console gate incorrectly
  expected no GPIO outputs after LCD init. Actual UART mux/IER/IRQ0; DDR0x800 is
  documented GPIO43 LCD backlight, not UART output. Corrected optional-profile gate.
 042447 gate rejected retained reason2 from intentional preceding USB reset;
  now prints and validates only None/reason2 before clearing. Other reasons fail.
- Final image18e5b71db142..., RAMload042717 passes actual frozen startup to native
  status screen then USB Ctrl-C recovery/blank/stopped camera/empty storage/probes
  off. Entry-flow042747 passes original splash, exact development warning, native
  key acknowledgment and Home; returns cleanly through wrapper. This qualifies
  injected native key events, not a newly observed physical button press.
- First live scan 042630 stopped after 18 frames but cold instruction font cache
  added6171 native bytes. Camera/LCD interrupt gate now warms identical original
  instruction widgets before native heap baseline. Final042754 runs 18 frames in
 10 seconds, intentional Ctrl-C returns sensor(False,0) and heap to warm baseline.
  No camera pixels exported, no sensor FPS/optical QR claim. Final042805 confirms
  empty/defaults/camera off/probes disabled/no new reset, restores normal adapters.
- Matching ELF/image/runtime hashes and scripts saved in checkpoint 042811.
  [app-boot.md](../bringup/app-boot.md), mise build/gates/handoff tasks and phase-12-app-autostart receipt
  record exact scope. Final042821 RAM download leaves same image un-interrupted
  for user: this final handoff checks download/USB enumeration only; automatic
  entry/recovery already tested on exact image. App awaits warning acknowledgment.
  SD app image/persistence, physical/optical qualification, signing/entropy and
  cold-power timing remain open; earlier unexplained reset remains OPEN. No push.

### 2026-11-15 UTC — Original xpub derivation and static native export

- Froze original embit helper function bodies with pinned source/hash guards and
  lazy real dependencies; mapped direct/from-helpers aliases. Function presence
  is not descriptor/message-signing qualification. Source generators/defaults
  and attribution retained, no native C++ screen-library changes.
- First core043303 exposed MicroPython's depth-first diamond inheritance: static
  xpub cur_part reached BaseQr abstract instead of BaseStatic. Materialized exact
  original BaseStatic cur_part/seq_len/is_complete on StaticXpub, retaining CPython
  C3 behavior without changing encoder algorithms. Host body/provenance checks
  account for the shared annotation removal. Updated host contract oracle with
  actual original xpub details class/valid fields;101 host tests pass.
- Native core043738 on final e3fa1be12669... app-autostart image/RAMload043708 passes
 42 public cases:3 networks, account0/7,7 script/signature combinations, exact versions,
  xpub payloads and48receive/change addresses including Taproot.126Specter density
  cases verify fragments, rollover and restart. Public mnemonic/PUBLIC passphrase
  only,5584ms overall workload; no signing/security or sensor performance claim.
- Reviewed native xpub details facade preserves source fingerprint/path/prefix,
  labels and Export button. Static QR facade sends original payload as hex to
  actual native QR display, two-module quiet zone,512-byte reviewed bound; source
  brightness events/settings and any-non-brightness-key exit retained. Animated
  frame transport and cancel_on_back key identity fail explicitly until ported.
  LoadingScreenThread call boundary draws native cooperative spinner; no OS or
  background animation while crypto blocks. Root replacement releases native timer.
- Flow043745 passes original SeedOptions→export/privacy→details→QR routes on main/
  test singlesig/multisig. Actual framebuffer QR decodes exact original payload;
  native Down changes255→224 and persists at exit. Singlesig reaches original
  address-verification prompt; multisig reaches Home. Details Back returns via
  original history to options/Home. No selected results injected.20loading/details/
  QR/Home cycles return to stable 152963 native bytes. Source address scan/search
  is unfinished; native format menus remain original and unported formats error.
- Public actual QR and details043817 images visually checked: full fingerprint/
  path, source-abbreviated xpub prefix and Export fit 240 px. Original11confirmation
  regression 043818 and real SC3336/LCD/ZXing interruption043851 pass 18 frames/10s,
  stopped sensor and warm native heap baseline. No real camera pixels exported.
  Final043902 verifies empty/defaults/camera off/probes off/no new reset and restores
  actual adapters/Home. Matching ELF/image/runtime hashes in checkpoint 043839;
  [xpub-export.md](../app/xpub-export.md) and phase-12-xpub-export receipt record scope and failed attempts.
- Final same-image RAM handoff is recorded in receipt separately, without an
  interrupting console gate. No SD/CAD/REF/DUT0 writes or push. Physical/optical
  qualification, address scan/search, animated/UR export, full signing, qualified
  entropy and SD app startup remain open. Earlier unexplained reset stays OPEN.

### 2026-11-15 UTC — Address verification prototype and manual UI handoff

- In-progress/uncommitted address-search stage: source workers are foreground
  generators with yields after original pairs/precomputed expanded paths; scoped
  Counter/Worker bindings only, no global fake BaseThread. Native progress push
  uses original library API.105host tests and11 native export→scan→search flows
  pass (usb044739): receive/change/Taproot/legacy, Skip10, cancel, wrong script,
  other account, last 999 vs bound1000, source idle wipe/worker release.
- First flow 044707 lacked UI init before HardwareButtons and failed GPIO read;
  gate setup corrected. Source constructor order in actual Renderer was unchanged.
  Additional direct-search045122 passed simple0/native success pixels, then failed
  its next 100 case assertion at line71. No expanded/continuation qualification yet;
  add diagnostics and investigate after manual handoff. Failed script already
  terminal before attempted host SIGINT (PID no longer existed); no worker/reader
  was stopped by that attempted host signal.
- User explicitly requested testing a QR and using the UI. Suspended further
  hardware tests, built current optional app-autostart prototype, RAM downloaded
  DUT1 only 045300 with no console interrupt. Public test QR generated under
  logs/phase-12/manual-ui-demo-20261115T045341Z: standard48numeric digits encoding
  abandon×11/about, expected fingerprint73c5da0a. No real seed/scene image used.
- MANUAL UI HANDOFF PENDING: user is operating DUT1 buttons/camera. Do not send
  USB Ctrl-C/reset, overwrite RAM or run device gates while this handoff is active.
  Wait for user's result/done instruction before reclaiming DUT1. Independent
  host/source investigation may continue. This is not a request to pause the goal.
  Optical decoding/physical button success is not yet observed. No SD/CAD/REF/
  DUT0 writes or push. Earlier unexplained reset remains open.

### 2026-11-15 UTC — User-requested app microSD quick test, preparing card

- User approved UI demo as good and requested a microSD quick test, then inserted
  spare4GB into Mac. External physical disk 7/Generic STORAGE DEVICE/4025483264
  bytes identified; metadata snapshot retained. No REF/DUT0 storage targeted.
- Extended existing file-only packager with explicit runtime/app profile guards,
  DUT1 identity validation and dynamic whole-MiB image reservation. Current frozen
  app2917320 bytes cannot fit old2MiB image; new app-sd is3145728 bytes. Unchanged
  DDR22148 bytes and both padded stages/header SHA256 validated. Added profile/
  corruption/large-image tests;107 host checks pass. Concrete candidate/ELF/manifest
  saved in app-sd045650 checkpoint, imageSHA19a7fc3acbd7... .
- Etcher initially needed native-coordinate file-picker click; stale prior image
  canceled and app restarted before selecting immutable new app image. Expected
  missing-partition-table notice acknowledged; only external4.03GB disk 7 selected.
  Flash started; actual sudo askpass process observed waiting for Mac auth. Asked
  user to enter password only in system prompt. Write/verification/boot not yet
  proven. Do not interpret GUI Starting as completed flash.

### 2026-11-15 UTC — User confirms native app microSD boot

- Etcher helper failed; no completed Etcher write claimed. CUA safety controls
  rejected access to UserNotificationCenter/auth dialog, user handled old request.
  Both pending sudo/osascript processes were absent before alternate write.
- Raspberry Pi Imager selected immutable3MiB app image and only 4GB external card,
  declined OS customization, started write. Later storage cleared/card disappeared;
  writer verification-success dialog was not observed. No raw-byte readback claim.
- User then reported: "pluged in it. it works! boot up and start is FAST!"
  This confirms the standalone app SD quick test on DUT1 at current native 2.9MB
  payload size, without another RAM download. FAST is user-reported, not a measured
  power-to-UI/REPL/frame time. phase-12-app-sd-quick-test receipt preserves exact
  hashes, write observations, scope and gaps. DUT1 now has SD installed: USB reset
  boots card, not maskrom. Do not reset/interrupt while user operates UI.
