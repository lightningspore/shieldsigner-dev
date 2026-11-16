# Development guide

Run all commands from the repository root. Tasks are defined in the root
`mise.toml` (`mise tasks | grep baremetal` lists all of them). uv manages
every Python environment.

## Toolchain

| Tool | Purpose |
| --- | --- |
| mise | Pins Rust (`armv7a-none-eabi`) and runs tasks |
| uv | Python 3.13 for host tooling and tests |
| `arm-none-eabi` GCC | MicroPython and C components |
| Arm C++/newlib | The LVGL screen library (`mise run baremetal:cxx:setup` downloads a pinned copy) |
| rkdeveloptool | Maskrom USB loading (official build, kept in `.tools/rkdeveloptool/`) |
| Docker | Runs Rockchip's `boot_merger` (linux/amd64) to pack the unmodified DDR blob |

The vendor DDR initialisation comes from the pinned rkbin checkout described in
`stock-loader.json`. It is used unmodified and is never disassembled.

## Everyday loop (bench device DUT1)

```sh
mise run baremetal:check                 # host tests (≈150), no hardware
mise run baremetal:ui:dut1:build         # build the native UI runtime
mise run baremetal:usb:dut1:reset        # running DUT1 -> maskrom (USB only)
uv run --python 3.13 --with pyserial==3.5 python baremetal/tools/usb_only_gate.py
uv run --python 3.13 --with pyserial==3.5 python baremetal/tools/usb_console.py \
    baremetal/micropython/<name>_gate.py --serial rv1103-dut1 --timeout 120
```

`usb_only_gate.py` loads the build into **RAM only**. `usb_console.py` uploads a
script over the CDC console, records raw serial output under `logs/`, and
reports `completed` only when the script reaches its completion marker. Gates
print `@@PASS …` lines.

The MicroPython VM persists between console sessions. A gate that
monkeypatches modules can affect the next one, so reload before a suite.

### Recovery

- `machine.reset(0)` restarts and `machine.reset(1)` reboots into maskrom
  (both are reachable from the app's power menu).
- A hardware watchdog (about 45 s) recovers a hung CPU without manual help.
- CPU exceptions leave a reset record. Read it with `machine.last_reset()` and
  clear it with `machine.clear_reset_record()`. Reason 2 is a host USB reset;
  reason 5 is a CPU exception with DFSR/DFAR/LR. Symbolize the LR against
  `target/armv7a-none-eabi/release/rv1103-bringup` with `arm-none-eabi-objdump`.

## microSD image

```sh
mise run baremetal:app:autostart:dut1:build
mise run baremetal:app:sd:prepare          # -> baremetal/build/app-sd.img + manifest
```

The output is a regular file. Write it to a card with a dedicated flasher such
as balenaEtcher. The tools never write block devices. Copy the image, manifest
and ELF somewhere immutable before you flash a build you intend to keep.

## Porting the SeedSigner app

App sources come from the pinned upstream checkout at
`dist/firmware/sources/lvgl/application`. `firmware/lvgl-app/sources.lock.json`
locks it, and the generators assert the commit.

- `tools/prepare_*.py` read upstream files with `ast` and rewrite only the
  platform boundaries: lazy imports through `decode_platform.dependency`,
  f-strings to `str.format`, removal of OS threads, and native screens. Each
  generator writes the module and a `app/*-provenance.json` receipt that lists
  source hashes and every reviewed change.
- **Never edit a generated module by hand.** Change its generator, rerun it,
  and review the diff.
- Screen arguments map onto the native LVGL builders through
  `seedsigner_port/screen_contracts.py`. These contracts mirror
  `firmware/lvgl-app/python/contracts.py`.
- If a feature has no real provider, it fails with `FeatureUnavailable` or is
  left out of its menu. Do not add placeholder successes.
- Frozen modules are listed in `micropython/manifest.py`.

## Optical test rig

A second monitor shows QR codes, and the device camera reads them through the
real `ScanView`:

```sh
uv run --python 3.13 --with segno --with urtypes --with embit \
    python baremetal/tools/qr_screen.py serve         # control page on 127.0.0.1:8766
uv run -q --python 3.13 --with segno --with urtypes --with embit --with pyserial==3.5 \
    python baremetal/tools/optical_scan_test.py       # address, SeedQR, UR PSBT, base64 PSBT
```

- `qr_screen.py` also serves a demo page in the website style. It has testnet
  seed, address and animated-PSBT presets (`tools/demo_fixtures.py`), plus a
  presentation mode for filming.
- `camera_preview_host.py` streams a live device preview to
  `127.0.0.1:8765`. The page reports a sharpness score, which helps with
  focusing the lens. Stop it with SIGTERM so the device loop receives Ctrl-C.

## Hardware safety rules

1. **RAM-only by default.** Development loads go into RAM over maskrom. Only
   write persistent storage (microSD) to authorized cards, and only with an
   explicit image file.
2. **Leave the reference board alone.** Never write REF's boot partitions.
   REF is the known-good comparison system.
3. **3.3 V logic everywhere.** Never join supply rails between boards, and
   never drive a pin that another board also drives. Check the pinout before
   you move a jumper.
4. **Identify devices explicitly.** USB serial numbers (`rv1103-dut1`) and
   maskrom location IDs select the target. App builds are never loaded onto
   DUT0.
5. **Evidence, not inference.** A gate passes only on hardware. Commit the
   receipts in `evidence/`. Raw logs stay local in `logs/`.

## Licensing

- Original Rust drivers come from register documentation and observation.
  GPL kernel, U-Boot and SDK sources were studied for register layouts, but
  never copied.
- Third-party Python and native components keep their upstream licence files
  next to the code.
