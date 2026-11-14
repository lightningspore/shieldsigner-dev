# Phase 9 interpreter candidates

User requested evaluation of [RustPython](https://github.com/RustPython/RustPython) as a possible alternative to MicroPython. No final interpreter decision yet. Do not begin runtime porting before the Phase 8 gate; this is planning only.

## Preliminary RustPython findings

The upstream [mini REPL example](https://github.com/RustPython/RustPython/blob/main/examples/mini_repl.rs) demonstrates embedding without the Python standard library, registering a Rust function, and compiling interactive Python. That is a useful model for GPIO/I²C/SPI/camera bindings.

However, omitting Python's standard library does not remove Rust's `std`: the [VM implementation](https://github.com/RustPython/RustPython/blob/main/crates/vm/src/vm/mod.rs) imports `std` collections and OS string types, and the [crate root](https://github.com/RustPython/RustPython/blob/main/crates/vm/src/lib.rs) does not declare `no_std`. The [VM manifest](https://github.com/RustPython/RustPython/blob/main/crates/vm/Cargo.toml) has optional host environment/stdio/compiler/threading features, but that alone does not prove a build for armv7a-none-eabi. A bare-metal integration likely requires additional porting; this is an inference from source inspection, not a compile result.

## Decision tests before choosing

- Pin an upstream revision and attempt the smallest relevant ARM build; record concrete blockers.
- Measure linked image size, initial heap, repeated-script heap growth and time to UART REPL on DUT. Fit within 64 MB while preserving camera buffers.
- Demonstrate native Rust peripheral calls and frame-buffer access without unnecessary copies.
- Test reclamation, exceptions and allocation failure; the current monotonic bring-up heap is insufficient for a long-lived interpreter.
- Compare with MicroPython using the same scripts and camera workload. Keep the original peripheral/camera gate regardless of interpreter choice.
