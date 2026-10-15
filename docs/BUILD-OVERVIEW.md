# ShieldSigner Luckfox Pico Mini build overview

> For the **current 0.0.4-dev eight-pin pill**, use the [pill design](LCD-MODULE-VARIANT.md) and [assembly guide](MODULAR-ASSEMBLY.md). The overview below describes the earlier standard FPC configuration; its dated store prices/bundles are an archived sourcing snapshot, not a quote for the pill build.
Checked 11 October 2026

Recommended configuration

For a compact build, use Luckfox Pico Mini with the integrated SeedSigner-Plus Smartcard Pico carrier. It combines the display, buttons and SEC1210 reader. Alternatives use a Mini/Max adaptor with separate Raspberry Pi-style hats, or a Pico Pi. These are distinct hardware configurations; match the carrier and firmware to the model.
Source: https://3rditeration.github.io/seedsigner/hardware.html

Shopping checklist

- Luckfox Pico Mini, with its boot/storage variant identified.
- Integrated ShieldSigner Plus smartcard carrier, including the 2.8-inch screen.
- Low-profile SC3336 camera and matching ribbon.
- Case matching carrier revision and soldered/socketed mounting.
- Blank J3H145 JavaCard.
- microSD card, USB power cable, mounting hardware and insulation.

The store category currently lists carrier/display at $36–38, Mini variants at $5–22, camera at $13 and case at $15: $69–88 combined before card, microSD, mounting materials, shipping and tax. The Mini range spans options; confirm the selected listing before buying. Product detail pages did not load during this check, so stock and exact bundle contents remain to be confirmed.
Sources:
https://3rditeration.github.io/seedsigner/shopping_list.html
https://cryptoguide.tips/product-category/luckfox-pico/

Mechanical assembly

The carrier accepts a directly soldered Pico or an 11-pin female header made from a shortened 12-pin strip. Mount microSD side up, USB-C toward the board edge. Insulate protruding pins beneath the LCD to prevent a 3.3V-to-ground short. Attach the camera directly to the Pico. Use the specified ST7789 2.8-inch SPI/FPC screen, not an arbitrary same-size display. Leave configuration jumpers at defaults; never bridge both alternatives of a pair.

The PCB folder includes KiCad sources plus Gerbers, BOM and placement files for fabrication. Buying an assembled carrier avoids assembling its surface-mount components yourself.
Source: https://github.com/3rdIteration/seedsigner/blob/dev/electronics/SeedSigner-Plus-smartcard-luckfoxpicozero/readme.md

Use the corresponding soldered or pin-header case body and microSD cover. Faceplates differ between carrier v1.0.0 and v1.0.1. The case requires a low-profile camera; the larger module will not fit. Camera mounting uses two M2 screws, 6–8 mm long; confirm other fasteners against the selected case instructions.
Source: https://github.com/3rdIteration/seedsigner/blob/dev/enclosures/luckfox_pico/plus-hat-smartcard-pico-zero/readme.md

Firmware and first boot

B13 is the current release checked here. For a Mini microSD build, the published asset is:
seedsigner-luckfox-pico-mini-sd-SeSi-0.8.7_ShSi-B13-osproduction-signed-devkey.img

A separate Mini NAND archive is available. Max and Pi images target different boards. Start with the Mini SD image for a compatible SD-boot build; verify it using the release instructions, then flash the image to the microSD. NAND installation instead uses the Rockchip flashing procedure and its separate files.
Release: https://github.com/3rdIteration/seedsigner/releases/tag/SeSi-0.8.7%2BShSi-B13
Flashing: https://3rditeration.github.io/seedsigner/quickstarts/10-flash-microsd.html

Production and development builds differ. The smartcard controller shares a UART with the serial console, which the current builds strip by default. Re-enabling that console conflicts with the reader. The Mini uses RV1103 according to the OS hardware table; the carrier README's RV1106 description appears inconsistent.
Source: https://3rditeration.github.io/seedsigner/os/luckfox/README.html

Secure boot

The published image name explicitly says signed-devkey. A published development signing key does not establish exclusive trusted authorship. The device can show a yellow verification status for development keys and an orange indication that secure boot is not enabled. Verify signer identity and reproducibility separately.
Source: https://3rditeration.github.io/seedsigner/os/luckfox/verifying-a-release.html

Hardware-enforced secure boot requires provisioning the intended key into OTP/eFuses. That is irreversible and can leave the board unable to boot if misconfigured. For initial assembly, stay with an unarmed image; treat fuse provisioning as a separate project after verifying boot and recovery with the intended keys.
Source: https://3rditeration.github.io/seedsigner/os/luckfox/secure-boot.html

Functional checks

Check screen, buttons and camera; then verify reader and blank-card detection. Install SeedKeeper through Tools > Smartcard Tools > DIY Tools > Install Applet. The current guide recommends SeedKeeper-0.2-official.cap and the default 8 KB storage. Set a PIN, check Card Info, and test saving/loading a disposable seed and QR signing before loading a funded wallet.
Source: https://3rditeration.github.io/seedsigner/quickstarts/01-install-applets-diy-javacard.html

Before ordering

Confirm Mini storage variant, carrier revision, whether the screen and headers are included, camera/ribbon compatibility, and matching enclosure parts. Decide whether you want an assembled carrier or to fabricate the PCB using its BOM and placement files.


This summary cites public upstream documentation and supplier pages. It contains no Telegram messages. For this carrier variant, the selected reader is SEC1210/PV-UR2; use [SMARTCARDS.md](SMARTCARDS.md) and [BRINGUP.md](BRINGUP.md) for current wiring/configuration and qualification status.
