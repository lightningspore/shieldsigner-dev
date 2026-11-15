# Phase10 standalone boot work

Status: the runtime now boots from the user-provided4GB microSD, with unchanged
vendor DDR followed directly by our code. Controlled SD resets and the complete
peripheral/camera/GC gate passed. The5Hz LED test also passed during camera work.
Cold power-edge timing, power-on-to-first-frame and app readiness remain open.
Receipt: [evidence/phase-10-sd-boot.json](evidence/phase-10-sd-boot.json).

## User-visible timing requirement

The primary product measurement is **power-on to a usable SeedSigner app**:
its main screen is drawn and button input works. Camera readiness is a separate
power-on-to-usable-camera-frame measurement through the actual app workflow.
The user reports that the current boot/app path takes at least about30seconds.
That is a user-observed baseline, not an instrumented measurement made here.

The13.1ms internal result below is **not app boot time** and cannot establish a
speedup against that baseline. It starts after ROM/DDR/loading at our payload
entry and ends at initialized MicroPython, with no SeedSigner app loaded. Keep
this number secondary in progress reports. Whole-system REPL timing from the
original Phase10 gate also remains required, independently of usable-app timing.

| Measurement | Current evidence |
| --- | --- |
| Current boot to running app | User reports at least about30s; exact start/end not instrumented |
| Replacement power-on to usable app | Not implemented or measured |
| Replacement power-on to REPL | Cold power-on not measured; SD warm reset to REPL marker about195ms |
| Replacement power-on to usable app camera frame | Not implemented or measured |
| Payload entry to initialized MicroPython | About13.1ms, measured on DUT and independently polled by REF; excludes earlier boot stages and app |

Record power/reset, first payload execution, initialized interpreter, first
accepted REPL command, app screen/input readiness and usable camera frame as
separate events. Do not label interpreter initialization as application readiness.

## Artifacts and commands

- `mise run baremetal:boot:build`: `fast-boot` feature, normal runtime APIs,
  MMU/caches, reclaiming heap and IRQ setup, without cache/allocator benchmarks or
  the deliberate one-second timer test. Diagnostic builds retain those tests.
- `mise run baremetal:boot:sd:prepare`: writes only regular files under `build/`
  and the ignored rkbin workspace. It has no block-device writing capability.
- `build/runtime-sd.img`: 2MiB raw experimental image. Header starts at sector64
  (32768bytes). No filesystem/partition table or SeedSigner assets yet.
- `build/runtime-idblock.img`: ROM header plus unchanged vendor DDR and our
  runtime as FlashBoot, not the USB download stage or U-Boot.
- `build/runtime-sd-manifest.json`: stage sizes and hashes, image checksum,
  source-manifest checksum and explicit unverified assumptions.

This is a raw disk image, not a file to copy onto an ordinary FAT-formatted card.
The candidate currently has856064bytes of ID block (including an831188-byte
runtime). Unlike the SDK layout it does not reserve a512KiB partition and place
U-Boot afterward. The ROM accepted this second stage on the real DUT and booted it successfully.
This proves this image size/profile, not an unrestricted ROM maximum.

The packager retains NEWIDB, SHA256 header/stage hashes and untouched DDR. It
validates both stage extents, ordering, input identities, padding and hashes.
Tests reject corruption, truncation, overlapping extents and stage substitution.
A rebuild produced the same payload and SD image bytes.

## Hardware evidence so far

`logs/phase-10/20261114T173336Z/` records a successful fast-start RAM boot.
The on-chip24MHz timer measured13153microseconds from payload entry to completed
MicroPython initialization. `logs/phase-9/console-20261114T173414Z/` records the
full eight-marker API/camera/GC gate passing on that payload. Rebuilding after
removing unused diagnostic-only definitions kept payload SHA256
`b503c56ec2168bc011f1fd2da7844ff9813b4c037f1a080157e604944849da43`.

GPIO1_C4 (blue wire) is high near `_start`, then low after `mp_init`; REF C4 must
remain input. Orange C5 remains input on DUT. This measures payload startup,
excluding ROM/card discovery and vendor DDR initialization. No claim of a
13ms power-on boot is made. The candidate currently reaches an idle REPL; first
camera acquisition is requested through that REPL and is not auto-started.

## Current card state and recovery

The user authorized the spare4GB card write. Direct privileged helpers were
blocked by macOS privacy before writing. Installed balenaEtcher completed the
write; after a later helper error, restarting Etcher and reselecting the card
successfully wrote the final5Hz image. The user moved it to DUT and powered it.
No independent host raw-byte readback was obtained before the move; do not
claim one. Actual controlled boot and full API tests subsequently passed.

Keep REF's original Linux card untouched. To use RAM-only USB downloads again,
power DUT off, remove its spare card, then power DUT on into maskrom. With the
card installed, Ctrl-] resets into the SD runtime instead of maskrom. Use
`mise run baremetal:boot:sd:gate` for an already-running SD REPL; this issues no
USB download or storage command. The card is a raw ROM image with no app
filesystem yet, so Finder cannot display app files on it.

Next measurement gap: cold power application was not timestamped externally.
The captured warm-reset request to REPL marker was195140.75us on the final
image. REF polling/UART buffering bounds its precision; it is not a cold boot
or usable SeedSigner app benchmark. Original Phase10 power-on/first-frame
measurement requirements and the app milestone remain open.

## Source provenance

Format facts were studied in Luckfox SDK revision
`0b5c1f30ca6333b7ec5af70d26511da9ef8d39af`, under
`sysdrv/source/uboot/u-boot/tools/rkcommon.c` (`header0_info_v2`) and
`scripts/spl.sh` (NEWIDB stage substitution), plus
`include/configs/rv1106_common.h` (SPL entry0 and stack4MiB). These GPL sources
are reference material; the local packager and runtime code are original MIT.
The existing pinned rkbin packager and DDR are used unchanged. Luckfox documents
its normal32KiB SD ID-block offset in its
[partition guide](https://wiki.luckfox.com/Luckfox-Pico-RV1106/Linux-Base/).

Independent REF observation `gpio-20261114T173649Z` measured13094.375us
against DUT13112us. The largest polling gap within that high pulse was130083ns;
this is polled Linux observation, not logic-analyzer qualification. A prior run
was conservatively rejected by a whole-capture gap threshold despite agreeing
edges; the observer now separately reports the gap within each measured pulse
and retains the global gap too. The receipt is
[evidence/phase-10-preparation.json](evidence/phase-10-preparation.json).

## Camera acquisition timing, separate from boot and live FPS

Three actual requests at `console-20261114T174525Z` measured initial processed
DMA output at702300/765364/710672us and complete32-frame acquisition at
5320135/5377477/5326094us. A separate `camera.init()` call took21ms. Python's
enclosing capture timer agreed within1ms. Initial output requires frame/output
IRQs, clear MI error status and changed DMA; the complete API result still
requires the existing full3A loop and final output validation. A missing initial
completion now returns failure instead of continuing on a timeout.

These are per-request camera timings on the RAM-loaded runtime, not power-on,
app startup, or steady-state streaming FPS. The user reports10+FPS under Linux:
Linux keeps the camera/ISP/3A running, whereas this bring-up capture reinitializes
and performs a32-frame batch each call. User clarified this was a comparison
question, not a request to rewrite the pipeline immediately. Preserve the
current bounded path for bring-up; introduce and qualify persistent streaming
when needed for the actual app preview. Do not reduce the batch merely to make
a timing number smaller.

The added `camera.timings()` API exposes the last request's stage measurements.
No streaming behavior, GPIO ownership, or 3A algorithm was changed. The complete
eight-marker runtime regression also passed at `console-20261114T174614Z`.
Latest experimental SD candidate includes this instrumentation; startup evidence
above and `phase-10-preparation.json` refer to the earlier candidate. Latest
hashes and limits are in
[evidence/phase-10-camera-timing.json](evidence/phase-10-camera-timing.json).

## Visible heartbeat test

The user requested a fast blink, then half the original10Hz rate. Final build
uses5Hz:100ms on,100ms off, from the1kHz generic-timer interrupt. Only the
onboard active-high GPIO3_C6 LED is configured; its mux/clock facts come from
Luckfox Mini DTS and pinned RV1106 pinctrl/clock definitions. No SD A-pin mux
is changed. `machine.led_status()` reports enabled/state/rate, transition count
and real pad-readback errors. `mise run baremetal:led:gate` verifies10 transitions
per second and both states. While the full API script ran two camera captures,
108 transitions occurred in10801ms with zero pad errors. This is a diagnostic
heartbeat, not an application watchdog.

## Native UI app SD candidate (2026-11-15 UTC)

`mise run baremetal:app:sd:prepare` packages the current DUT1 `app-autostart`
payload as `build/app-sd.img`. It validates the exact payload manifest/hash and
DUT1 USB identity, preserves unchanged DDR and independently checks both NEWIDB
stage extents/hashes. The image reservation rounds up to whole MiB above the
historical2MiB minimum, so the2917320-byte frozen native app fits in a3MiB image.
The original runtime profile/filenames remain available.107host tests pass.

Current candidate is saved under
`logs/phase-12/app-sd-20261115T045650Z/seedsigner-app-sd.img`, SHA256
`19a7fc3acbd7b0123a711eb815b3d0f31f0485d0b249329ffe25eb0998e04098`.
User requested a quick test and inserted the spare4GB card, identified as external
USB `/dev/disk7`,4025483264bytes. Etcher selected this exact image/card; write was
started and is waiting for macOS administrator authentication. No successful
write/readback or ROM boot is claimed at this checkpoint. The larger native
second stage is not yet hardware SD-boot qualified. Frozen app/assets require no
FAT filesystem; the missing-partition-table notice is expected for this raw ROM
layout. Current image includes the in-progress address-search prototype; expanded/
continuation search gates remain incomplete. This is a development quick test.

Follow-up: Etcher's helper failed and was canceled. Raspberry Pi Imager wrote the
selected card; its final verification dialog was not observed, so no independent
byte-for-byte readback is claimed. User moved the card to DUT1 and explicitly
confirmed it works and starts FAST. The native2.9MB stage/app SD quick test now
has user hardware confirmation. Exact power-to-app/REPL/frame timings and the
unrestricted ROM maximum remain unqualified. Receipt:
[evidence/phase-12-app-sd-quick-test.json](evidence/phase-12-app-sd-quick-test.json).
