#!/usr/bin/env bash
# Run on Linux with the already-built pinned Luckfox SDK. No SDK mutation.
set -euo pipefail
sdk_dir="$(cd "${1:?Usage: build-uclibc.sh SDK_DIR}" && pwd)"
crate_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
host_dir="$sdk_dir/sysdrv/source/buildroot/buildroot-2024.11.4/output/host"
compiler="$sdk_dir/tools/linux/toolchain/arm-rockchip830-linux-uclibcgnueabihf/bin/arm-rockchip830-linux-uclibcgnueabihf-gcc"
sysroot="$host_dir/arm-buildroot-linux-uclibcgnueabihf/sysroot"
[[ -x "$compiler" && -x "$host_dir/bin/rustc" && -d "$sysroot" ]] || { echo 'Built SDK toolchain missing' >&2; exit 1; }
export PATH="$host_dir/bin:$PATH"
export RUSTC="$host_dir/bin/rustc"
export PYO3_NO_PYTHON=1
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_UCLIBCEABIHF_LINKER="$compiler"
export RUSTFLAGS="-C link-arg=--sysroot=$sysroot -C target-cpu=cortex-a7"
cd "$crate_dir"
cargo build --locked --release --features python --target armv7-unknown-linux-uclibceabihf
