# ShieldSigner bare-metal runtime

The experimental, Linux-free firmware path of [ShieldSigner](../README.md#how-the-pieces-fit).
The current firmware is a Linux (SeedSigner OS) image with an LVGL frontend; see
[firmware status](../docs/FIRMWARE-STATUS.md). This runtime runs the same pinned
application and LVGL screens on the Luckfox Pico Mini (Rockchip RV1103, one Cortex-A7,
64 MB in-package DDR2), but on MicroPython instead of Linux. The
Rust base boots directly from the ROM loader, drives the SC3336 camera, ISP and
3A, the bench LCD and buttons, and a USB CDC console. The SeedSigner app is the
pinned upstream Python source, ported to MicroPython by reviewed generators
rather than hand-copied.

> **Status: development build. Not for real funds.** The firmware has not had
> an independent security review, and the device has no hardware random number
> generator driver. Use public test seeds only. See [docs/status.md](docs/status.md).

## What works today

Verified on the bench device (DUT1: Pico Mini, 240×240 SPI LCD, five-way joystick plus three keys,
SC3336 camera), using gates that drive the real UI and check results against
host-computed oracles:

- **Boot**: standalone microSD boot straight into the app; RAM loading over
  USB maskrom for development.
- **Navigation**: main menu, Seeds, Tools, Settings, power/restart/flash-mode routes.
- **Camera and scanning**: live preview; static and animated (UR) QR codes read
  off a monitor through the original `ScanView`, including SeedQR, addresses
  and multi-part PSBTs.
- **Seeds**: camera and dice entropy, 12/24-word generation, final-word
  calculation, word backup and verification, SeedQR transcription, passphrases.
- **Bitcoin workflows**: xpub export, address explorer, address verification,
  PSBT review, signing and animated QR export.
- **Tools**: Text QR Code (encode/decode) and Password Generator (dice and
  BIP85 sources).

Not included: smartcards (by decision), SLIP39 seed *creation* (needs an RNG),
settings persistence and file-based backups (no filesystem service), and
anything needing a wall clock. The full matrix is in [docs/status.md](docs/status.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/` | Rust `no_std` runtime: boot, MMU/caches, UART, GPIO, I²C, SPI, USB (DWC3 CDC), camera receiver, ISP and 3A glue, LCD, watchdog, reset records. |
| `micropython/` | MicroPython port (C), frozen-module manifest, and on-device gate scripts (`*_gate.py`). |
| `app/` | Frozen Python: `seedsigner_port/` (generated and reviewed app modules), pinned third-party libraries (embit, shamir-mnemonic, qrcode, UR2, urtypes), provenance receipts (`*-provenance.json`) and licences. |
| `ui/` | Build glue for the upstream SeedSigner LVGL screen library. |
| `hash-core/`, `secp/`, `qr/`, `unicode/` | Native crypto, QR decoding and Unicode components with their upstream notices. |
| `tools/` | Host tooling: builders, `prepare_*.py` source-port generators, gate runners, USB console, image packaging, optical scan rig. |
| `tests/` | Host test suite (`mise run baremetal:check`). |
| `evidence/` | Committed JSON receipts from passed hardware gates. |
| `docs/` | Documentation; start at [docs/README.md](docs/README.md). |

Local, ignored: `logs/` (raw gate logs), `build/`, `target/`, `.tools/`
(toolchains and vendor checkouts), `ref-dumps/`.

## Quick start

Requirements: macOS or Linux, [mise](https://mise.jdx.dev), [uv](https://docs.astral.sh/uv/),
Docker (for the vendor `boot_merger`), and a Pico Mini reachable in maskrom over USB.
All commands run from the repository root.

```sh
mise run baremetal:check                 # host tests; touches no hardware
mise run baremetal:ui:dut1:build         # build the app runtime for the bench device
mise run baremetal:usb:dut1:reset        # put a running DUT1 back into maskrom
uv run --python 3.13 --with pyserial==3.5 python baremetal/tools/usb_only_gate.py
                                         # load the build into RAM (nothing is written to storage)
uv run --python 3.13 --with pyserial==3.5 python baremetal/tools/usb_console.py \
    baremetal/micropython/view_flow_gate.py --serial rv1103-dut1 --timeout 120
                                         # run an on-device gate over the USB console
```

To produce a microSD image (a regular file; nothing is flashed):

```sh
mise run baremetal:app:autostart:dut1:build
mise run baremetal:app:sd:prepare        # -> baremetal/build/app-sd.img (~4 MiB)
```

See [docs/development.md](docs/development.md) for the full workflow, gate
catalogue, hardware safety rules and the optical test rig.

## Design principles

- **Upstream code, not rewrites.** App behaviour comes from the pinned SeedSigner
  source. `tools/prepare_*.py` port it mechanically and record every reviewed
  change in a provenance receipt. Generated files are not edited by hand.
- **No placeholder success.** Features without a real provider fail explicitly
  or are omitted from menus. Nothing fakes randomness, time or storage.
- **Hardware evidence.** A feature counts as working only when a gate passes on
  the device. Compilation and host tests are prerequisites, not proof.
- **Licensing.** Original Rust drivers are written from register documentation;
  GPL kernel sources were studied, not copied. Rockchip DDR/loader blobs are
  used unmodified. Third-party licences are kept beside the code they cover.

## Licence

Project code is MIT. Bundled components keep their own licences (see the
`LICENSE.*`, `COPYING` and `COPYRIGHT` files in `app/`, `secp/`, `unicode/`
and `hash-core/`).
