# Bring-up history

## 2026-11-13 — Phase 0: establish a safe two-board test setup

1. Read the user plan in `PLAN.txt`. Defaulted to plain `no_std` Rust; retained all hardware gates and RAM-only restrictions. No bare-metal source or payload existed at the start.
2. Identified macOS 26.5.1 / arm64. Found two ADB boards, not an initial maskrom target. Explicit per-device shell reads identified the newer `seedsigner-os` image as REF and the older `seedsigner` image as DUT. REF detected SC3336 ID `0xcc41`; DUT's Linux image logged sensor-ID failure. Both had 4 GB microSD media. Evidence: `logs/phase-0/adb-devices-initial.txt`, `usb-initial.txt`, `ref-uart-inventory.txt`.
3. User unplugged DUT, removed its microSD and reconnected it. REF remained accessible. Host USB changed from two `2207:0019` Linux gadgets to one Linux gadget and one `2207:110c` maskrom device. Built official Rockchip rkdeveloptool commit `304f073752fd25c854e1bcf05d8e7f925b1f4e14`; `ld` confirmed `Maskrom`, USB location `201`. Evidence: `maskrom-detection.txt`, `rkdeveloptool-build.txt`. No `db`, storage write, erase or reset command was issued.
4. Installed `arm-none-eabi-gcc` 16.2.0 through Homebrew and `armv7a-none-eabi` for Rust 1.93.1 through rustup under mise. Evidence: `arm-toolchain-setup.txt`, `rust-target-setup.txt`.
5. Read live REF serial DT nodes and vendor configuration behavior. All six UART nodes were disabled. UART3 exists at `0xff4d0000`, pinctrl group GPIO1_D0/D1, while UART4 at `0xff4e0000` was represented by a disabled vendor overlay. Debugfs showed GPIO1_D0/D1 were owned as output GPIOs by the display frontend, so they could not simply be wired to DUT TX.
6. Stopped only the display supervisor/frontend at runtime using SIGTERM. The supervisor exited first; the Python frontend completed shutdown shortly afterward. Applied a fresh status-only UART3 runtime overlay, without calling the vendor's persistent FDT save path. `/dev/ttyS3` appeared with IRQ 60 and base baud 1,500,000. Verified frontend exit, GPIO release and UART3 pin ownership before requesting wiring. Evidence: `ref-after-ui-stop.txt`, `ref-uart-enable.txt`, `ref-uart-pin-owners.txt`.
7. Opened `/dev/ttyS3` from Python with raw 8N1, `CLOCAL|CREAD`, both termios speeds set to `B1500000`; closed it successfully. Evidence: `ref-uart-open.txt`. This proves the Linux port opens, not that the inter-board wire path or baud has been validated.
8. Requested the three-wire, 3.3 V bridge with both boards unpowered: REF pin 12/TX → DUT pin 5/RX; REF pin 13/RX ← DUT pin 4/TX; GND pin 2 ↔ pin 2. Requested reconnect with DUT microSD still absent. Awaiting physical confirmation. A REF reboot will require reapplying the runtime UART setup.
9. User requested all work and its history in a new folder. Created top-level `baremetal/`; moved this effort's tool checkout and Phase 0 logs inside it. Original Linux firmware and PCB sources were left unchanged.

### Sources consulted

- [Official Rockchip rkdeveloptool](https://github.com/rockchip-linux/rkdeveloptool): host build, device listing and RAM loader command semantics.
- [Official Luckfox UART guide](https://wiki.luckfox.com/Luckfox-Pico-Plus-Mini/UART/): Mini UART availability and Linux serial naming.
- Retained official Mini pinout at `../docs/luckfox-mini-pinout.json` and SDK pinctrl snapshot at `../reference/pinouts/rv1106-pinctrl-824b817.dtsi`, cross-checked against REF's live device tree and pinmux.

### Gate status

Host tools, REF shell, DUT maskrom detection and REF UART open have hardware evidence. Phase 0 remains open until bridge wiring is confirmed. No DDR-loader banner, own-code hello, GPIO/I2C/SPI test, bare-metal frame or MicroPython boot has passed yet.

10. User said both boards will be powered off before wiring. Continued host-only documentation/tool setup during that physical action. Added `devices.json` with explicit roles and wiring still unconfirmed, plus a read-only `baremetal:doctor` task. No harness image download or next-phase execution was started while Phase 0 wiring is pending.
11. Checked the doctor's command-line help and ran `mise run tasks:check`: all 286 task definitions passed structural checks. Set subprocess working directories to `baremetal/` so rkdeveloptool's automatic `log/` directory remains inside this effort's folder. These are host checks only; no board commands were run during the power-off/wiring interval.
12. User confirmed the boards are connected. Rediscovered REF via its explicit ADB serial and DUT as the single `2207:110c Maskrom` target. Paused the rebooted REF frontend supervisor (PID 993, checked command line before SIGTERM), verified GPIO release, reapplied the UART3 runtime overlay and set raw 8N1 at 1,500,000 baud. Pinmux confirmed pins 56/57 serial-owned with GPIO unclaimed. Updated the physical wiring confirmation and ran `mise run baremetal:doctor`: all four Phase 0 checks passed. Evidence: `logs/phase-0/doctor-20261114T053121Z.json`. The wire path and actual loader baud remain to be validated by Phase 1 output; no payload has been loaded yet.

13. Started Phase 1 after the Phase 0 gate. Downloaded official rkbin commit `3e288fe814e059dd06833495f845cab04ac20a5c`, retained its license, and packed RV1106MINIALL.ini using the supplied Linux x86-64 boot_merger in Alpine Docker on macOS. The official Luckfox Mini A SDK config selects the RV1106 software family; RV1103B blobs were not selected. Provenance/hashes: `stock-loader.json`. Added a bounded REF capture helper and RAM-only `harness.py`. REF ADB rejected exec-out and non-PTY shell; first attempt aborted without download. Implemented base64 framing over supported PTY shell.
14. Ran the stock-loader capture: `rkdeveloptool db` returned success; no storage-write commands were used. Captured 2,437 bytes, all zero. REF driver reported 2,424 breaks and 13 framing errors; no readable DDR banner, so Phase 1 FAILED and Phase 2 was not started. DUT still enumerates Maskrom. Saved raw bytes, transport stderr, download result and REF UART/pinmux state under `logs/phase-1/20261114T053328Z/`. Next action is physical wire/ground verification while powered off.
15. While awaiting the physical wiring recheck, improved only host tools: capture now verifies baud readback; harness records download/capture exceptions and refuses success on malformed base64 transport. Added a real host pseudo-terminal test using the capture helper: all 256 byte values repeated four times survived its framed transport exactly (1,024 bytes). `mise run baremetal:check` runs this without accessing boards. This validates transport handling only and does not validate the physical UART link or close Phase 1.

16. User explicitly confirmed both boards are RV1103. Recorded the silicon identity for both roles in `devices.json`, NOTES and loader provenance. Rechecked the local official Mini A SDK config: its filename and `RK_APP_TYPE=RKIPC_RV1103` identify the board while `RK_CHIP=rv1106` selects shared software support. No hardware command or new download was issued. Phase 1 serial output remains unverified; the RV1106 loader filename is not evidence that the boards contain RV1106 silicon.

17. User stated the UART wiring is probably correct. Rechecked REF and DUT access: UART3 overlay remained active and DUT still listed Maskrom. A passive one-second 1,500,000-baud capture produced no bytes and the previous break/framing counts did not increase. Corrected the earlier inference: the errors may be confined to loader transmission at a mismatched baud; they do not prove a persistent low input or incorrect wiring. Local official SDK rkbin has explicitly named 1,500,000-baud DDR variants. Added `--baud` to the harness and attempted the existing stock loader at 115,200. The second `db` timed out (30 s), with no serial bytes, despite the device still listing Maskrom before the command. Saved failure JSON in `logs/phase-1/20261114T053856Z/`. Need a DUT-only replug before a fresh trial; no rewiring requested and no storage commands used.

18. User replugged DUT. Repeated the stock loader with capture at 115,200 baud: `db` succeeded and an 803-byte readable DDR/USB loader banner was captured. Banner reports DDR v1.16, DDR2 64MB, 528MHz and `chip_id:5256110300,0`; hardware is RV1103. Phase 1 PASSED: `logs/phase-1/20261114T054010Z/result.json` and `serial.txt`. The physical wiring was correct; the earlier zero/break stream was a baud mismatch. Updated configured capture baud to verified 115,200. No persistent writes occurred. Phase 2 now begins; ten own-code hello runs are still required.
19. User asked for actual USB power cycling to avoid manual attendance. Inspected macOS IOUSB topology: both boards appear directly below Apple USB host controllers, with no external USB hub exposed. No per-port power controller is currently available through the inspected tools. uhubctl requires a hub exposing power switching; macOS 26 additionally needs libusb >=1.0.30 per upstream documentation. No port power command or reset was issued. Software reset via the stock Rockchip USB loader remains a separate possibility, not a substitute for removing power from a hung payload.
20. Verified remote recovery from stock usbplug: `rkdeveloptool rd 3` reported success, and a fresh stock DDR-loader capture passed without a replug (`logs/phase-1/20261114T054225Z/`). Created original MIT Rust no_std stage-2 code at address 0 with stack top 0x00400000, using UART2 inherited from unchanged DDR initialization. Register facts studied in open SDK sources: UART2 base ff4c0000, 32-bit registers at four-byte spacing; CRU base ff3a0000 + TOPCRU 10000 + global reset c08, reset key fdb9. No GPL implementation or closed blob code was copied/disassembled.
21. Built the hello payload using Rust 1.93.1 and packed it with the unchanged DDR blob, replacing only CODE472. First DUT run printed `@@PASS hello` after the DDR banner: `logs/phase-2/20261114T054351Z/`. Sent R from REF UART; DUT disappeared then re-enumerated in Maskrom, confirming our payload's UART-triggered warm reset works without physical power cycling. Started the ten-consecutive-run hardware gate with saved per-run logs and reset checks.

22. Phase 2 PASSED: ten consecutive own-code hello runs, each followed by UART R reset and maskrom re-enumeration, without physical replug. Gate evidence: `logs/phase-2/hello-gate-20261114T054519Z.json`; independently audited all ten referenced raw captures and per-run results for DDR completion plus exact `@@PASS hello` output. Phase 3 CPU base is next; no cache/timer/IRQ qualification is claimed.

23. Implemented Phase 3 CPU diagnostics, original short-descriptor identity MMU mapping and cache maintenance. Counter works at 24 MHz; loader SCTLR has M/C/I off and ACTLR has SMP clear. First memory benchmark failed the requested threshold (~2.1x). Arm Cortex-A7 TRM explains SMP must be set before cache/MMU maintenance; after setting it, the unchanged workload improved ~93–96x with equal checksums. This was a cache-control issue, not a clock-rate adjustment.
24. Added banked IRQ stack and exception vectors, GICv2 physical timer interrupts and UART2 RX interrupt echo, plus a monotonic DDR heap (alignment, nonoverlap, write/read patterns and OOM rejection verified). Final combined Phase 3 build hardware gate PASSED: `logs/phase-3/phase-3-gate.json`, raw capture `20261114T055317Z/`, echo `echo-20261114T055341Z.json`. Measured cache speedup 96.4486x; timer 1,000 IRQs in 24,000,004 counter ticks at 24 MHz (~999.9998 Hz); all 47 echo bytes matched. Heap passed. No GPIO/I2C/SPI/camera qualification is inferred. Phase 4 GPIO pinmux and inter-board patterns are next.

25. User corrected board identities: REF is a standard Luckfox Pico, not a Mini; DUT remains Pico Mini. Both are RV1103 per user confirmation. Earlier header-number instructions assumed Mini on both boards; withdrew the pending GPIO 10-to-10 / 11-to-11 instruction until standard Pico physical numbering is checked. The UART3-to-UART2 signal path remains hardware-proven, but REF physical header numbers in config were assumptions and are now explicitly marked unverified. No new GPIO output or wiring test was started.

26. User identified existing REF wires: red TX, white RX, brown GND; available new wires blue/orange. Visually checked standard Pico official schematic pinout. Standard Pico GPIO1_C4 is GP5/header7; GPIO1_C5 is GP4/header6. Planned blue REF7/C4 → DUT10/C4 (DUT output to REF input), orange REF6/C5 → DUT11/C5 (REF output to DUT input). Corrected the Mini-to-Mini numbering assumption. Existing UART3 signals correspond to standard Pico header19/D0 TX and header20/D1 RX; actual ground pad unspecified. New GPIO wiring remains unconfirmed.
27. Prepared original gpio-test driver for GPIO1_C4/C5 using 16-bit write masks, GPIO-v2 split registers, pinmux/pull fields and GPIO1 PCLK gate. Both pins start as input; only UART0/1 command enables C4 output; Z releases both. Preserved Phase3 baseline artifacts and built gpio-test host-side while user wired. User confirmed GPIOs in place. REF did not reboot; UART bridge remained active. Exported REF GPIO52/53 as inputs and checked ownership before download. Initial db timed out because old CPU payload still ran despite USB Maskrom listing; UART R reset recovered it without user replug.
28. Phase4 PASSED: successful gpio-test boot `logs/phase-4/20261114T060058Z/`, then sixteen opposite-level transitions on blue/orange matched REF GPIO reads and DUT UART-reported reads. Evidence `logs/phase-4/gpio-gate-20261114T060114Z.json`; final Z acknowledged and both REF pins returned to input. No Phase5 sensor test inferred.
29. User will attach a separate camera to DUT, not move REF's camera. Requested DUT power-off before ribbon attachment and reconnect without microSD. REF's SC3336 remains available. Read-only REF/source inspection confirms camera address0x30 on I²C4, expected chip ID0xcc41 at16-bit register0x3107 and driver MCLK27MHz. DUT power/reconnect confirmation remains pending; no further DUT command issued during camera attachment.

30. User requested a commit here and a commit after each stage going forward. Prepared a checkpoint of completed Phases0–4, including compact hardware evidence receipts under `evidence/`. In-progress Phase5 I²C implementation is excluded from this checkpoint. No tools, full device-tree dumps, build caches or ignored logs are committed.
31. Committed completed Phases0–4 as `33d0926` (`Add RV1103 bare-metal bring-up through GPIO hardware gates`). Verified the exact staged GPIO source in an isolated build before commit, plus host transport/task checks. Subsequent completed stages will receive their own commits. Phase5 source/feature wiring remains uncommitted.
32. User confirmed separate DUT camera is connected and powered back on. First original polled I²C4 combined register read succeeded: sensor ID0xcc41, MCLK configured27MHz from detected GPLL, controller parent explicitly24MHz/100kHz SCL. Evidence `logs/phase-5/20261114T060551Z/`. This is partial Phase5 progress; interrupt-driven transfers and NAK/timeout validation are still pending, so Phase5 is not marked passed.

33. Phase5 PASSED: `logs/phase-5/20261114T060918Z/`, compact receipt `evidence/phase-5.json`. Original driver returned0xcc41 both polled and from IRQ-completed combined repeated-start reads; IRQ count increased by1. Address0x31 produced NAK in both modes. Deliberately masking I²C4 GIC INTID54 produced a bounded timeout (48,293 ticks at24MHz, ~2.012ms), and the following IRQ ID read succeeded. Sensor MCLK is configured27MHz from GPLL1188MHz /2 ×1/22; I²C parent explicitly24MHz with100kHz divider. REF CRU mux read0 corresponds to its198MHz input; DUT intentionally selects the known oscillator instead of inheriting that rate. No physical stuck-bus or waveform qualification claimed. Prepared separate completed-stage commit per user instruction.

34. Phase5 committed as b20da4d. User confirmed SPI MOSI/MISO jumper in place. Prepared original polled SPI0 driver, external loopback only,4KB deterministic pseudorandom data with full byte comparison. First init rejected an assumed1GHz CPLL; DUT register calculation showed996MHz. Revised driver to derive/report actual source instead of retuning PLL.
35. Phase6 PASSED: `logs/phase-6/20261114T061524Z/`, receipt `evidence/phase-6.json`.4096 bytes each at configured0.996,9.96,49.8MHz yielded zero mismatches and identical checksum0x90a534ae. These are nominal1/10/50MHz requests with -0.4% clock quantization, not oscilloscope measurements. Stage commit follows hardware gate as requested. Phase7 camera replay remains pending.
36. User suggested RustPython for Phase9. Inspected upstream README, VM manifest/root/implementation and mini REPL example. Embedding/native-function APIs are promising; current VM still imports Rust std, so bare-metal viability and64MB memory/boot budget remain unproven. Recorded candidate evaluation plan in PHASE-9-RUNTIME.md without starting Phase9 implementation or replacing the existing hardware gates.
37. Started Phase7 reference work. Existing Rust camera-probe captured3.98MB compact RAW10 directly from REF /dev/video0 (2304x1296,stride3072), while /dev/video11 is ISP NV12. No vendor rkaiq process ran. User manually positioned REF. Initial exposure128/gain128 was dark; runtime controls exposure1024/gain512 produced a recognizable reference scene. Preview uses existing Rust frame-preview with Rockchip contiguous little-endian RAW10 decoding; scene files stay ignored/local. DUT camera capture has not passed.
38. Matching REF config hash b210dc5fca942dc4725c6644b9b141d4a881c062e2c5f409bb9166020c92f9c6 confirms ftrace/kprobes unavailable. Fetched exact SDK commit0b5c1f30ca6333b7ec5af70d26511da9ef8d39af into isolated ignored baremetal/.tools/kernel-reference. Preparing temporary module write instrumentation and a bounded in-RAM recorder, without changing REF boot storage. Module compilation/loading and ordered write capture remain pending. User confirmed the existing Rust library is being used; clarified Rust camera-probe handles REF capture and no_std Rust runs DUT, while kernel camera drivers remain REF's hardware reference until replacement on DUT.
39. User cannot keep holding cameras, turned off room lights, and authorized exposure changes including approximately1-second exposure. Extended REF frame length to VBLANK31471 (VTS32767) and compared exposure1024 vs32759 at gain512 using the Rust capture tool. Preview means78.66 vs241.31/255; long exposure strongly increased signal and overexposed much of the scene. Both raw payloads captured successfully; images remain local/ignored. Configured a less aggressive exposure4096/gain256 afterward. No exact integration-time measurement or DUT frame is claimed.
40. Prepared original GPL runtime recorder and deterministic narrow hook script for pinned sensor/CIF/CSI-host/D-PHY module sources; no ISP hooks yet. First kernel preparation failed because vendor gcc-wrapper requires a `python` executable. That failure also removed compiler-dependent config options during olddefconfig; restored the exact retained REF .config before the corrected preparation. Rebuilding the container adds Python3 alias. No instrumented module has been loaded on REF yet; ABI/config checks remain mandatory before runtime replacement.
41. The optional container rebuild stalled resolving registry metadata; verified its live process and registry reachability, terminated only that task's shell/Docker CLI, then reused the completed local image with an in-container Python alias. Restored exact REF .config again before preparation. Current kernel prepare uses the vendor8.3 compiler in Docker and isolated output. The config hash remains the expected b210dc5f... during this attempt. No REF module replacement or DUT camera image yet.
42. Kernel preparation succeeded with exact REF config hash; recorder and instrumented sensor/CIF/D-PHY modules compiled. Compared all retained driver-source hashes against REF proof, module vermagic against originals, and undefined-symbol changes (only trace hooks added; memory-barrier call moved to recorder). Original modules backed up locally and unchanged on REF. Loaded recorder alone successfully, then attempted normal runtime camera-module unload before any instrumented camera module was loaded. Stock video_rkcif unload crashed in v4l2_async_notifier_call_unbind/csi2_remove, leaving it in Unloading state. Rollback could not remove that stuck module. ADB remains responsive. Saved full dmesg under logs/phase-7/ref-unload-crash-dmesg.txt. Stopped Phase7 camera work per the REF ground rule; reboot is required to restore the original camera stack. No REF storage writes or DUT camera capture occurred.

43. Recovered REF without physical action. Standard adb reboot request remained pending; CONFIG_MAGIC_SYSRQ is absent. After sync, wrote the already-proven RV1103 warm-reset key0xfdb9 to CRU0xff3b0c08. REF disconnected/re-enumerated and booted original modules with taint0. Paused rebooted frontend, verified GPIO release, restored runtime UART3 overlay and115200 baud. Existing Rust camera-probe again captured3,981,312-byte raw frame; evidence ref-recovery-capture.txt/ref-recovery.json. Failed unload sequence renamed to non-executable diagnostic text and README warns against retry. No instrumented camera module was loaded. Phase7 remains incomplete; choose a corrected teardown or different tracing method after static investigation.
44. Static investigation found embedded notifier ownership in vendor D-PHY, CSI2 and CIF-interface components. A runtime helper using public unregister/cleanup APIs still faulted in __v4l2_async_notifier_cleanup; stopped it immediately and saved ref-detach-crash-dmesg.txt. Recovered REF a second time by synced CRU warm reset, restored UART3 overlay/front-end pause, and re-proved original raw capture with taint0 (ref-recovery-2.txt). No modified camera module was loaded. Abandoned runtime graph-detach experiments; evaluating write-call instrumentation that leaves modules/graph intact, with host-side callsite inspection before any application.
45. Added a host-only whitelist generator for exact original camera ELF write calls:18 sites (14 MMIO,3 regmap,1 sensor), excluding one read-side barrier. Unsupported post-barrier instruction sequences fail closed. Three offline tests passed: Thumb forward/backward/range encoding, all14 store calculations compared with actual original Thumb instructions under Unicorn across32 register cases each (448 comparisons), and actual observer assembly preserving integer registers/stack/flags despite ABI-clobbering callees. Source program generation and tests did not write any device. Live observer installation and coverage are still unverified; no new REF instrumentation applied.
46. Extended offline checks to the original C prediction/branch core and automatically generated C site tables. Four tests pass, including448 C/Python/original-instruction comparisons and compilation/data validation of all18 generated records. The new generated-table test initially failed from a missing tools import path; corrected and reran the full suite successfully. User confirmed lights going out; retain stationary cameras and adjust exposure/gain as needed. No live camera call changes or DUT raw frames in this step.
47. Implemented original short-descriptor walker and REF-specific read-only memory adapter for trace addresses. Host suite now passes6 tests; callback checks cover section/large/small-page translation and fault handling without reading mapped devices. Matching vendor GCC8.3/kernel config compiled both objects successfully after correcting the staging Makefile. REF read-only health check reports taint0 and64MB System RAM. Updated trace README to remove obsolete replacement-module deployment instructions. No observer installed or live call sites changed; runtime translation validation, pin/apply/restore and capture remain open.
48. Read-only address-translation probe PASSED on REF. Known allocated RAM matched __pa and stored value; VICAP mapping endpoints translated correctly; guarded reads rejected device and user addresses. Temporary mapping never dereferenced. Probe insmod/rmmod both returned0; original Rust raw captures before/after each returned3,981,312bytes. Out-of-tree module load set expected taint4096, with no fault reported. Original camera modules and graph untouched. Saved live module text/driver identities for upcoming validation; no call redirections applied. Full logs remain local under phase7.
49. Live read-only preflight pinned3 camera-module owners and validated all18 branch targets/link modes plus post-call instruction bytes. Standalone validation loaded/unloaded successfully, original refcounts restored and full raw capture passed afterward. Integrated shared preflight with bounded live observer and transactional patch core. Seven host tests pass, including mismatch/unreadable rejection at every batch position before any code write. Exact kernel/GCC build succeeded. Idle live apply/restore/unload passed, active self-reference tracked correctly, and original raw capture passed afterward.
50. First actual observed Rust capture succeeded and hooks restored/unloaded, but trace had45 observation errors. Diagnosed module-address rejection below PAGE_OFFSET; corrected guarded translation to use MODULES_VADDR. First post-capture verification reused an existing output filename and was rejected by camera-probe; reran with a fresh name and full capture passed. No REF fault or graph teardown occurred.
51. Second live observed capture PASSED:3,981,312byte raw frame and201 events (148 sensor,50 MMIO,3 regmap), dropped0/errors0. Original calls restored and observer unloaded, statuses0; subsequent original raw capture passed. Local evidence live-events-2.txt/live-observer-capture-2.txt/post-observer-capture-2.txt. REF remains healthy with expected out-of-tree historical taint4096. Trace includes sensor initialization/VICAP/CSI/D-PHY, but MMIO is pre-store observation and clock/power/dump coverage remains open. No DUT raw image or Phase7 gate yet.
52. Collected108 source-reviewed clock/config registers at idle and during a10-warmup REF stream; full3.98MB capture passed and runtime_status active. Saved partial snapshots/clk_summary under ref-dumps. No full-range dump claim. Normalized trace with strict event-integrity and write-range guards; remapped DMA buffers to48/52MB and generated original Rust replay constants. Added bounded sensor-write transfer and camera feature with noncacheable DMA mapping, timeouts, FIFO/status checks and UART RGB preview.
53. First DUT RAW capture WORKED: run20261114T072933Z captured10 alternating frames, status0x101/0x202,933120 changed words matching packed payload.192×108 RGB preview decoded and inspected: too dark for recognizable scene. Run20261114T073140Z repeated10 frames with near-full-frame exposure32759 and high analog/digital gain; still dark. Both harness checks passed, but these do not close Phase7's scene/full-dump/named-driver requirements. User asked asynchronously for a stationary lit scene when convenient; no holding/replug required.
54. Added optional SC3336 internal-pattern diagnostic. Run20261114T073406Z passed10 frames but high gain clipped much of the pattern. Reducing diagnostic gain exposed an inline stack LDR literal-range build error. Shell continued after failure and run20261114T073531Z loaded previous image; explicitly exclude it as proof of new source. Replaced IRQ-stack literal load with MOVW/MOVT, rebuilt successfully and launched a fresh unity-gain pattern run20261114T073621Z. Host4 tests, observer7 tests and295-task validation passed. Phase7 remains open.
55. Fresh unity-gain sensor-pattern run20261114T073621Z PASSED10 consecutive frames and complete preview transport. Decoded/inspected dut-pattern-unity-preview.png: visible black-to-white gradient. Confirms synthetic pattern delivery/packing and preview; does not satisfy real-scene/true-color gate. Updated stack initialization exercised successfully. All build/capture sessions finished; DUT stopped streaming, UART R recovery retained. Awaiting convenient lit scene while further Phase7 register/dump work remains available.
56. Added temporary public-API clock-reference holder for CIF/CSI0/PHY/ISP and framed read-only full-resource snapshot helper. Original pre-capture passed. Full VICAP/CRU/GRF reads passed; IOC declared span hit userspace external abort atff570000 after0x38000 bytes. Automatically stopped scan/unloaded helper, reported it, verified REF remained responsive/taint4096 and original full raw capture passed. No kernel crash or reset. Preserve partial raw file as failed evidence; never label IOC tail captured.
57. Added explicit IOC-prefix profile and blocked repeated full IOC read. Collected complete PMU/DPHY/CSI0/ISP resources and readable IOC prefix with clock references. Matching8 profiles then captured during a30-warmup REF stream, each with active/CIF-enable/taint state receipt. All byte counts and CRCs validated. Helper released successfully; post-release original3.98MB capture passed. Saved binary/text manifests, generated ref-dumps/idle.txt/streaming.txt and diff. Only IOC tail remains unverified; snapshots across blocks are not atomic and contain dynamic/status registers.
58. Found REF sensor clock actually selects24MHz oscillator despite nominal27MHz sensor mode. Made Phase7 replay match live REF (Phase5-only setup unchanged), emitted selected readbacks, rebuilt and RAM-loaded run20261114T075157Z. Passed10 frames at steady~799203us, clean statuses, complete synthetic preview inspected.32 configuration readbacks match manifest-validated REF snapshot after explicit masks/DMA-remap/polling exceptions; dynamic interrupt status excluded. Six host checks pass including checksum/truncation/mismatch sensitivity. REF healthy, no helpers loaded; DUT stopped in this image. Real scene and named-driver requirements still open; no Phase8 or phase completion claim.
59. Preserved proven replay image/manifest under ignored build/phase-7-replay-baseline. Replaced default timestamped replay with original named SC3336 and RV1103 receiver modules, retaining observed analog preset facts. Added combined one-byte sensor register reads and9 control readbacks. Strengthened capture sequencing/interval checks. Build provenance now includes nested source modules. Default pattern build succeeded without warnings.
60. Named-driver pattern run20261114T080339Z PASSED10 consecutive clean frames,9 correct sensor readbacks, expected DMA payload count and complete preview.32 selected config comparisons still match REF. Decoded/inspected synthetic gradient. Named real-camera build/run20261114T080816Z also PASSED10 frames/~799203us, all readbacks correct, pattern disabled and long-exposure/high-gain values confirmed. Real preview remains dark; no scene/phase qualification claimed. Optional legacy replay feature compiled but was not loaded; packaged image remains named real-camera.
61. Captured separate4KB PMU IOC/GPIO0 page at idle and during original REF raw stream. Released helper and re-proved full original capture, taint4096/no bm modules. Source-coverage audit against actual manifest-checked snapshot bytes shows all SDK-known pin-control fields fit captured main IOC prefix/PMU IOC page. The declared main IOC tail remains faulting/unprobed and explicitly excluded. Added CAMERA-REGISTERS.md and PHASE-7-STATUS.md with evidence scope, limitations and resume steps.
62. Rechecks: host6 tests, observer7 tests,295-task validation, both named-driver32-register comparisons and whitespace checks. Physical recognizable-scene blocker persists and latest real PNG revalidates darkness with controls correctly applied. Remaining visual gate needs a stationary lit scene. Do not begin DUT Phase8 or mark Phase7 passed. The plan's explicit parallel-reference-capture exception still permits useful REF comparison work, so leave the full goal active rather than blocked while preparing that evidence. No phase7 gate commit yet.
63. Used explicit parallel REF-capture exception to prepare ISP reference data. Inspected live pipeline/installed Rust CLI/factory IQ and successful dry-run. Selected VGA NV12 on image11 to fit12MiB CMA. Installed Rust first-frame-sc3336 with optional noise modules disabled captured460800byte ISP frame using11145byte Rust-generated parameters; three raw-bridge completions/no cleanup errors. AE/AWB disabled, frame association/cold-start not proven. Pulled data/initial report to ignored logs/ref-isp and decoded/inspected dark luma PNG. Original raw capture afterward passed, taint4096. REF controls now fixed-startup values, VGA output retained; no persistent writes/module teardown. DUT Phase8 not started; next permitted work is REF stats/automatic3A comparison capture while waiting for lit DUT scene.
64. REF automatic Rust AE/AWB capture succeeded:33 raw completions,22 statistics,21 parameter submissions, no dropped records/cleanup errors. Saved10 artifacts and hashed summary.14/22 exposure lookups exact,19 decisions; final association missing, physical parameter timing unverified. Decoded/inspected brighter but noisy luma (mean31.23), not convergence/image-quality qualification. No DUT Phase8 work.
65. Captured full ISP resource during91-frame fixed-parameter REF stream, with active-state receipt/CRC/hash. Clock helper released, original full raw capture afterward passed and taint stayed4096. Selected AWB audit confirms SDK-documented read/write differences at0x530/0x534; six interpreted channel pairs match, gain2 pairs unresolved. Saved REF-ISP-REFERENCE.md with limits and final runtime state.
66. Reassessed blocker after completing useful allowed reference captures. Both real previews remain unrecognizable despite verified DUT controls and reference AE/AWB activity. Same illumination blocker has persisted beyond three goal turns; further dark repeats cannot satisfy visual gate and DUT Phase8 is disallowed until it passes. All jobs finished, both boards recoverable/REF healthy, work and resume steps preserved. Set goal blocked pending stationary lit DUT scene; do not claim Phase7/mission completion or create a gate commit yet.
67. User resumed with “ok go ahead”; fresh blocker audit. Rebuilt/RAM-captured20261114T150900Z: ten frames, night settings clip white under changed illumination. Preserved night baseline; added camera-low-light task/feature and set ordinary diagnostic to unity gain.1024-line run20261114T151123Z was dim;8192-line run20261114T151455Z shows real pale surface/edges, clean ten frames,9 controls/32 register comparisons. Not yet a high-contrast colourful target. Requested stationary colourful book/box/card/screen via async input, without holding or rewiring. Added independent mechanical capture auditor and negative tests; fixed a test's startup-vs-later interval assumption;7 host tests/296-task validation pass. Low-light branch compiled, not reloaded; current packaged/DUT image unity8192. No Phase7 pass/commit or repeated blocked update.
68. User repositioned target (“how bout now”). Run20261114T152545Z PASSED raw gate: recognizable printed carton label/barcodes and contrasting surroundings, ten clean alternating frames,9 sensor readbacks/32 selected register matches, complete preview. Pattern disabled,933120 changed payload words. Recorded phase-7 receipt with hashes/limitations; scene pixels remain local/ignored. User explicitly requests continuing8 and9 after final checks. Finish checkpoint commit, then Phase8 actual ISP integration before interpreter gate; preserve RAM-only and remaining full mission.

69. Phase8 fixed offline ISP diagnostic produced a recognizable processed carton/barcode image on DUT (20261114T155539Z). Partial live ISP tracing restored cleanly, fixed and automatic reference captures saved. Existing no_std Rust3A library now compiles for DUT; measurement/IRQ path under test. Full3A/Phase8 and interpreter/Phase9 gates remain open.

70. Calibrated AE/AWB ran on DUT statistics. Fixed a newly exposed main/IRQ stack overlap, separated stacks with a1MiB MMU guard, then completed six actual feedback frames and five IRQ-applied gain updates (161302Z). Normal AWB scheduling map now matches82 reference writes;32-frame test in progress. No Phase8 or Phase9 gate claim.

71. Phase8 bounded linear hardware gate PASSED (163158Z):32 frames,31 IRQ updates,186 gain-word readbacks,80 fixed-register matches, normal30fps sensor timing, actual calibrated AE/AWB settling and saved/inspected Linux comparison. Evidence receipt records exclusions. User may put REF down. Checkpoint commit precedes Phase9 runtime/allocator work.

72. RustPython ARM experiment failed on std dependency with its required1.99 toolchain; user accepted MicroPython. Original RV1103 port boots a UART REPL and passes the first full Python peripheral/camera/settings/GC script on hardware. Added reclaiming Rust allocator, separate Python GC heap, alias-safe SPI and read-only NV12 views. Final source/transport verification precedes Phase9 commit.
73. User expanded remaining scope: standalone microSD boot, USB debugging/REPL or ADB, then SeedSigner MicroPython port with real PCB LCD/buttons/camera. Milestones documented; full project remains active after Phase9.

Phase9 checkpoint: five repeated RAM boots and final console-20261114T172550Z hardware API script passed. Receipt: evidence/phase-9.json. Rust heap returned to zero after two camera captures; Python GC/OOM and read-only frame checks passed. No storage writes. Short capture windows were insufficient evidence of a hang; measured RAM handoff/self-test timing is not SD cold-boot timing. Standalone microSD, USB debugging and full SeedSigner/PCB integration remain open.

Phase10 preparation: fast-start RAM boot173336Z reached initialized MicroPython13153us after payload entry (excludes ROM/DDR). Full runtime hardware API script173414Z passed. Generated validated2MiB raw SD candidate with unchanged DDR plus original runtime; exact stage/header hashes checked and12 host tests/307 task checks passed. No SD write/insertion; awaiting a spare card and explicit authorization. PHASE-10-BOOT.md records candidate, size uncertainty and measurement limits.

Phase10 independent REF GPIO observation173649Z:13094.375us high pulse vs DUT13112us, max within-pulse sample gap130083ns. Whole-capture Linux scheduling gaps retained separately; no power-on/SD claim. Spare-card/erase authorization requested asynchronously; none connected at last read-only disk inventory. REF source-inventory helper was OOM-killed (no other killed process observed); moved all AST analysis to Mac. Original REF raw camera subsequently captured3981312bytes successfully, taint remains4096 and original modules remain loaded. Read-only /opt/src snapshot contains113 Python source files/2,904,054bytes; local ignored inventory records actual fork/version and imports. No app code changed.

User corrected the interpretation of13.1ms: current boot and app launch take at least about30s. Acknowledged that payload-to-initialized-MicroPython is not boot-to-app, and the replacement does not run SeedSigner yet. Updated primary performance reporting to power-on→usable app screen/input and camera readiness, while retaining original power→REPL gate and clearly secondary internal timing. No end-to-end speedup established.

Phase10 camera timing instrumentation passed on DUT174525Z: init21ms; first processed output702300/765364/710672us; full32-frame captures5320135/5377477/5326094us. Outer Python timer agrees. Full8-marker peripheral/camera/GC regression174614Z passed. These exclude boot/app and are not FPS. User reports10+FPS Linux and clarified this was just checking; do not rewrite streaming solely for this comparison. No streaming changes made. API metadata and initial-ISP timeout/error rejection added, latest regular-file SD candidate revalidated. Card/erase request remains unanswered; no external card found and no storage written.

User connected spare4GB card (host disk7,4060086272bytes) and authorized continuing after image-size explanation. Verified source image/stages and target identity. macOS denied direct administrator helper access before write; staged retry also denied raw-device open with writeAttempted=false. Used installed balenaEtcher through UI, explicitly selected runtime-sd.img and disk7, accepted expected missing-partition-table notice for raw ROM image. UI reported Flash Completed/1 Successful target. User moved card to DUT before independent host readback; no claim of our own byte verification. Card no longer appears in host disk list. SD-only UART-reset capture180701Z underway, no USB db issued.

Standalone SD runtime confirmed: controlled reset180943Z produced DDR/hello/REPL with no USB db, about192ms reset request→REPL marker; full API gate181415Z passed. User requested fast onboard LED then50% slower. Original GPIO3_C6 LED implementation verified at10Hz in RAM, changed to5Hz (100ms on/off); final RAM test181916Z showed10 transitions/second and0 pad errors. Etcher hit a helper-spawn failure; app restart/reselection recovered and final image9406c4fcc7c795ecf519bc4a3b810b7d2b2a06c9bf2bc6ff8643a9917bc7a6b8 flashed successfully. User reinserted card. Controlled SD reset182159Z passed at195140.75us request→REPL. Full gate182256Z passed all8 original markers plus LED-during-camera:108 transitions/10801ms,0 pad errors. No independent raw host readback; real SD boot and APIs verified. Cold power-edge/first-frame and app readiness remain open. Current DUT is SD-booted atREPL,LED5Hz, GPIO52/53 released, SPI loopback still installed. REF remains powered/reachable.

Phase10 cold-rail fixture preparation: verified Mini schematic H2 pin3=3V3_OUT (pin1=VBUS5V), REF inputGPIO1_C5/physical6. Added input-only power observer, native32-bit MMIO access, temporary C4/C5 pull-downs, UART TX high-Z plus both UART pull-ups disabled until sensed power rise, exact saved-state restoration, bounded capture and negative timing audits. Real REF TX isolation/restoration and300ms logic-pulse dry runs passed;17 host tests/312 task checks pass. Orange role is power-sense-pending, original GPIO gate disabled in devices.json and REF helper guarded by/tmp/bm-orange-power-sense. Asked user to unplug DUT, move orange DUT end11→3, then power DUT; other wires and SD unchanged. Live capture process/session85387, folderlogs/phase-10/power-20261114T183856Z, armed for300s. No real power timing result yet; UART TX can remain isolated if timeout sees C5low. Read POWER-ON-TEST.md and recheck live handle/current GPIO before any follow-up; do not drive REF C5 or clear interlocks while orange may be on3V3.


User deferred cold-power benchmarking and prioritized SeedSigner buttons/LCD/camera, excluding smartcard software. No physical wire was moved. REF UART mux/pulls/direction restored exactly (0x55/0xaaa5/0x300); console-20261114T184604Z confirmed DUT REPL and 5Hz LED. Power observer finished without a power edge; it is not a cold-boot measurement. Unused preparation/tools/tests archived under ignored logs/phase-10/deferred-power-tools. User confirmed the existing board that ran Linux, not the current HOTHMI carrier: bench LCD DC56/RST57, 240x240; button mapping follows PCB-SOFTWARE-COMPATIBILITY.md. Remove SPI loopback and resolve UART2/button pin conflict before connection/output tests.


App/USB checkpoint: user confirmed a third Luckfox Pico Mini A without onboard flash as the app target, preserving the existing wired REF/DUT fixture. USB debugging is explicitly important; implement and verify USB console/script transfer and reconnect before relying on the third board without UART. Existing Linux-tested 240x240 LCD/buttons profile selected; smartcard software excluded. Added app-runtime build feature retaining fast CPU startup while suppressing all GPIO52 timing-output writes (GPIO52 is the bench center button). mise baremetal:app:build succeeded; all12 baremetal host checks passed. This is preparation, not a running SeedSigner app or USB implementation. No new payload downloaded, SD written, or pin output enabled. Shared build/hello artifacts now contain app-runtime; the existing runtime-sd.img and installed card remain the previously verified fast-boot build. Rebuild fast-boot before regenerating that diagnostic SD image.


USB console preparation checkpoint: original no_std Rust DWC3 device driver and CDC descriptors added behind usb-console feature; foreground servicing at REPL/VM branches/output/delays, bounded buffers/backpressure, Ctrl-C pending exception and Ctrl-] warm reset, retained UART recovery. DMA60MiB reserved outside camera buffers. Host USB paste uploader selects matching development device and saves nonce completion evidence. 3 descriptor tests, cross-build, uploader CLI and12 existing host checks pass; evidence/phase-11-usb-preparation.json is explicitly HOST-ONLY. No USB payload loaded and no storage written. Last enumeration showed REF ADB only, no maskrom DUT (the verified SD runtime still runs). Asked user to power off DUT, remove spare SD and repower, keeping all wires/REF unchanged, for RAM-only USB testing; no acknowledgement yet. Shared build/hello artifacts now contain usb-console; installed SD remains the verified5Hz runtime. Hardware gate remains open; do not claim usable USB or remove debug wires yet.


USB review checkpoint: still no maskrom DUT on read-only enumeration; no payload download/storage write. Extracted the actual endpoint-zero phase transitions into usb_control.rs and hardened completion direction validation. Five control tests cover descriptor IN/data OUT/status/no-data and wrong-direction/duplicate events;3 descriptor tests and cross-build pass. Updated host-only preparation receipt. Current blocker for hardware proof remains DUT SD removal and repower (request already pending); no new wiring change requested.


USB hardware blocker revalidated20261114T190106Z: host USB inventory exposes only REF2207:0019/ADB0a523b8b23110ffc; rkdeveloptool ld finds no maskrom target and no external card is present on Mac. Actual DUT UART LED gate console-20261114T190106Z passed (10 transitions,0 pad errors), confirming the existing SD runtime remains alive. USB candidate has never been loaded. SD removal/repower request has remained outstanding across three goal turns; no live capture/download process is running. Mark goal blocked pending physical DUT power-off, spare SD removal and power-on; REF/jumpers unchanged. Resume with enumeration, then RAM-only USB candidate load and UART capture; preserve existing wired fixture. No USB, app or cold-power completion claim.


Phase11 RAM USB milestone passed. DUT0 native macOS CDC enumerated; initial host TX reached REPL but IN stalled because bulk endpoints were configured before bus reset/host configuration. Moved non-control resource/config commands into SET_CONFIGURATION and added full-packet ZLP termination. Final DUT0 boot191709Z/full API USB191721Z passed GPIO/I2C/SPI/two460800byte camera captures/settings/GC (Rust heap0). Exact USB output audit191928Z passed46593bytes with32768byte largest block. Ctrl-C from infinite Python loop and3 serial reopens passed191911Z. One stress script initially used unsupported slice syntax in minimal MicroPython; fixed the test to exercise transport without slicing, not a USB corruption finding. User added DUT1 Mini A atUSB101 with existing Linux-tested LCD/buttons and aimed DUT0 camera at its screen. Added GPL host-tool patch selecting RAM db by explicit USB location, requiring2207:110c maskrom; storage commands remain unavailable through selector. DUT0 remains201; REF originalADB untouched. DUT1 USB-only build uses unique rv1103-dut1 identity; USB script192141Z proves actual UART pads input/mux0, IER0 and IRQdisabled. Three reopens/Ctrl-C and USB Ctrl-]→maskrom101 passed192218Z. DUT1 currently maskrom, ready for next RAM load; DUT0 remains running tested UART+USB build and camera. Evidence/evidence/phase-11-usb.json (path baremetal/evidence/phase-11-usb.json). No SD write or working SeedSigner app claim. User is leaving; continue autonomously with current hardware and use software reset/reload, no new wiring/aiming requests. Next: LCD/buttons on DUT1, observe via DUT0 camera; preserve all3 devices and REF source/card.


Phase12 checkpoint completed for bounded software scope, full app/optical gates remain open. Frozen imported seedsigner_port.buttons passed195043Z; core MPZ/slice/format/timerwrap, held-Key2 suppression and six display guards passed on realDUT1. Native register readbacks: input directions/pulls/mux matchbench, LCDDC56/reset57 outputs, SPIdivisor20. Full ST7789 profile, len-1 TX counter, complete240x320 backing-RAM fill and optional100kHz-or-slower GPIO SPI diagnostic implemented; no recognizable optical output in current close/oblique/cropped camera view. Don't claim LCD success or infer a proved board fault. Independent observer pixel hashes differ (no stale-frame evidence). Further safe probe found DUT1 ALSO has a responding SC3336: ID195559Z and actualRGB camera195651Z passed (different carton scene fromDUT0's LCD view). Camera is available locally; earlier no-confirmed-camera assumption superseded. Reinitialization/fill after camera195824Z passed; preservation without LCD reinit/continuous preview still untested. Final frozen-core DUT0 boot195253Z and full GPIO/I2C/SPI/two-camera/settings/GC USB195410Z passed; session66646 and90177 are terminal. All tool sessions terminal, no active captures.19 host tests pass. Receipt evidence/phase-12-app-io.json; PHASE-12-APP-IO.md is the current handoff. Current shared build artifacts are final frozen-core usb-console forDUT0, matching its running firmware. DUT1's matching bench-ui image/manifest saved logs/phase-12/dut1-frozen-tested. Both devices reachable via uniqueUSB identities; REF untouched. Preserve originalwiredDUT0fixture, no physical actions needed for independent work. No SD writes. The full SeedSigner app is NOT running: actual controller/views/rendering/models/crypto/QR and app boot/navigation still need porting/verification. Next useful work: native camera→RGB565 app display adapter and actual app rendering/controller integration; keep optical check open and use software reset when reloadingDUT1. User is away and explicitly requests continuing with existing setup; don't stop for re-aim/rewiring while software work remains.


Native camera/display checkpoint: realDUT1 gate201402.499624Z passed two read-only460800-byte NV12 captures→nativeRGB565→SPI submissions without display reinitialization. GPIO/mux/divisor preserved; Rust heap baseline restored; conversion/blit233/232ms, capture5255888/5256468us. Not previewFPS, appboot or optical proof. Receipt evidence/phase-12-camera-blit.json;2RGB tests+19bringup tests pass. DUT1 remains running bench-ui boot201148Z; DUT0 remains committed frozen-core usb-console, REF untouched, no SD writes. Host USB log timestamps now include microseconds after two rapid scripts collided at folder creation (no board script ran on failed attempt). Pinned official Arm14.3.rel1 C++/newlib toolchain installed only in ignored local cache, SHA verified; existing pinned SeedSigner LVGL corpus and existing portability patches compile542objects. Archive/bridge are NOT linked/running yet: allocator, constructors, unwind metadata, memory layout, MP UI module and actual screen/controller gates remain next. Keep native UI initial testing on wiredDUT0 with UART recovery; don't disturb DUT1 button/UART pads or DUT0 GPIO loopback. Current LCD optical view remains inconclusive; user away, continue independent app software. All build/upload sessions terminal at checkpoint. No full app completion claim.


Native Home renderer checkpoint: native-ui firmware runs on wiredDUT0 boot logs/phase-12/20261114T202608Z. Genuine locked main_menu_screen renders, exports read-only240x240 RGB565, and produces Scan index0 / Right+Enter Seeds index1 callbacks. Decoded native-home.png visually inspected: correct title/powericon/4tilelabels/icons/orangefocus. Real gate logs/phase-11/usb-20261114T202711.768518Z passed;20 error/render/GC cycles202742.154315Z returned nativeheap42015bytes exactly; fullGPIO/I2C/SPI/two-camera/settings/GC gate202747.583864Z passed with samebaseline. Rawimage1486708bytes/BSSend0x177618 below4MiB; relocatedSVC27..28/IRQ29..30MiB, guards26/28, heaps/DMAunchanged, shadow32MiB. Newlib C allocator uses Rustbuddyheap, constructors invokedafterheapinit, EHtablespreserved. InitialmalformedJSON resetdiagnosed byUART instructionabort202346Z; LLD TARGET2 defaultwasincompatiblewithGNUbaremetalEHABI, --target2=rel fixedrealcatch/recovery (LLVM D149458 reference). Input firstpressdrop fixed by settling releasedkeypad afterscreenhandoff, matchingexistinghost. Initialframeexport20stimeout gave219rows;60sbound yieldedcompletevalidated115200bytes. First hostprobe usedunsupported time.ticks_diff, correctedtest;5scaptureendedbefore~12sloaderdelay, later20scapturepassed. One UARTprobe overlapped bootcapture and hadsplitoutput; rerun202436Z cleanpassed, don'ttreatmixedlogasproof. Receipt evidence/phase-12-native-ui.json.19hosttests pass. No storagewrites, REF preserved, DUT1 remains nativeRGB bench-ui201148Z. Allsessions terminal. Fullcontroller/app and physicalLCD/buttons notqualified; next moveactualrenderer toDUT1 preservingUSB-onlyUARTpadrelease, thenfreeze realcontroller/viewadapters andexpandactualregistry. Don'tclaim11msrenderasappboot/coldpower. Useraway; continuewithoutrewiringrequests.


DUT1 actual-native-renderer milestone: final app-ui boot logs/phase-11/dut1-20261114T203237Z, frozen cooperative adapter+camera/Home-restore gate203256.506883Z, final nativeHomeframe203317.045222Z allpassed. Native framehash6d46d67b07a7be9a35e87012261466fb05fd3ca06e3ac7a759fae4562bf62aac matchesDUT0; render+SPI194ms, notappboot. Frozen ScreenSession usesrealMPJSON, debouncedinput→completeLVGLpulses, timers and screenhandoffheldsuppression; constructor initializesbackendbeforedefaultbuttonread. Actualheldmask64 suppressed; injectedacceptededges selectSeeds1. Capturesubmission and Home restorewithoutLCDreinit preserveheap42015bytes andUARTpadmux/output/IER/IRQzero.22hosttests pass. FoundnativeINVOFF0x20 differedfrominstalledST7789.NORMAL_COLORS_REQUIRE_INVERSION=True; correcteddefaulttoINVON0x21, nootherpins/clockchanged. Opticalobserver203317.045224Z stillhasno recognizableHome incloseobliqueview. Imagesdifferhashesacrosscaptures; notstale-frameevidence. Don'tclaimphysicalLCDsuccess/switchqualification orfullapp. Native registryHomeonly; actualController/View/screencontracts, longhold/lifecycle/models/QR/crypto andstandaloneappbootstillopen. DUT0 remains38bf1edheadlessUI withcameraobserver, REF preserved. Sharedbuild/hello nowfinalDUT1app-ui; wiredharnessnewguardrejectsDUT1/appbuildsbeforeenumeration/db (negativegate logs/phase-12/20261114T203342Z). NoSDwrites, noactiveprocessesatcheckpoint. Receipt evidence/phase-12-dut1-native-ui.json. Nextusefulwork: realappController/View compatibility and configurationadapters + genuine screenregistryexpansion, preserveunsupportederrorsinstead oftoywalletflows. Useraway: continueindependentsoftware, no rewiring/aimingrequiredfornextsteps.


Original navigation/native registry checkpoint: full43lockedbuilders registered on wiredDUT0 native-ui, introspectionui.screens() andmanifest/cachekeyincludeexactlist. Finalboot logs/phase-12/20261114T204128Z; frozenoriginalDestination/BackStackgate usb-20261114T204159.328829Z passed; actuallistDown/Enter,topBack1000,2tileRight/Enter,Homecleanupgate204159.863413Z passed. Sourcegeneratedwholeclassesfrompinned3rdIterationapp, annotations/dataclassruntime removed, equivalent4argconstructor andlistbase; routing/redirection/equality/recursive_sensitive_repr methods unchanged. app/navigation-provenance.json recordsclass/filehashes/transform/output.3differentialtestsagainstactualCPython/dataclassclasses+realfrozengatepassed;25hosttests total, noskips. Registryavailabilityisnot43workflowqualification. Originalfirstregistrycyclefailedstrictcoldheapcheck; isolated4cycleprofilesstabilized at52553 afterfontcaches. FinalafteractualtextwidgettestcoldHome43018→warm53300, fivefurtheridenticalnavigationcyclesfixed53300. Textcallbackreviewfoundoldsharedcopyhelpercouldsilentlytruncate>255bytes; nowexplicitRuntimeError,consumedbufferisvolatilecleared. Actualseed_add_passphrasewidgetKEY3gate204158.658955Z provedexact255ASCII/254UTF8and explicit256byteerrorsfollowedHome recovery. Widersupportedtext andsinglependingeventslot/lifecycle/contractsremainincomplete; notseed/signingflowqualification. FinalfullGPIO/I2C/SPI/twocamera/settings/GC gate204221.658896Zpassed withheapbaseline53300. Raw1817316bytes,BSSend0x1c76d0below4MiB. DUT0runningfinalnewimage; DUT1unchanged54bfdcaHome-onlyapp-ui, opticalLCDstillunconfirmed. Sharedbuildnowwirednative-ui(defaultdevUSBidentity);DUT1loaderrejectswrongbuild. NoSDwrites/REFchanges; allsessions terminal. Receipt evidence/phase-12-navigation-registry.json. Next: actualController/View sourcecompatibility/configuration/resultadapters, settings/model/crypto/QR/storageandstartup;don'tsubstituteatestView/menu/demoappforrealSeedSigner. Useraway, continuewithcurrenthardware.


Basic original Screen contract milestone: frozen screen_contracts mapsButtonList/LargeButton/MainMenuarguments toactualnativebuilders andvalidateschoice/back/powercodes. Originalinheriteddefaults generatedfrompinnedappAST, sourcehashprovenanceapp/screen-defaults-provenance.json. DifferentialtestsagainstexistingLinuxcontracts+originaldataclassfields pass fordefaults/layout/scroll/colors/icons/translationoptout;29hosttests total. Correctoriginalaccent#FF9F0A nowinappconfig(previousdirectHomefixtureusednative#FFA500default). UnreviewedScreen subclasses, Button_cls styling andconfiguredlong_press_keyraiseUnmigratedScreen; NULtext rejected. ScreenSession show_screen/screen_result/run_screen exposes class+kwargsdictboundary; rawshowclearsbuttoncountvalidator. FullController/View NOTyetwired/importable, fullwalletlogicnotreplaced. RealDUT0 boot logs/phase-12/20261114T204642Z /frozengate usb-20261114T204714.964041Z passed3basicclassconfigs, ButtonOptionfixtureobjects and actualnativecallbackindices/back1000 throughdebouncedinjectededges. Thesearetestfixtures, notproductionViewsorphysicalswitchproof. Rawimage1821140bytes;nativeheapaftergate53037(onlycurrentfixturemix, notanewglobalbaselineclaim). Finalsharedimage/runningDUT0native-ui containadapters;DUT1unchanged54bfdcaHome-onlyapp-ui,opticalstillopen. NoREFchanges/SDwrites;allsessions terminal. Receipt evidence/phase-12-screen-contracts.json. Next integrateactualController/Viewrun_screen/servicesandremaininggenuinecontracts/dependencies; alsoQRdecoder/models/crypto/settings/storageandcompleteappboot. Preservefullscopeandavoidtoyappsubstitution; userawaycontinuewithcurrenthardware.


Original settings dependency checkpoint: source-derived wholeSettingsConstants/Entry/Definition(60entries) andoriginalSettings.parse_settingsqr frozen asportSettingsQR. Originall10nmarkerretained; noLinuxOS/peripherymock:explicitrealhardwaremetadata+English-onlyfrozenlanguage discovery. ExplicitEntryconstructor/eqNotImplemented/repr replaceCPdataclassruntime, methods/provenancepreserved. Parserloggingremoved; realfloat64conversion or explicitunsupported error, nofakefloatparser. NativeUI/appUI MicroPython nowdouble+fullpinnedlibm; globalNotImplementedconstantenabled. Originalschemafloatconstantswouldbreakminimalfreeze, sohostMakefileexportsBM_NATIVE_UI andmanifestonlyincludeschemaforappbuild. MinimalMParchive+configuredusb-consolelink andfinalnativeUIbuildpassed. Initialbaselinecargo--manifestfromrootdidn'treadbaremetal.cargo config; reranpropercwdconfiguredcheck, useonlylogs/settings-baseline-link-configured-check.txt asbaselineproof. Nativefreeze/source changeschangedimagehashaftermatrixbuild, soexplicitlyreloaded/retestedfinalartifact. Finalboot logs/phase-12/20261114T205505Z; actualschema/parser/double/30GCcyclesgate usb-20261114T205541.162242Zpassed, entirepublicschemaauditedexact60entries SHA d029fa08de4ecfefdefe1805ac712c1efa5a8bc2ebf1a081e62ffa8c0be5b1a9. Nativeheap1120beforeUIfontinitfixedacrossparsercycles.32hosttests(3newagainstactualoriginalschema/parserclasses)allpassno-skips. Screenadaptergate205544.153536Z andfullGPIO/I2C/SPI/twocamera/settings/GCgate205544.787006Zpassed. NoSettingssingleton/apply/setter/persistence/platformeffects portedyet; rawSettingsQRFREE_ENTRYdoesnotenforceminmaxuntilsetter, metadatafloor10/ceiling1000preservednotclaimedcryptovalidation. Schemahardwarechoicesinertupstreammetadata, noall-driverpromise; smartcardsoftwarestillexcluded. Finalraw1879284bytes/BSSend0x1d76d0below4MiB; currentDUT0/sharednativeUIartifactsupdated, DUT1unchanged54bfdcaHome-onlyappUI,opticalopen. NoREF/SDchanges, allsessions terminal. Receipt evidence/phase-12-settings-schema.json. Next actualSettingsnativeRAMstore/platformservices+Controller/Viewstartup/model/QR/cryptoprereqs; keepfullappscope, nofakeproductionViews orcryptofallbacks.


User supplied actual PCB path in sibling seedsigner-luckfox-pico repo. Read-only PCB pads/schematic pin names establish LCD reset51/DC52/backlight43, CS48/SCK49/MOSI50; keys57/59/56/54/58/55/4/53. This differs from earlier assumed bench profile; prior dark-LCD/stuckmask64 observations were wrong-board configuration, not a proved panel fault. Reset DUT1 to release wrong56/57 outputs after restricted Pin API could not quiesce them directly. Added explicit mini-pcb-ui/mini-pcb240, GPIO0_A4 input forKey2 and high backlight43; old profile and fixtureGPIO/SPI APIs reject on app target. Physical white/Home/static-camera images now visible; user ready+k and exercised every key, monitor usb-20261114T211837.412363Z sawmask255 plus real selection/powercallbacks. Native UARTmux/IER/IRQ0; GPIOB3 intentionally backlight output0x800, so old all-input assertion superseded. FinalDUT1boot dut1-20261114T212458Z and gates212601/212602/212603/212604/212605 passed white/Home/guards/RAMsettings/camera→Home restore. Same src/display.rs hash as physical button-tested image. Current source/artifacts app-ui forcorrectMiniPCB; DUT0 still headless observer. Source board unchanged, noSDwrites. Receipt evidence/phase-12-mini-pcb.json; MINI-PCB-IO.md is current pin authority. Background RAMSettings port also passed36hosttests, original numeric/multiselect/update/getter comparisons, real board bounds/atomic native-action rejection and30GC cycles. No persisted settings or device-side effects; source prefix and explicit native policy only. FullController not wired. User now explicitly requests working preview: prioritize persistent sensor/ISP and repeated display updates, not repeated5s captures. Commit checkpoint before streaming work.

## 2026-11-14 — Persistent camera preview on the actual Mini PCB

- Replaced per-preview32-frame captures with a persistent foreground Rust AE/AWB
  session. Initial acquisition/ISP setup happens once; subsequent frames retain
  calibrated control state. Sensor streaming continues while CIF pauses at frame
  boundaries for exclusive RAW/ISP/LCD ownership. Three raw frames per control
  update preserve the existing two-frame settling rule.
- Added MicroPython start/next/stop/status APIs and a frozen cooperative LCD
  preview adapter, with held-button suppression and center/Key3 exit. Stop/error
  paths release the native session. Read-only NV12 views expire on the next fetch.
  Reinit, still capture, duplicate start and settings writes reject while active.
- Headless DUT0 gate captured twelve changing frames, ~825ms startup and
  ~150ms subsequent fetches, returned heap to baseline and passed legacy still
  capture afterward (`usb-20261114T214234.079753Z`). These timings exclude boot.
- Initial DUT1 physical preview rendered90 changing frames at2.74FPS, ~132ms
  acquisition and235ms blit. Its first gate's final heap assertion compared a
  blank native screen with restored Home, so the assertion was corrected to use
  Home on both sides. TX FIFO burst filling reduced blit to~140ms. The corrected
  ninety-frame gate passed at3.77FPS (`usb-20261114T214505.329543Z`).
- USB Ctrl-C initially cleaned up but surfaced OSError and left a pending VM
  interrupt. The final native path consumes that flag after returning safely from
  Rust and raises KeyboardInterrupt in C; a USB test verifies heap/session cleanup
  and executes500 further VM iterations without a second interrupt. No Python
  exception unwinds through Rust.
- RAM-only loads on DUT1; no SD writes, REF changes, CAD edits or rewiring.
  This establishes local continuous preview, not QR decoding, camera entropy,
  full Scan View integration, optical/color calibration or full app readiness.
- Final deployed image: `dut1-20261114T214550Z`. Final90-frame/guard/Home/heap
  gate: `usb-20261114T214622.693828Z`,90frames/23879ms =3.769FPS.
  Optical observer: `usb-20261114T214626.539661Z`; visible local camera scene
  on LCD. Frozen preview adapter:6frames/1648ms and clean timeout/Home restore
  (`usb-20261114T214652.585339Z`). Interrupt evidence:
  `logs/phase-12/preview-interrupt-final.txt`. `baremetal:check`:36tests passed.
  Receipt: `evidence/phase-12-continuous-preview.json`.

## 2026-11-14 — Bare-metal ZXing QR payload decoder

- Read the original plan again. The previous preview stage was concrete hardware
  progress; the full SeedSigner/standalone storage/fast-boot objective remains
  active. The two-minute preview demo exited after294frames/88036ms, consistent
  with its physical center/Key3 exit path, and restored Home.
- Reused the existing Linux decoder source, ZXing-C++3.1.1 commit
  `287c85df6f961c8efbfb5ffd736cd9457b8b890e`, compiled for Cortex-A7 without
  Linux. QR readers only, no writers or non-QR formats. Disposable source edits
  remove the unused Threads link and replace scratch TLS with automatic vectors.
  Cached upstream sources/license stay intact. C++ exceptions return across a
  C ABI before MicroPython raises anything; no NLR through C++ frames.
- Added `qr.decode(packed_luma,width,height)` returning exact raw bytes or None,
  strict640x480/length bounds, no decoded payload logging. Native app builds link
  the decoder; source/toolchain/archive manifest is retained and included in the
  generated firmware manifest. Detailed contract: `qr/README.md`.
- Real wired DUT0 fixture gate passed text, bytes0..127, NUL/high-bit binary,
 90-degree rotation, inversion, blank frame, invalid dimensions/length and ten
  repeat decodes. Small fixture times3–13ms. Immutable ZXing version/Galois-field
  tables added36616native heap bytes at the first decode; subsequent cases and
  repeat decodes stayed flat39696bytes. This is a bounded retained table cost,
  not a claim that the first decode returns to cold heap baseline.
- Optical attempt: rendered public `ss-test-001` on DUT1 LCD; DUT0 tried20 real
  frames. No decode. Each full640x480 attempt took220–261ms. Observer image
  visibly contains the QR but it is small/oblique/blurred; no optical gate passed
  and no re-aim requested. The known-good fixture gate is separate evidence.
  DUT1 Home was restored afterward; no CAD changes, SD writes, REF changes or
  rewiring. Original DecodeQR classification, animated assembly, ScanScreen/View
  integration and wallet flows remain incomplete.
- Exact final headless QR image loaded in `logs/phase-12/20261114T215241Z`;
  fixture gate `usb-20261114T215316.299710Z` passed. Twelve-frame persistent
  preview, heap cleanup and following legacy capture also passed with the QR
  decoder linked (`usb-20261114T215322.984059Z`).36host checks passed.
  Receipt: `evidence/phase-12-native-qr.json`. DUT1 Home restore receipt:
  `usb-20261114T215212.909795Z`.

## 2026-11-14 — Regex/Unicode prerequisites for original Scan parsing

- Read the original plan again and inspected the original ScanScreen._run and
  DecodeQR source. Generic classification depends on counted/noncapturing regex,
  ignore-case matching, groups and fullmatch that the minimal MicroPython build
  does not supply. Enabled proper Unicode strings plus UTF8 validation on native
  app builds and added a bounded PCRE2-backed match/search/fullmatch adapter.
- Pinned PCRE2-10.46 b2bd4254b379b9d7dc9a3dda060a7e27009ccdff, Unicode enabled,
  JIT/OS tests/grep disabled. Preserved upstream cached source and license. The
  disposable source changes two read_repeat_counts int32_t locals to int, matching
  the upstream int-pointer helper on ARM newlib; unmodified10.46 fails GCC14's
  incompatible pointer type check. No pattern engine was replaced with a small
  approximation. PCRE2 is not identical to CPython re outside the tested API.
- C wrapper releases compile/match/context state before Python allocations/NLR.
  Bounds are explicit; Unicode span positions count codepoints. Frozen adapter
  supports the app's current matching/group APIs, not compile/sub/split/findall or
  named-group lookup. Contract and limits: REGEX-UNICODE.md.
- Real DUT0 boot logs/phase-12/20261114T215832Z. CPython-generated original QR
  protocol-pattern and Unicode/bytes/invalid/bounds gate passed at
  usb-20261114T215951.910578Z; heap returned to baseline after every operation.
  QR fixtures215911.779797Z, native UI215923.119160Z and RAM settings gates passed
  with the new Unicode configuration;36host tests passed. Receipt:
  evidence/phase-12-regex-unicode.json.
- New dependencies only on wired headless DUT0. DUT1 remains on working preview
  app-ui/Home. No CAD/REF/SD changes. Full original DecodeQR/ScanScreen/View model
  integration is still next, not established by dependency gates.

## 2026-11-14 — Original DecodeQR model and ScanScreen loop on native camera/LCD

- Read the original plan and inspected the actual source. REF snapshot matches
  the pinned app byte-for-byte for decode_qr.py and scan_screens.py. Prepared all27
  model classes with explicit native image/import boundaries, not a replacement
  classifier. Full class/method/output provenance retained. Status integer values,
  fragment logic and getters remain original; annotation/dataclass/IntEnum runtime
  dependencies are removed explicitly. Missing features propagate FeatureUnavailable
  rather than disappearing into original broad invalid-data handlers.
- Added pinned micropython-lib base64 plus actual MicroPython binascii/hex APIs,
  retaining licenses. Base64 error raises use the real binascii ValueError spelling.
  Enabled native array slice assignment after the first pixel-fixture construction
  exposed CORE_FEATURES' disabled slice stores; bytearray repetition is unsupported,
  so the fixture uses a bytes initializer instead. Both earlier fixture failures
  were recorded before the final hardware gate, not counted as model passes.
- Reused the complete original ScanScreen._run with three reviewed platform
  substitutions: native clock, native input names, cooperative preview metadata
  instead of thread0. A fixed NV12 stream owns start/read/stop; finally releases it
  on completion, Back, exceptions and USB interruption. Visual overlays and the
  original BaseScreen/View/Controller dispatcher remain unfinished.
-44host tests passed, including comparisons to whole original model classes and
  the original Scan loop. Native public QR-pixel/model/loop gates passed on DUT0
  (usb-20261114T220934.155706Z) and DUT1 (final expanded gate
  usb-20261114T221552.594573Z). These include valid/invalid text/fragments,
  SettingsQR, five native pixel decodes, Base64 vectors, explicit missing deps,
  scripted Back and error cleanup. Public descriptor text is not a qualified wallet.
- Real camera/ZXing original scan loop: DUT0 processed7frames and returned camera/
  heap baseline after Ctrl-C (scan-interrupt-20261114T221004.938513Z). DUT1 processed
 19camera/LCD frames in the ten-second test, then restored Home and heap baseline
  (scan-interrupt-20261114T221310.208806Z). Observer image confirms local camera
  pixels on LCD. Full luma export timed out; drained the same live transfer, then
  recovered206missing rows from the retained frame without recapture. All480rows
  validated when assembling original-scan-lcd-optical.png.
- User asked status, then placed a QR in frame. Thirty-frame passes on both boards
  failed; another240-frame DUT1 pass also failed. Saved full-resolution snapshots
  contain the whole printed code; initial clipping diagnosis was wrong and corrected
  to the user. Native and pinned desktop ZXing both fail on this image; desktop
  reports QR detection with Reed-Solomon checksum failure.29crop/sharpen/threshold
  variants did not decode; diagnostic quirc found no symbol. No payload was logged.
  Requested a flatter, front-facing or larger code; no optical QR pass claimed.
- DUT1 boot dut1-20261114T221157Z; current shared artifacts are its app-ui build.
  DUT0 remains headless native-ui boot20261114T220856Z. No CAD/REF/SD changes.
  SCAN-PORT.md distinguishes actual gates from incomplete dependencies, overlays,
  original destination routing, wallet/crypto and standalone app readiness.

## 2026-11-14 — Native hash/HMAC/PBKDF2 prerequisites

- Read the original plan and inspected Seed/QR crypto dependencies. Added a
  no_std hash-core library with exact RustCrypto crate pins, independent streaming
  hash contexts, HMAC and service-aware PBKDF2. The latter retains pinned upstream
  PRF/block/XOR logic, with USB/cancel checks before blocks and every64rounds;
  cancellation clears partial output and never returns it as a key. Preserved
  upstream licenses/source attribution. Cargo manifests record both workspaces.
- Native MicroPython exposes SHA224/256/384/512, SHA1 and RIPEMD160, repeatable
  digest/copy metadata, HMAC, subtle-backed comparison and PBKDF2. Context storage
  is aligned and GC-owned; compile-time size/alignment/no-drop checks and runtime
  alignment checks protect the C boundary. GC finalizers clear stored context;
  reuse after clear rejects. Empty mutable buffers get valid empty Rust slices,
  avoiding null-pointer/zero-length slice UB. No system-wide memory-erasure or
  full wallet/security qualification is claimed.
- Reused pinned micropython-lib HMAC source, adapting inherited allocation, requiring
  digestmod and adding native one-shot/comparison entry points. Host app tests now
  append their package path so native-only hashlib/hmac do not shadow CPython's
  independent reference implementations. Exact supported API/bounds: HASH-PORT.md.
- Three Rust host tests passed, including216 PBKDF2 cases against unmodified pinned
  upstream, cancellation clearing and non-consuming independent copies.44existing
  host checks pass. Native target boot logs/phase-12/20261114T224658Z; public
  CPython/RFC/BIP39 vector gate usb-20261114T224802.460807Z passed all six algorithms,
  block boundaries, streaming/copy/repeat, long/empty keys, multi-block output,
  empty buffers, invalid inputs and context/GC cleanup. SHA1/4096 took23ms;
  BIP39 SHA512/2048 took56ms. These are derivation times, not cold-power/app startup.
- Final one-million-round SHA512 USB interruption gate passed at
  hash-interrupt-20261114T224932.534807Z: caught KeyboardInterrupt,500further VM
  iterations, fresh SHA256 and native heap baseline; host-bound response~0.11s at
 0.1s read resolution. UI regression224951.332648Z and original QR model/scan
  regression225049.291412Z passed on the same final image.
- Only wired headless DUT0 was updated. DUT1 stays on16b2986 app-ui/Home, available
  for the optional optical retry. Shared artifacts now target wired DUT0; do not
  load them on DUT1. No CAD, REF storage or SD changes. Native Seed/embit/UR,
  Unicode NFKD, curves, Controller and SD app integration remain unfinished.

### 2026-11-14 — Unicode15 normalization prerequisite

- Added pinned no_std Unicode15.0.0 normalization, matching read-only REF
  CPython3.12.10, with native normalize/is_normalized APIs and retained licenses.
- Actual DUT0 passed saved REF oracle/API bounds/reordering/heap gates and all
  381480 relations in the official19074-row corpus (6380ms). Separate unlisted
  scalar sweep remains pending after initial host observation timeout; no full
  conformance, mnemonic or wallet readiness claim.44host regressions pass.
- User finished demo; stopped DUT1 camera and restored Home. Continued software
  dependencies without requiring further physical camera holding. RAM-only work.

### 2026-11-14 — Actual embit BIP39 leaf on DUT1

- Froze pinned embit0.8.0 BIP39 and English wordlist with source/license receipt.
  Native DUT1 passed24published English vectors and5Unicode passphrase cases,
  entropy/mnemonic conversion, checksum rejection, candidate search and heap check.
- Native Unicode/hash/UI and original QR/scan regressions passed;44host tests pass.
  BIP39-PORT.md records missing original Seed model/curve/wallet integration.
- Expanded DUT1 loader enumeration observation to40s after successful late USB
  arrival, without another reload. No cold-power timing claim or storage writes.
- Diagnosed identity sweep's chr() interning behavior; corrected its test fixture
  construction and reran on fresh DUT1. Original DUT0 sweep was interrupted with
  state captured and interpreter responsive; pending full sweep result is explicit.

- Unicode identity follow-up: corrected DUT1 sweep231941 completed all4380140
  comparisons across1095035unlisted scalars in83586ms, native heap baseline.
  Combined with published corpus gate, completes supported UTF8 normalization
  conformance coverage. Original chr()-interning test defect documented explicitly.

### 2026-11-14 — Original passphrase codec boundary

- Implemented the original Seed passphrase escape/fallback/NFKD result without
  pretending to supply full codecs/re.sub. Preserves literal/uppercase/adjacent
  escapes and whole-input fallback; rejects surrogate results that cannotencodeUTF8.
- Read-only REF stdlib oracle515public cases;10khost differential cases;47host
  regressions pass. Native DUT1 passed515REF comparisons and32end-to-end actual
  BIP39 derivations, heap check, published BIP39 and original QR/scan regressions.
- FinalDUT1 image60f75644...,RAMload232400,gate232451. Home restored,cameraoff.
  NoSDwrites. OriginalSeed memory-clearing/ownership policy remains real work;
  no fake wipe/curve/model/optical-success claim. Detailed PASSPHRASE-PORT.md.

### 2026-11-14 — Original BIP39 Seed model and actual native clearing

- Retained every original Seed class/method with explicit deferred dependencies,
  REF-tested passphrase boundary and native secure_delete. Actual volatile writes
  are guarded by GC object/data ownership; frozen/qstr/external storage protected.
- NativeDUT1 memorygate232932 passed clearing/alias/frozen-wordlist/neighbor tests.
  Seedgate232943 passed24published vectors,32REF passphrase derivations, changes,
  equality, invalidinput and actualseedbytewipe.48hosttests, QR/scan andpassphrase
  regressions pass. Earlier memorytest incorrectlytreatedREPLbytes asfrozen;
  correctedfixture isactuallyfrozen andprotected. No falseimplementationfailure.
- SEED-PORT.md documents caller-owned/discard-only clearing, aliases/hash caveat,
  skipped sharedstorage and remaining alternate seed/curve/UI/optical work.
  FinalDUT1RAMimageab515da0...,Home restored,cameraoff. NoSD/CADwrites.

### 2026-11-14 — Whole strict framing and numeric SeedQR

- Ported actual embit parsing/model modules and whole original PSBT framing;
  actual original refusal classes retained, not the full PSBTParser policy.
  Missing curve methods/NUMS point initialization explicitly defer to a real
  backend and raise FeatureUnavailable today. No substitute crypto/entropy.
- Native finalimage553bfe12...,RAMload233756 passed15referenceframing cases,
  strictrefusals and v0/v2roundtrips.12-wordnumericSeedQR nowpasses original
  genericclassifier/decoder/Seedvalidation. Noopticalclaim. Initialparserimage
  exposed eagerNUMScurveimport, correctedbylazyactualexpressionwithgatecoverage.
- Seed/memory/originalQR-scan regressions and50hosttests pass; Home restored,
  cameraoff, allreadersfinished. DetailedPSBT-FRAMING-PORT.md andreceipt recorded.
  NoSD/CADwrites. Text/24word/compactambiguity andfullapp/curve flows remain.

### 2026-11-14 — Original mnemonic formats and SLIP39 recovery

- Ported the exact REF-pinned Shamir core/recovery source and whole original Aezeed
  module, preserving licenses and verifying the frozen wordlist against REF.
- Native gate passed 45 published recovery vectors, original classifier/share
  decoding, 26 BIP39 fixtures in three encodings, all five word counts, CRC and
  ambiguity checks. Parameter records are immutable; both wordlists survive wipes.
- Corrected real platform dependencies discovered by hardware tests: dictionary
  delegation, _asdict/_fields, mutation hooks and stale frozen-QSTR invalidation.
  Updated the obsolete three-word missing-dependency fixture to original INVALID.
- Final image89da26d1..., load235301; gate235538 and Seed/memory/PSBT/QR regressions
  pass, plus52host tests. Home restored, preview stopped, no active readers.
  MNEMONIC-PORT.md records remaining UI/optical/curve/entropy/decryption/SD gaps.
  No SD/CAD/REF-storage changes. This does not qualify complete wallet operation.

### 2026-11-15 UTC — Actual secp256k1 and Seed fingerprints

- Found the original result View needs a real root fingerprint. Added actual pinned
  libsecp256k1 v0.7.0, validated portable C bindings and the required embit ABI.
  Preserved source/license; no placeholder point/signature or random-byte fallback.
- Native final gate passed17BIP32paths/16invalidkeys,19BIP340vectors,24Seedroots/
  fingerprints, ECDSA/ECDH/recovery/low-S and malformed/in-place cases. Gate2740ms
  is not boot/UI timing. Context randomization works; entropy qualification pending.
- Final image3e476dbe..., load001212; all Seed/PSBT/mnemonic/memory/QR regressions
  and54host tests pass. Home restored, preview stopped, no active readers.
  SECP-PORT.md and receipt record details. No SD/CAD/REF-storage writes.
