# Troubleshooting: find the failing layer

Start with an unfunded test wallet and record the firmware revision and hardware variant. Preserve existing backups and card contents while diagnosing a fault. The current pill and earlier FPC carrier have different assembly details.

| Symptom | Check first | Next reference |
|---|---|---|
| No boot | Stable power, correct Luckfox model/boot medium, intended image and checksum | [Flash workflow](/build/flash/), [OS build](OS-BUILD.md) |
| Backlight but no useful image | Eight-pin module wiring, 3.3 V logic, correct ST7789 320×240 profile and orientation | [LCD module pinout](LCD-MODULE-VARIANT.md) |
| Buttons do the wrong thing | Runtime board/profile mapping; Pi GPIO numbers are not Luckfox pin numbers | [Hardware architecture](HARDWARE.md), [platform profiles](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/hardware_platform_support.md) |
| Camera missing | Exact supported camera/module, connector orientation and profile; power down before reseating | [Modular assembly](MODULAR-ASSEMBLY.md) |
| No smartcard reader | UR2 image/configuration, UART2 ownership, pcscd and serial CCID configuration | [Reader stack](SMARTCARDS.md), [bring-up](BRINGUP.md) |
| Reader exists, card absent | Insertion switch, full-size card orientation, socket contacts and card power | [Smartcard contact map](SMARTCARDS.md) |
| Card has ATR, wallet action fails | Compatible applet and enabled backend; ATR only proves initial card communication | [Card compatibility](SMARTCARDS.md) |
| Expected menu is absent | Feature setting, application revision and packaged dependencies | [Software features](SOFTWARE-FEATURES.md) |
| QR will not scan | Correct QR data type/format, lighting, focus and complete animated sequence | [Upstream QR formats](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/qr_formats.md) |
| Wrong wallet/address | Passphrase, network, script, account and loaded multisig descriptor | [Backup concepts](WALLET-BACKUPS.md) |
| Satochip signing is slow | Card-specific timeout and documented protective dummy-request behavior | [Satochip guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/satochip.md) |

## Identify the installed software

On a development device with an existing console, this read-only command reports image provenance:

```sh
cat /etc/seedsigner-os-release
```

Compare the application and OS commits to the [documented build](OS-BUILD.md). An upstream screenshot or a newer README does not establish what your image contains. Avoid adding network/debug access to a device holding a real seed just to obtain diagnostics.

## Separate card transport from card application

The chain is application → PC/SC → serial CCID driver → UART2 → SEC1210 UR2 → socket → applet. Test it in that order. A missing reader is a different problem from a detected reader with no card, and both differ from an unsupported applet. Only SC1 is physically connected on our carrier; SC2 capability is not a second socket.

Do not reset a populated card to diagnose transport. Capture the error, card/app version and firmware revision without sharing PINs, seed words, seed QR images or wallet secrets. The [bring-up guide](BRINGUP.md) contains the staged electrical and reader checks; [test results](BRINGUP-RESULTS.md) distinguishes completed checks from pending physical measurements.

## Display settings belong to the actual module

The fork documents **Settings → Hardware → Display type**. Our eight-pin 2.8-inch module uses ST7789 at landscape 320×240; ordinary SeedSigner Pi display instructions commonly describe 240×240 hardware. Selecting a profile cannot repair swapped power pins or an incompatible module. Source: [platform support](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/hardware_platform_support.md).
