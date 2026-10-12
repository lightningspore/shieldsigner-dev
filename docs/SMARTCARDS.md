# Smartcards: which work, and what they do

## Exact reader hardware on this PCB

The card connector is **J601, Amphenol 7312P0225A13LF**, supplier **LCSC/JLCPCB C5417011**. It is a bottom-side, surface-mount **contact smartcard socket**, with eight card contacts and a normally-open insertion switch. It is not a microSD socket, USB reader, or NFC reader. The PCB uses the custom `Library:AMPHENOL_7312P0225A13LF_smrt2_combo_handsolder` footprint. The extended hand-solder lands are inherited; automated reflow qualification remains pending. The socket is fitted in the carrier BOM even when the Luckfox module is supplied separately.

Use the saved [Amphenol mechanical drawing](../reference/pdfs/C5417011.pdf) for contact locations, retention and insertion direction, and the [J601 component map](COMPONENTS.md#j601) for this board's land assignments. The upstream describes a combined full-size/SIM arrangement. A full-size contact card is the initial test fixture; smaller card formats require verified retention/contact alignment or an appropriate adapter. “SIM compatible” does not establish application support for telecom SIMs. Card orientation must follow the drawing and socket contacts; “chip up” is ambiguous because J601 is on the board's bottom side.

| J601 contact | PCB connection | Purpose |
|---|---|---|
| C1 | U601 SC1_VCC, C604 1 µF | Reader-controlled card power |
| C2 | U601 SC1_RST_N; R605 10 kΩ to ground | Card reset |
| C3 | U601 SC1_CLK through R604 47 Ω | Card clock |
| C4 | Unconnected | Reserved/auxiliary contact unused |
| C5 | GND | Card return |
| C6 | Same switched supply as C1 | Legacy programming-voltage contact; confirm target-card compatibility |
| C7 | U601 SC1_IO; R606 100 kΩ to ground | Bidirectional card data |
| C8 | Unconnected | Reserved/auxiliary contact unused |
| COM / NO | GND / U601 SC1_PRSNT_N | Mechanical insertion detection; closes to ground |

Pad names are physical card-contact identifiers, not tscircuit's generated `pinN` aliases. C6 is **not** an independently generated programming supply here. C4/C8 are not wired for a second interface, and the carrier does not route USB to the card socket.

**U601 is Microchip SEC1210/PV-UR2, C633309**, a preprogrammed UART-to-smartcard bridge in the PCB's QFN package. The socket provides contacts; U601 handles card activation, clock/reset, switched voltage and protocol timing. Luckfox UART2 TX reaches U601 RXD through R602, and U601 TXD reaches Luckfox RX through R603. The processor exchanges framed reader commands over UART rather than directly bit-banging C7. U601 is powered from +5 V; its VDD33 output has C603 1 µF decoupling, and its separate active card supply has C604 1 µF. R601/C601 provide bridge reset startup, and R607 biases TEST for normal operation.

The SEC1210 supports ISO/IEC 7816 contact protocols **T=0 and T=1**, and nominal **Class A 5 V, Class B 3 V, Class C 1.8 V** card supplies. This is bridge capability, not proof that every card or supply class has been tested on our PCB. Its low-input-voltage protection disables 5 V/Class A operation below the internal approximately 4.8 V threshold; use a stable regulated 5 V input and let the reader select card voltage. This hardware does not establish synchronous memory-card, magnetic stripe, NFC, arbitrary SIM or arbitrary payment-card application compatibility. [Microchip data sheet](../reference/pdfs/SEC1210-DS00001561D.pdf), [manufacturer source](https://ww1.microchip.com/downloads/en/DeviceDoc/00001561D.pdf).

UR2 supports two reader channels; **only SC1 has a physical socket on this carrier**. The unused SC2 is not a second connector you can attach without a hardware change. URT, UR2 and blank/differently programmed SEC1210 parts are not interchangeable BOM selections.

## How the reader works with Linux

The software path is:

```text
ShieldSigner Python card backend (applet-specific commands)
  → pyscard / PC/SC client library
  → local pcscd daemon
  → CCID serial IFD driver: libccidtwin.so
  → Linux UART2 device: /dev/ttyS2
  → SEC1210/PV-UR2 SC1
  → J601 contacts → card applet
```

An **APDU** is an application command/response exchanged with the card. An **ATR** is the card's initial response after activation/reset; it helps establish communication parameters but does not prove the wallet applet is installed. PC/SC presents reader/slot discovery, card insertion state and command exchange to the application. The applet backend then selects and interprets SeedKeeper, Satochip or another supported application. Linux's UART driver transports bytes; it does not implement the wallet applet.

The CCID driver normally associated with USB readers also has a **serial build**, selected here. This PCB's reader is not discovered through USB enumeration: it needs an explicit serial reader configuration. The pinned Buildroot recipe builds CCID **1.7.1** with `-Dserial=true`, plus `pcsc-lite` and `python-pyscard`. The upstream Luckfox image installs `/etc/init.d/S60pcscd`, starts a supervisor for `pcscd`, and logs it to `/tmp/pcscd.log`. App/client communication uses the local UNIX socket `/run/pcscd/pcscd.comm`; it does not require Internet connectivity. Kernel `CONFIG_NET` and `CONFIG_UNIX` must remain enabled for this local IPC even on an offline signer.

For **our selected UR2 part**, the intended reader file is:

```text
DEVICENAME        /dev/ttyS2:SEC1210UR2
FRIENDLYNAME      "SEC1210"
LIBPATH           /usr/lib/pcsc/drivers/serial/libccidtwin.so
```

The pinned OS copies its reader file to both `/etc/reader.conf.d/sec1210` and `/etc/readers.d/sec1210`. Keep those copies consistent when making a recorded firmware patch. The current carrier wrapper prepares UR2; its full image build remains unqualified. **The two successfully built historical baseline images still contain `SEC1210URT`**, so they need this documented adjustment before UR2 carrier testing; this guide does not imply we already patched or boot-tested them. CCID 1.7.1 treats URT as one slot and UR2 as two. A second empty enumerated slot can be expected; identify the physically connected SC1 slot by insertion/removal rather than hardcoding a reader-list index. The serial driver starts at 9600 baud and negotiates 115200, so both rates can appear in a capture.

UART2 pinmux and the `/dev/ttyS2` device must be enabled, and its serial console/getty must be disabled. A second process opening the UART can corrupt reader traffic. This is a userspace serial driver, so there is no separate SEC1210 kernel module to load. The image's PC/SC library/driver locations and architecture must match; installing a desktop USB-reader package alone does not configure this UART reader.

Pinned implementation sources: [CCID serial variant handling](https://github.com/LudovicRousseau/CCID/blob/1.7.1/src/ccid_serial.c), [Luckfox reader configuration](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/files/sec1210), [daemon startup](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/files/S60pcscd), [image integration](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/os-build.sh). Build inputs and the unchanged-image caveat are recorded in [OS-BUILD.md](OS-BUILD.md).

### Read-only checks on a development image

These commands are for a development image that exposes a shell; the production image may omit shell access or diagnostic programs. They inspect state without provisioning a card:

```sh
ls -l /dev/ttyS2 /usr/lib/pcsc/drivers/serial/libccidtwin.so
cat /etc/reader.conf.d/sec1210
cat /etc/readers.d/sec1210
/etc/init.d/S60pcscd status
ls -l /run/pcscd/pcscd.comm
tail -n 60 /tmp/pcscd.log
```

Where installed, `pcsc_scan` displays reader/slot and insertion/ATR state; stop it after testing. In the app, use the smartcard tools to inspect reader and applet identity. Do not run a second standalone `pcscd` alongside the image's supervised daemon. Keep testing to a spare card without wallet funds. Follow [bring-up stages 6 and 7](BRINGUP.md#stage-6--reader-configuration-before-inserting-a-card) for voltage, wiring and ATR measurements.

| Symptom | What to check next |
|---|---|
| No UART device | Kernel/device-tree UART2 configuration and module pinmux |
| PC/SC cannot connect | Daemon status, local socket and client permissions |
| Daemon runs, no reader | Reader file search paths, exact UR2 suffix, driver path, UART ownership and U601 reset/power |
| Reader exists, insertion never changes | Connected SC1 slot, socket COM/NO, card seating and detect input |
| Insertion works, no ATR | C1 supply, C2 reset, C3 clock, C7 data, contact orientation and supported card voltage |
| ATR works, applet missing | Correct card/app installation, applet identity/version and enabled application backend |
| Applet found, operation fails | Applet-specific status/error, PIN state and firmware support; not automatically an electrical fault |

The current evidence establishes source/datasheet compatibility and a successfully compiled Linux stack. It does **not** establish a physically tested reader, a qualified small-card adapter, or successful card signing on this prototype. Record actual results in [BRINGUP-RESULTS.md](BRINGUP-RESULTS.md).

For this board, start with a **contact-capable retail SeedKeeper** if the goal is convenient seed/secret storage, or a **contact-capable retail Satochip** if the goal is signing on the card. Both avoid DIY applet provisioning during initial board bring-up. This is a recommendation based on the fork's documented support, not a claim that this particular prototype has been tested with either card. [Fork card support](https://3rditeration.github.io/seedsigner/smartcard_support_installation.html).

## Three different compatibility questions

1. **Physical/electrical:** does the card fit the socket and expose supported contact communication and supply classes?
2. **Transport:** can the SEC1210/CCID stack activate it and receive an ATR / exchange APDUs?
3. **Application:** does ShieldSigner recognize the installed applet and implement the intended operation?

An ATR does not mean the card can store a Bitcoin seed or sign a PSBT. A familiar chip family does not mean a blank, locked, banking or EMV card can accept the desired applet.

The reader on this PCB is **contact-only**: J601 connects through the SEC1210 UART bridge. There is no PN532, NFC antenna or other contactless reader in the carrier BOM. A dual-interface card can use its contact interface here; its NFC features remain useful with other devices. An NFC-only card/tag cannot be read by this PCB merely because the fork supports NFC elsewhere.

## Practical card choices

| Card / applet | What the fork uses it for | Fit for this carrier |
|---|---|---|
| Retail SeedKeeper with contact chip | PIN-protected seed, passphrase and secret storage | First choice for storage; confirm exact retail card has contact capability |
| Retail Satochip with contact chip | Seed-bearing on-card derivation/signing | First choice for signing; use a spare/test card for bring-up |
| Blank J3R180 **SECID** with a compatible applet | DIY SeedKeeper / Satochip / other supported applets | Good DIY candidate; requires known GlobalPlatform management keys and provisioning |
| Blank J3R110 **SECID**, J3H145 | Other reported working DIY platforms | Candidate alternatives; confirm exact configuration/app versions |
| Keycard applet on a compatible contact JavaCard | Keycard backend for seed/xpub/signing flows | Conditional: enable backend and verify dependencies; do not substitute an NFC-only retail card |
| Satodime with contact interface | Bearer-key slots and deliberate seal/unseal workflows | Supported applet family, but a different custody model; not the default seed-backup card |
| Specter-DIY MemoryCard applet | Simpler mnemonic-card workflows | Conditional: compatible contact JavaCard and enabled feature |
| OpenPGP / OTP applets | Separate GPG or authenticator applications | Not automatically a Bitcoin signing/backup card; menu/backend support is app-specific |
| Bank/payment card, ordinary telecom SIM, NFC tag or arbitrary smartcard | Its own application | Not established as a supported signer/backup card |

The DIY maintainer lists J3R110/J3R180 based on NXP JCOP4 P71 SECID and J3H145 based on JCOP3 P60 as working platforms. It distinguishes SECID from EMV configurations and notes reliability differences for THD89 cards with official versus modified applet builds. Prefer a specifically supported platform over an arbitrary seller's “JavaCard” listing. [DIY compatibility evidence](https://github.com/3rdIteration/Satochip-DIY).

## SeedKeeper versus Satochip

**SeedKeeper is storage.** It keeps secrets persistently behind its card PIN/application mechanisms. When ShieldSigner loads a stored seed, that secret enters the host's memory and the host performs the ordinary signing workflow. This improves convenience and protection of stored data, but does not keep the loaded seed out of the Luckfox during use. The vendor documents dual contact/NFC connectivity on its card; select an actual contact-capable product. [Fork SeedKeeper guide](https://3rditeration.github.io/seedsigner/seedkeeper.html), [vendor connectivity guide](https://satochip.io/wp-content/uploads/2024/11/Seedkeeper-EN-Short-tuto-app-mobile.pdf).

**Satochip is a signing card.** Normal operations derive keys and produce signatures on the card, with ShieldSigner providing the display, transaction review and reader interface. Initializing/importing a seed can still involve the host; “on-card signing” is not a claim that every setup path avoids host secrets. The card still depends on the host presenting an accurately reviewed request. Use the fork's Satochip flows, not “load from SeedKeeper” workflows. [Fork Satochip guide](https://3rditeration.github.io/seedsigner/satochip.html).

Buying both makes sense when you want to compare these two workflows. For the first electrical test, one known-good contact card is sufficient; extra cards are system/test equipment, not PCBA components.

## DIY blank cards and applets

A blank card needs more than enough advertised memory. Confirm the exact JavaCard/GlobalPlatform configuration, cryptographic capability required by the applet, contact interface, known management keys and permission to install applications. Cards with unknown keys, incompatible crypto support or an incompatible EMV configuration are not equivalent to the tested SECID products.

The pinned fork bundles, among others:

| Applet | Pinned CAP filename | Intended role |
|---|---|---|
| SeedKeeper | `SeedKeeper-0.2-official.cap` | Secret/seed storage |
| SeedKeeper + NDEF | `SeedKeeper-Ndef-v0.2-0.1.cap` | Same storage plus NFC tag companion functionality |
| Satochip | `SatoChip-0.12-official.cap` | On-card wallet signing |
| Satodime | `SatoDime-0.1.2-official.cap` | Bearer-card key slots |
| Keycard | `Keycard_v3.2.cap` | Keycard-compatible signing backend |
| Specter-DIY | `SpecterDIY.cap` | Mnemonic memory-card workflows |

These names are verified against the locally pinned `reference/research/docs/javacard_applets.md`, not a promise about any other flashed image. Preserve the actual firmware release/app manifest when testing. The NDEF variant does **not** add NFC hardware to this carrier. If only using contact operation, the plain SeedKeeper build is sufficient. [Fork applet reference](https://3rditeration.github.io/seedsigner/javacard_applets.html).

For deliberate DIY provisioning, the fork offers Tools → Smartcard Tools → DIY Tools → Install Applet. First test the physical reader with a known-good card; then use a separate blank/test card for installation. Use the pinned CAP manifest, correct storage settings for the actual card, and a stable contact connection. Provisioning is not part of automatic PCBA bring-up and no card has been provisioned in this session.

Card-management GlobalPlatform keys are different from the applet PIN and from wallet keys. Preserve them before changing them. A card that answers transport commands may still reject installation because its management keys/configuration differ. Do not treat repeated installation attempts or a factory reset as a harmless electrical diagnostic.

## Conditional support and important differences

**Keycard:** the fork defaults KeyCard support to disabled, and its compatibility backend/dependencies must be present. The menu and backend are separate from the card's physical interface. A retail NFC-only Status Keycard requires an NFC reader that this PCB does not have; a compatible Keycard applet on a contact JavaCard is the relevant route here. [Fork Keycard requirements](https://3rditeration.github.io/seedsigner/keycard.html).

**Satodime:** this is a bearer-key workflow, not interchangeable SeedKeeper backup storage. The fork documents that unsealing exposes a slot's private key and changes the slot state. Its contact path also differs from NFC unlock-code protection. Read that behavior before using it as a test card or depositing value; use an empty/spare card for bring-up. [Fork Satodime behavior](https://3rditeration.github.io/seedsigner/satodime.html).

**Specter-DIY and other applets:** bundled CAP availability is not a universal guarantee that the desired menu/backend is enabled on a particular build. Inspect firmware settings and applet identity. Multiple applets can coexist on some platforms, but memory, cryptographic services and management policy must be qualified for that exact card.

**SIM-sized cards:** the upstream calls the custom socket arrangement full-size/SIM compatible. That describes mechanics, not an ordinary telecom SIM's ability to run SeedKeeper/Satochip. Verify how the desired card is physically retained, the actual contact alignment and C6 behavior; do not assume a loose smaller chip card will locate correctly.

## What to record for each card

Record a non-secret test ID, seller/exact product, chip/configuration where known, contact versus dual interface, applet/protocol version, firmware version, reader/slot and outcome. Do not record wallet secrets, PINs or management keys in project docs.

Bring-up progression is **presence → activation → ATR → applet identity → harmless application operation**. Failure at each step narrows a different problem. Do not repeatedly guess PINs, erase a card, unseal a bearer slot or replace applets to make an unrelated PCB error disappear.

## Support evidence versus our testing

The locally pinned fork source includes the card guides and settings definitions. Smartcard and Satochip support default to enabled; Keycard and Specter-DIY default to disabled at that pinned revision. Reader transport is separately configured for the selected UR2 hardware.

This project has performed source/datasheet review and generated manufacturing draft data. **No card/board combination has passed physical testing here yet.** Start with one factory-provisioned contact card and a documented spare-card test, then add DIY provisioning or more applets after the reader is stable.
