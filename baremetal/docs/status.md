# Status

Last updated 2026-11-15. This page is the current capability summary. The
[journal](journal/) holds the detailed chronological record.

**This is a development build. Do not use it with real funds.** It has had no
independent security review, and the runtime has no hardware RNG driver.
Every recorded test uses public test seeds (for example `abandon ×11 about`,
fingerprint `73c5da0a`).

## Hardware platform

| Device | Role |
| --- | --- |
| **DUT1**: Luckfox Pico Mini A on the Mini PCB | Primary target: 240×240 SPI LCD, five-way joystick, three keys, SC3336 camera, USB-only console. Boots from microSD or loads into RAM through maskrom. |
| **DUT0**: Pico Mini A | Headless/UART development target for early phases and native-library gates. |
| **REF**: Luckfox Pico running Linux | Reference camera system and UART bridge for bring-up (phases 0–10). |

Bring-up phases 0–12 (CPU, GPIO, I²C, SPI, camera, ISP/3A, MicroPython,
standalone boot, USB console and app I/O) are complete. Their receipts are in
[`evidence/`](../evidence/) and are summarized in [bringup/](bringup/).

## Application capability

Each **Verified** row has an on-device gate (`micropython/<name>_gate.py`)
that drives the real native screens and checks the results against
host-computed oracles.

| Area | State | Device evidence |
| --- | --- | --- |
| Boot to app (microSD) | Verified by the operator. Cold-boot timing is not measured. | `app_autostart_gate`, [phase-12-app-sd-quick-test](../evidence/phase-12-app-sd-quick-test.json) |
| Menus and navigation | Verified | `view_flow_gate`, `navigation_gate`, `ui_registry_gate` |
| Power, restart, flash mode | Verified | `power_routes_gate` |
| Camera preview and entropy | Verified on synthetic and live frames | `camera_entropy_core_gate`, `camera_entropy_flow_gate`, `preview_lcd_gate` |
| Dice entropy and final-word calculation | Verified | `camera_entropy_flow_gate`, `calc_final_word_gate` |
| Seed words, backup test, SeedQR | Verified | `backup_words_gate`, `seedqr_flow_gate`, `seedqr_confirm_gate` |
| Mnemonic entry and passphrase | Verified | `mnemonic_entry_gate`, `passphrase_flow_gate` |
| QR scanning (optical) | Verified end to end through `ScanView` and the live camera: address 1.4 s, SeedQR 1.7 s, a 440-character static PSBT 1.5 s, and a 6-part animated UR PSBT about 10 s | `optical_scan_gate` with `tools/optical_scan_test.py` |
| Xpub export | Verified | `xpub_flow_gate` |
| Address explorer and verification | Verified | `address_explorer_gate`, `address_flow_gate`, `address_search_gate` |
| PSBT review, signing, animated export | Verified on public fixtures | `psbt_review_gate`, `psbt_flow_gate`, `animated_qr_gate`, `ur_core_gate` |
| Settings (in RAM) | Verified | `settings_store_gate`, `settings_schema_gate` |
| Tools: Text QR Code | Verified, including camera decode | `tools_extra_gate` |
| Tools: Password Generator | Verified for dice and BIP85 sources against upstream oracles | `tools_extra_gate`, `tools/tools_extra_oracle.py` |
| Crypto primitives | Verified against public vectors | `hash_gate`, `secp_gate`, `bip39_gate`, `unicode_gate` |

## Not available, by design

| Feature | Reason |
| --- | --- |
| Smartcards (Satochip, Seedkeeper, Keycard, SmartPGP) | Out of scope for this port. The PCB connector is kept. |
| SLIP39 seed creation | Share generation needs random bytes and there is no RNG driver. Importing SLIP39 shares is unaffected. |
| "System RNG" password source | Shows the original "System RNG monitor unavailable" warning. |
| Settings persistence, file-based backups | No filesystem service. Settings are kept in RAM only. |
| Wall-clock features (e.g. timestamp locktimes) | No real-time clock. Uptime is never used in place of wall time. |
| Linux-only Tools entries (microSD tools, battery, network, build tools, GPG) | No equivalent platform service. |

## Known issues

- **Intermittent LVGL data abort.** A CPU alignment fault in
  `lv_obj_get_ext_draw_size` (corrupted object pointer). It has been seen three
  times, each right after a host preview session was stopped and a scan screen
  started. It has not been reproduced in isolation. The reset record and
  watchdog make recovery hands-free. See the
  [2026-11-15 journal](journal/2026-11-15-handoff.md).
- **Optical margin.** At full-monitor distance the lens corners are soft. The
  optical suite shows codes at 75% of screen height, and the lens must be
  focused for dense static codes.
- **Cold-boot timing** to a usable UI has not been measured with external
  instrumentation.

## Next steps

1. Find the root cause of the LVGL data abort with a deliberate
   interrupt-during-scan gate.
2. Port `SeedEncryptedQRnonECBModeView`.
3. Speed up animated UR scanning by tuning fps and part size against the
   device decode loop.
4. Measure cold power-on to a usable UI.
5. Commission an independent security review before any real-funds use.
