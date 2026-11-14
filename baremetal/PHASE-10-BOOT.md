# Phase10 standalone boot work

Status: fast-start payload passed the complete Phase9 hardware API script after
RAM download. Experimental microSD image prepared and validated on host; no card
written and no standalone boot or power-on timing gate passed yet.

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
| Replacement power-on to REPL | Not measured; standalone SD boot untested |
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
The candidate currently has854016bytes of ID block (including an829040-byte
runtime). Unlike the SDK layout it does not reserve a512KiB partition and place
U-Boot afterward. The ROM's acceptance of this larger second stage still needs
an actual SD boot. If rejected, investigate the documented format/ROM load limits
and an original minimal loading path; do not silently insert U-Boot.

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

## Next hardware step

The original mission requires user approval before writing or inserting a DUT
card. Use a spare card in a host reader, identify its physical device and size,
confirm it is the authorized target, write the prepared image and read it back.
Never use REF's Linux card. Keep REF powered and its UART bridge connected;
power DUT off before inserting the verified spare card. Capture UART and REF
GPIO timing before powering DUT. Verify REPL APIs and camera, then report both
whole boot and payload-only timing with the actual measurement boundaries.
First-frame timing and cold power-on measurement remain open.

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
