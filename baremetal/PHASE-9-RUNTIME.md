# Phase9 MicroPython runtime

Phase9 hardware script passed on the RV1103 DUT through the actual UART REPL.
Five repeated RAM boots and the final API script passed; exact hashes are in
[evidence/phase-9.json](evidence/phase-9.json). This extends the bounded Phase8 camera
profile; standalone SD boot and USB debugging are separate remaining milestones.

## Runtime choice

The user requested evaluating RustPython and accepted MicroPython after the
bare-metal constraint was explained. RustPython revision
`1d17957399ef02dab4a3ed90622d44437acc6fc1` was checked with default VM features
removed and the compiler feature enabled:

```
mise exec rust@1.99.0 -- cargo check --manifest-path baremetal/.tools/RustPython/Cargo.toml -p rustpython-vm --no-default-features --features compiler --target armv7a-none-eabi --locked
```

The pinned revision requires Rust1.99; installed it separately without changing
the project's1.93.1 toolchain. The target build failed with E0463: dependency
`either` still imports Rust `std`, unavailable for this bare-metal target.
Disabling Python's standard library is a different operation from removing Rust
`std`; the VM and other dependencies also import `std`. This does not prove a
port impossible, but it requires additional runtime/platform work. Logs and
source remain ignored in `.tools/` and `logs/phase-9/`.

MicroPython v1.27.0, revision `78ff170de9e32c79db6e64d3e33d2bd60002bdcd`, is
linked unchanged through the original port in `micropython/`. Its upstream MIT
license is retained as `micropython/LICENSE.upstream`. The port follows the
[upstream porting guide](https://docs.micropython.org/en/v1.27.0/develop/porting.html).
The native Thumb2 NLR and GC register/stack helpers work on Cortex-A7; all C and
Rust use the compatible soft-float EABI.

## Memory and console

- Image/BSS below1MiB, IRQ stack below2MiB, unmapped guard2–3MiB, SVC stack below4MiB.
- Reclaiming Rust heap4–16MiB using pinned MIT `buddy_system_allocator`0.13.0.
  IRQ handlers remain allocation-free. The allocator hardware check exercises
  64 fragmented allocation/free cycles, coalescing an8MiB allocation and OOM
  rejection. The earlier bump allocator remains available in legacy diagnostics.
- MicroPython GC heap16–24MiB; camera DMA48–64MiB remains separate/noncacheable.
- UART2 at115200 through REF UART3. Ctrl-] resets DUT; uppercaseR is ordinary
  Python input. The4096-byte IRQ queue feeds the REPL. No filesystem or network
  is exposed yet. USB REPL/ADB is the next debugging milestone.

`tools/console.py` uses a single UART reader/writer and paste mode. UART output
is base64 framed across ADB so the outer PTY cannot change captured bytes.
Evidence stays ignored under `logs/phase-9/`. Scripts are compiled/executed on
DUT; a completed nonce alone is not the peripheral gate—check all emitted PASS
lines and script assertions as well.

## Supported API

```
from machine import Pin, I2C, SPI
import camera, time, gc

pin = Pin(52, Pin.OUT, value=0)  # GPIO1_C4;53 is GPIO1_C5
pin.value(1)
pin = Pin(52, Pin.IN)
i2c = I2C(4, freq=100000)
assert i2c.readfrom_mem(0x30, 0x3107, 2, addrsize=16) == b"\xcc\x41"
spi = SPI(0, baudrate=1000000)
spi.write_readinto(tx, rx)       # equal1..4096-byte buffers; in-place supported
camera.init()
frame = camera.capture()        #460800-byte NV12 memoryview,640×480
camera.settings(ae_target=48, exposure_seed=160)
```

Pin supports only the two proven GPIOs and IN/OUT modes. I2C supports the SC3336
at0x30,16-bit register addresses, up to32 bytes per call, with read/write methods.
SPI supports mode0,8-bit MSB-first,100kHz..50MHz requests; actual rate uses the
inherited clock and an even divisor. `time.ticks_ms()` and `sleep_ms()` use the
hardware generic timer.

Each capture starts the known sensor/ISP profile and runs32 bounded feedback
frames. It is not continuous video or a persistent camera-control session.
The returned memoryview is read-only and zero-copy; later captures overwrite its
underlying storage. Copy needed pixels before capturing again if retaining an
image. `ae_target=0` restores profile targets; other accepted values8..200 replace
the calibrated controller's target table. `exposure_seed`1..1352 sets the initial
sensor exposure before automatic control; it is not manual exposure lock.
Settings report final exposure/gain and current Rust allocation bytes.

## Build and test

`mise run baremetal:runtime:board:build` packages the image with the unchanged
vendor DDR blob. `baremetal:runtime:build` is the smaller REPL-only diagnostic.
The normal RAM harness loads it, then `mise run baremetal:runtime:gate` runs
`micropython/phase9_gate.py` on the already-running REPL. Do not run another UART
capture concurrently. Reset a runtime image with `printf "\035" > /dev/ttyS3`
on REF, rather than the old single-R reset command.

The first full gate ran at `console-20261114T170029Z`: GPIO transitions and
release; cc41 sensor ID plus safe same-value write/readback;4096-byte physical
SPI loopback at1/10/50MHz and in-place transfer; timer; two real NV12 captures;
AE-target/exposure-seed passthrough and sensor exposure readback; Rust heap0
before/after captures; repeated Python GC, invalid-input and exception handling.
The first pure REPL smoke test also executed arithmetic, allocations, GC and a
caught exception on DUT. The final script at `console-20261114T172550Z` also caught a9MiB allocation
failure and rejected writes to the camera view; all eight PASS markers passed.

For a fresh build, clone the pinned MicroPython revision into `.tools/micropython`.
The ARM GCC package on this host lacks libc headers; build-only newlib headers
were extracted from Ubuntu22.04 `libnewlib-dev`3.3.0-1.3 into `.tools/newlib/include`.
Only MicroPython's own minimal libc routines are linked, not a host libc.
The firmware manifest records the interpreter revision, archive hash, header
package, local port sources and the existing Rust3A source hashes.

## Reset and capture-window verification

A short6/8-second UART capture initially looked like an interrupt-start stall.
A later UART probe received the reset marker successfully, and the6-second run
ended at the DDR banner: the capture budget included ROM/USB handoff and diagnostic self-tests. A later
measurement recorded the download command at1.35s, hello at7.45s and REPL at8.68s
from capture start; the remaining handoff time was not isolated.
Treat those as insufficient capture budgets, not proven firmware hangs. The
harness now records command wall times; the repeated runtime boot test uses an
18-second total capture window including download. Firmware also initializes
all GIC enable/pending/active banks before enabling owned sources, and the UART
reset path completes its acknowledged interrupt before issuing warm reset.
These initialization changes are verified by the repeated boots and final script.
