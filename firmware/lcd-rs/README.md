# Rust LCD frame transport prototype

This prototype moves RGB888-to-big-endian-RGB565 conversion and Linux SPI
messages into Rust/PyO3. Conversion and SPI waits release the Python GIL. A
reusable 115,200-byte buffer serves the 240×240 panel; the Python periphery
full-frame returned integer list is eliminated. This is not yet a hardware
qualification or a guarantee that the camera/UI fits the Mini's 64 MiB RAM.

The process-local shim preserves the exact reviewed board ST7789 driver's
GPIO acquisition, reset delays, command sequence, inversion behavior and SPI
configuration. Confirmed wiring is DC56, RST57, `/dev/spidev0.0`, mode0,
kernel-managed CS and10MHz; INVON is normal colors. The shim never selects or
requests new GPIO lines. It requires the reviewed source SHA in
`python/shieldsigner_lcd_driver.py` and must be installed before Renderer/display
construction. Existing GPIO handles (currently periphery GPIO) remain in use;
a separate gpiod ABI is not introduced.

`FrameWriter` duplicates the configured SPI fd with CLOEXEC. Its destructor
closes only the duplicate. The shim serializes GPIO/window/data transactions
across Python threads. Native writes start at4096-byte messages and reduce only
EMSGSIZE, down to256bytes, before retrying those bytes. Other errors and short
messages fail without replaying uncertain writes. There is no MISO/readback
verification. Offset frames and other panel geometries are deliberately rejected.

Host verification:

```sh
mise exec -- cargo test --locked --manifest-path firmware/lcd-rs/Cargo.toml
mise exec -- cargo build --locked --release --features python --manifest-path firmware/lcd-rs/Cargo.toml
mise exec -- uv run --with pillow python -m unittest discover -s firmware/lcd-rs/python
```

The extension uses pinned PyO3 0.23.5, `abi3-py311`, and the Cargo lockfile. On
Unix, unresolved Python symbols bind to the importing interpreter; macOS linker
arguments are added by `pyo3-build-config`. See the [official PyO3 build guide](https://pyo3.rs/v0.23.5/building-and-distribution.html).

The board requires an **uClibc shared library**, not the camera's standalone
musl executable target. Use the existing pinned SDK's built Rust1.82 compiler,
ARM std, GCC8 and sysroot on the Linux builder:

```sh
bash firmware/lcd-rs/build-uclibc.sh /path/to/luckfox-pico
```

Run inside the existing builder image (with its entrypoint overridden to bash)
if the host lacks a C compiler. The SDK can be mounted read-only. The artifact
is `target/armv7-unknown-linux-uclibceabihf/release/libshieldsigner_lcd.so`;
install it under an importable name such as `shieldsigner_lcd.abi3.so`.
Dependencies are target `libgcc_s.so.1`, `libc.so.0` and `ld-uClibc.so.1`.

Without touching GPIO or SPI:

```sh
PYTHONPATH=/path/to/extension python3 firmware/lcd-rs/python/bench_lcd.py
```

For an explicitly authorized hardware trial, add the extension and shim to
PYTHONPATH, then call `shieldsigner_lcd_driver.install('/opt/src')` before the
normal integration entry point constructs the display. Keep the production
files unchanged. First qualify primary colors/orientation, inversion and
repeated-frame/recovery behavior; then measure actual full GUI/camera memory,
CPU, cancellation and QR acquisition. A successful packing bench does not
qualify any of those hardware behaviors.

The [prototype validation record](prototype-validation.json) separates builds,
host tests and hardware results. The earlier3090artifact imported on board
Python3.12 and completed60SPIframes: median110.614ms/max116.256ms, versus
119.916ms/121.268ms for60frames with the existing Python path. There is no human
visual confirmation or SPI readback. The final a3d8artifact was rebuilt from
formatted source with a compile-time SPI layout assertion; its combined GUI
trial is separate. Successful transfers do not establish full camera/UI reliability.

The final a3d8artifact subsequently passed1000actual board SPI frames:
median110.448ms, maximum259.666ms. Process RSS changed19,952→19,964KiB
while the timing sample list grew; this is not an isolated heap leak test.
Human confirmation of colors/orientation and combined GUI/optical reliability
remain separate gates.

The normal integration launcher keeps Python as its default. Explicitly select
`--lcd-backend rust` or `SHIELDSIGNER_LCD_BACKEND=rust`, with the extension and
reviewed shim on PYTHONPATH. Selection occurs before camera/Controller setup,
uses the shim's idempotent installer and fails explicitly if the runtime is
missing or the display source differs. This does not change pins or make the
native backend the production default.


## Native preview primitive

`PreviewRenderer(width=240, height=180)` reuses a bounded RGB output vector. `render_luma(bytes, source_width, source_height, rotation)` returns expanded output dimensions and independent RGB bytes for 0/90/180/270 degrees. Processing releases the GIL; concurrent use fails explicitly rather than waiting with the GIL held. Source geometry and destination bounds are checked before writing. The current interface is a primitive; it does not yet replace app reception or GUI preparation.

`tests/preview-reference.py` requires the compiled extension on PYTHONPATH and pinned Pillow 11.0.0. It compares every output byte for four geometries and four rotations, tests independent returned buffers and rejects invalid inputs without touching GPIO/SPI. The physical ARM result is in `reverse-engineering/rkaiq/frontend/preview-arm-reference-2026-10-29.json`. The upstream divergence and rollout plan are documented in `docs/UPSTREAM-DIVERGENCES.md` and `docs/NATIVE-FRONTEND-PLAN.md`.
