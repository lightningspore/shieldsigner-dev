# Display and buttons: 0.0.12-dev electrical review

The current target is the native **eight-pin HOTHMI pill carrier**. The local
source, netlist and compiled-input checks below pass. No assembled carrier has
been powered or physically qualified by this review. The deliverable supports
ordering and preparing first articles; measurements follow their delivery.

## Current files

- [Native KiCad project](../kicad/SeedSigner-Plus-smartcard-pico.kicad_pro)
- [Datasheets: all 18 factory BOM SKUs, modules and retained references](../datasheets/README.md)
- [Current build-input preparation record](../hardware/carrier-build-preparation.json)
- [Factory sourcing and first-article order review](PCB-ORDER-READINESS.md)

The PCB hash in the electrical reports must match the selected native board.
The main reference uses four layers, nine factory Keystone points and four
additional M2.5 holes. The standard 40-pin FPC board, PWM candidate and existing
bench display/button assembly are separate designs.

## Display: wiring and initialization

Use **HOTHMI HTM-TFT028A16-SPI, no touch, J1 2.54 mm row**. Carrier J701 numbering
runs opposite to the vendor header: match VCC/GND and every signal before mating.
[The compatibility guide](PCB-SOFTWARE-COMPATIBILITY.md) gives the complete table.
The display receives its own nominal 3.3 V from U701, not the host regulator.
JP201 enables the backlight from host 3.3 V; it is a logic input, not its current
supply. Preserve closed JP201/JP203/JP205 and open JP202/JP204/JP206.

The image needs carrier FOX_22 GPIOs, kernel-managed SPI0 CS0, **10 MHz** and
`display_config: st7789_320x240`. Reset uses GPIO1_C3, so SPI MISO must remain
unclaimed. The tested base-fork bench image assigns LCD outputs to two carrier
button nets and must not be used unchanged.

The generic square-panel initializer differs from HOTHMI's recommended program.
The explicit `hothmi_htm_tft028a16_spi` profile now follows manufacturer
Rev 0-0 pages 17–19: RAM control, VCOM/drive, gamma, landscape MADCTL `0xA0` and
pixel format `0x55`. Its 19 commands and 54 data bytes match the independent
manufacturer fixture. Reset retains the pinned driver's conservative
10/10/150 ms sequence; Sleep Out is followed by 150 ms and Display On by 20 ms.
It is installed before the driver's first lazy initialization. The existing
user inversion policy remains; normal output uses controller inversion on.

The profile is selected by the image's public
`/usr/share/shieldsigner-lvgl/panel-profile.json`, or an explicit app option.
Direct hardware diagnostics also read that image profile. Generic bench
initialization remains available when no physical panel profile is selected.
The HOTHMI path requires 320×240 settings and does not silently use 240×240.
This is a manufacturer-based starting point, not a physical color/orientation
acceptance result.

## Buttons: all eight paths

Each normally-open switch connects only its intended host input to GND. There
are no external pull-ups. Released must be stable high and pressed low.

| Key | Switch | Host pin | GPIO bank / line | Domain |
|---|---|---:|---|---|
| Left | SW501 | 12 | 1 / 24 | 3.3 V |
| Up | SW502 | 13 | 1 / 25 | 3.3 V |
| Press | SW503 | 16 | 1 / 22 | 3.3 V |
| Down | SW504 | 17 | 1 / 23 | 3.3 V |
| Right | SW505 | 18 | 0 / 4 | 3.3 V |
| Key1 | SW506 | 19 | 4 / 16 | **1.8 V** |
| Key2 | SW507 | 20 | 4 / 17 | **1.8 V** |
| Key3 | SW508 | 11 | 1 / 21 | 3.3 V |

GPIO bank numbers are not Linux `/dev/gpiochipN` device indices. The retained
Mini device tree exposes banks 0, 1, 3 and 4; character-device indices depend on
probe order. In particular, bank 4 must not be assumed to be `gpiochip4`.
The carrier image installs `S41shieldsigner-gpio-banks`, which reads kernel chip
metadata and creates `/dev/gpiochip-bank0`, `-bank1` and `-bank4` aliases from
unique `gpio0`, `gpio1` and `gpio4` labels. The IO profile uses these aliases.
The pinned OS also has a Mini-specific `gpiochip4 → gpiochip3` workaround.
That can make the original profile work in its expected probe order; the
label-based policy removes that ordering assumption. Discovery ignores numeric
symlinks so the upstream alias is preserved without counting one device twice.
Resolution checks line counts before changing aliases and never requests GPIO
lines. Missing or ambiguous banks fail initialization. The application then
fails to open the missing alias rather than selecting an unrelated bank.
[The pinned kernel sources](../reference/research/firmware/gpio-cdev-sources.json)
record the cdev allocation, Rockchip labeling and metadata ioctl ABI evidence.
Tests cover sparse banks, reordered device indices, ambiguous labels and
preservation of existing regular files. The earlier transport simulation assumed
bank numbers matched device indices; the revised tests use the corrected profile.

The pinned-driver integration test allocates the eight real configured GPIO
inputs against simulated periphery. Through the actual LVGL input method it
checks press/release for every key, initial 5/10 ms bounce filtering and release
chatter without duplicate events. The C&K sheet specifies bounce at most 10 ms;
the LVGL press threshold is 25 ms. This is a software timing test, not a
measurement of the purchased switches or kernel input voltage.

The pinned Mini OS setup configures all eight input/pull-up paths. The app also
requests bias but may retry without it after GPIO errors. If that happens,
check OS setup/pinmux and measure released levels; floating inputs are not an
acceptable result. Never add 3.3 V pull-ups to Key1/Key2.

The retained compiled SDK snapshot has a dormant DHT11 node on Down/GPIO1_C7
with `CONFIG_DHT11=n`. Enabling that driver while retaining its node can compete
with the button. New carrier validation rejects that condition, SPI MISO on LCD
reset, competing CS0 devices and other default pinctrl claims on these pins.
Live overlays and GPIO ownership still need inspection on the finished image.

## Power clip row

The 0.0.12 front row is **GND (TP902) — +5 V (TP901) — GND (TP909)**,
at 15 mm centres. The three factory Keystone loops replace the previous 7 mm
spacing of the power pair. Native land-edge gap is 11.6 mm; actual alligator
clip clearance, insulation and mechanical strain remain first-article checks.
[The bounded layout audit](../hardware/power-clip-layout-audit.json)
records the moved points, rerouted service spurs and unchanged retained pad nets.
No LCD, GPIO/button or reader signals changed, so the existing carrier image
remains the software candidate; its recorded readback evidence is preserved.

## Power and footprints

The LCD operating range is 3.1–3.6 V. Its typical backlight current is not a
maximum total-module current, and U701's 600 mA headline rating is not a thermal
budget at 5 V input. Measure total module load, rail minima/maxima and regulator
temperature at recorded ambient and enclosure conditions. The
[power sensitivity calculation](../hardware/manufacturing/lcd-power-budget.json)
is planning evidence only.

C701/C702 use Samsung CL21A106KAYNNNE. Its local typical DC-bias curves show
substantial capacitance loss at several volts; nominal 10 µF alone is not a
minimum over voltage, tolerance, aging and temperature. The reader's nominal
1 µF / 50 V X7R CL21B105KBFNNNE is different; its supplier PDF is a family catalog,
not a part-specific capacitance-at-bias guarantee.

The C&K G-lead switch lands are 1.25 × 2.1 mm at ±3.875 mm. They replace the
inherited standard-board pattern. Keystone uses the official KiCad 3.4 × 1.8 mm
land; its drawing gives 3.43 × 1.78 mm. That library rounding is retained for
assembler DFM review. Models and software checks do not establish solder yield.

## Smartcard path

The desk checks cover separate VDD5, reader VDD33 and switched card-supply nodes;
nominal 1 µF decoupling; UART direction through R602/R603; numbered first-channel
socket contacts; presence detection and series card-clock resistor. Host TX
feeds reader RX pin 11; reader TX pin 14 feeds host RX. These are 3.3 V UART
signals; the series resistors are not voltage translators.

Select **SEC1210/PV-UR2**, not URT, in the OS reader configuration. UART2 must be
enabled without a serial-console conflict. Only the first physical card channel
is wired. The driver negotiates its startup baud rate; test its handshake rather
than forcing a guessed rate. C6 is tied to card VCC in this design, so use a
compatible test card and validate activation/presence/ATR before a harmless
transaction. LVGL smartcard UI and card operation are not qualified by the
camera/display build-input package.

## Prepared first-article build inputs

The replacement combined stage with the bank-label fix is
`dist/firmware/staging/carrier-first-article-hothmi-alias-compatible`.
`carrier-first-article-hothmi-review-v2` is superseded and must not be flashed.
Its candidate OS build was stopped before completion (terminal exit 137).
The replacement includes the HOTHMI initializer and image profile, 320×240 first-run template,
carrier GPIO mapping and revalidated development/zram kernel proof. Its hashes
and verification count are in the build preparation record. Earlier geometry-only
stages are superseded for this panel.

```sh
mise run firmware:stage --name NEW_UNIQUE_NAME \
  --camera dist/firmware/staging/carrier-first-article-camera-alias-compatible-20261110 \
  --display-config st7789_320x240
```

Attachment rejects the bench pin profile. Offline preflight refuses existing
settings templates or panel-profile files before any overlay writes. Persisted
`/userdata` settings retain priority and are never overwritten: use fresh
first-article media or review its display setting separately.

The replacement candidate job is `carrier-first-article-hothmi-alias-compatible-20261110`.
It finished with exit 0. Packed-image readback and all four ARM userspace QEMU
checks passed; [the exact readback report](../hardware/carrier-image-verification.json)
records the installed DTB, carrier IO mapping, pull-up startup, reader library
and HOTHMI settings. The actual packed renderer reached `(319,239)`. The first
readback exposed a verifier wrapper that dropped geometry arguments; its fix
was regression-tested, and the same image passed the second readback.

The local candidate is **`lvgl-dev.e4c4ec6a5760`**, under
`dist/firmware/images/lvgl-dev.e4c4ec6a5760/`:

- `shieldsigner-lvgl-dev-e4c4ec6a5760-hothmi-carrier.img.xz` — 64,350,808 bytes;
  SHA-256 `8f13e96081bddeb45b987607adbfa3b73aaf04b5da17849261833542955dff02`.
- Decompressed `.img` — 363,786,240 bytes;
  SHA-256 `ce35f7cea5684f9668a1ab849185d6e7d6cc8e800078d393cef4a945d8fcd697`.

`mise run firmware:verify lvgl-dev.e4c4ec6a5760` verifies both forms and frozen
provenance. The current bench-image selection is unchanged. This carrier image
has not been flashed or booted; physical LCD/button/card acceptance remains open. The PIL rollback path has not gained
320×240 support; the LVGL profile does not qualify that separate frontend.

## Repeatable checks and evidence

```sh
mise run datasheets:check
mise run variant:lcd:pinouts
mise run variant:lcd:runtime-audit
mise run variant:lcd:kernel-pinmux
mise run firmware:io:check
mise run firmware:test
mise run lvgl:app:test
mise run lvgl:app:test:host frames geometry
```

[Pinout report](../hardware/pinout-audit.json) checks all 22 host
pins, eight LCD pins and every button's exact net membership.
[Runtime audit](../hardware/carrier-runtime-audit.json) exercises
pinned reset/wake methods and the selected manufacturer program with virtual
time and GPIO/SPI substitutes.
[Compiled pinmux audit](../hardware/compiled-pinmux-audit.json)
identifies its retained kernel snapshot; it is not the installed image.
The new carrier kernel ABI report validates archived input hashes, 190 ARM ABI
assertions, camera/memory configuration, enabled UART2 and carrier pinmux.
New carrier application packaging requires that explicit proof.
The compiled reader UART audit uses the same DTB/config hashes as the prepared
development carrier proof. It checks UART2_M1 on GPIO1_B2/B3 and rejects UART2
console/early-console arguments. A dormant FIQ-debugger node names UART2, but
`CONFIG_FIQ_DEBUGGER=n`; enabling its driver conflicts with the reader and now
fails new kernel validation. Bootloader output, rootfs getty/PCSC service state
and actual card communication still require finished-image/live checks.

The pinned SPI-class integration test also verifies mode 0, the 10 MHz request,
DC/reset GPIO selection, the complete HOTHMI command/data stream and normal
inversion policy. RGBW bytes are sent through the actual SPI transfer methods
at columns 254–257 and 316–319, verifying both high address bytes and the right
edge. GPIO/SPI and board detection are simulated; no electrical waveform or
physical pixel output is inferred from that result.


## First-article acceptance order

1. Unpowered inspection: actual header orientation, every LCD signal, rail
   shorts, straps and all eight switches open released/closed to GND pressed.
2. One regulated, current-limited 5 V source: carrier-only rails first, then
   host and LCD. Do not externally feed host 3.3 V or combine USB/bench sources.
3. Finished carrier image: confirm actual GPIO ownership, 10 MHz SPI, CS/DC/reset
   waveforms, panel profile and 320×240 setting before normal use.
4. All eight buttons: released/pressed levels, holds, repeats, simultaneous keys
   and case actuation. Measure Key1/Key2 in their 1.8 V domain.
5. Display: RGBW, byte order, inversion, rotation, all four corners and full
   extents, plus repeated cold/warm starts. SPI success alone is not panel output.
6. Power: whole LCD current, startup/shutdown and combined-load rail transients,
   U701 temperature and stable operation at recorded ambient/enclosure conditions.
7. Reader: UART handshake, correct UR2/first-slot selection, presence/removal,
   card voltage/activation, ATR and a harmless test-card transaction.

Record results in [the bring-up record](BRINGUP-RESULTS.md). Blank fields and
software checks are not physical acceptance results.
