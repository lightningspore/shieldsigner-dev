# Build tips: isolate faults before changing parts

Start with the current [eight-pin pill assembly guide](MODULAR-ASSEMBLY.md). These checks turn common failure categories into a repeatable diagnosis process. They are engineering checks to perform; they do not add physical test results to our prototype's record.

## Keep a compatibility record

Record the exact carrier revision, processor model, display controller/interface/resolution, camera module, reader variant, card applet/version, and installed OS/application commits. “SeedSigner compatible” leaves too much unspecified.

Our current carrier targets Luckfox Mini, the specified HOTHMI eight-pin ST7789 module in landscape 320×240, and SEC1210/PV-UR2. Raspberry Pi GPIO numbers, DPI display overlays and Pico-shaped LCD pinouts belong to different configurations. See [LCD pinout](LCD-MODULE-VARIANT.md) and [upstream platform profiles](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/hardware_platform_support.md).

## Check mating signals, not equal pin numbers

The LCD header numbers run in opposite directions on carrier and module. **Carrier 1/BL mates with module 8/BL_E; carrier 8/3V3 mates with module 1/VCC.** Match all eight signal names before powering it. Inspect the module from the mating side and support it mechanically; the header is not the only mount.

Power down before fitting or reseating modules and camera cables. Use staged power checks and the specified supply arrangement. The [assembly guide](MODULAR-ASSEMBLY.md) contains rail checks and mounting details; the [electrical review](ELECTRICAL-REVIEW.md) lists pending measurements.

## Separate three camera problems

| Observation | Next check |
|---|---|
| No live frames | Module identity, profile, power and connector orientation/seating |
| Frames appear but are blurry | Focus and realistic working distance for that exact camera |
| Sharp image but no decode | Expected QR format, complete animation, lighting and display glare |

Use a non-secret test QR first. Record distance and lighting so a change can be repeated. Do not adjust a glued or fixed lens based on instructions for another camera. Different connector fit does not establish electrical or driver compatibility. The [QR format reference](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/qr_formats.md) explains supported payloads; the [enclosure guide](ENCLOSURE.md) distinguishes camera envelopes from proven physical fit.

## Treat the reader as four checkpoints

1. **Reader enumerates:** PC/SC can reach the UART/CCID reader stack.
2. **Insertion detected:** the socket switch changes state.
3. **Card activates:** communication produces an ATR.
4. **Applet works:** the expected SeedKeeper/Satochip/backend operation succeeds.

A success at one checkpoint does not prove the next. Insertion detection alone does not verify contact orientation or solder joints; an ATR does not identify a supported wallet applet. Preserve card contents while diagnosing. Our [smartcard guide](SMARTCARDS.md) documents the switch, contact map, UART2 configuration and applet distinction; follow the [staged bring-up](BRINGUP.md) for measurements.

## Change one variable and keep evidence

Write down symptom, exact configuration, expected result, one change, observed result and whether the change was reverted. Include error text and supply readings where useful; omit seeds, PINs, passphrases and seed QR images.

A successful camera reseat is not evidence of a firmware fix. A correct setting is not evidence of correct wiring. Re-test with the case assembled after bench checks because cable routing, support and optical clearance can change. Add physical observations to the [test record](BRINGUP-RESULTS.md), keeping unrun checks visibly pending.

Reviewed 2026-10-17 against the linked project engineering documents and pinned upstream profile/format documentation.
