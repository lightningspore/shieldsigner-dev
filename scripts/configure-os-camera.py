#!/usr/bin/env python3
"""Apply/revert only reviewed Rust-camera hooks in the pinned Luckfox OS tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = "e7589465aff172f4f510ad46d18776ccc8d2c203"
FILES = ["opt/luckfox/build.sh", "opt/luckfox/os-build.sh",
         "opt/luckfox/prepare-oem-for-rootfs.sh"]


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Pinned camera hook anchor is not unique: " + before[:70])
    return text.replace(before, after, 1)


def patched(name, text, dependencies=True, probe=True, cma=True, memory=True, lcd=True, io=True):
    if name.endswith("/build.sh"):
        text = replace_once(text, '    local docker_args="$PLATFORM_ARGS', '''    local camera_bundle_arg=""
    if [[ -n "${SHIELDSIGNER_CAMERA_BUNDLE:-}" ]]; then
        [[ -f "$SHIELDSIGNER_CAMERA_BUNDLE/manifest.json" ]] || { print_error "Camera bundle manifest missing"; exit 1; }
        case "$SHIELDSIGNER_CAMERA_BUNDLE" in *[[:space:]]*) print_error "Camera bundle path must not contain whitespace"; exit 1 ;; esac
        camera_bundle_arg="-v $SHIELDSIGNER_CAMERA_BUNDLE:/build/shieldsigner-camera:ro -e SHIELDSIGNER_KERNEL_PROBE_ONLY=${SHIELDSIGNER_KERNEL_PROBE_ONLY:-0} -e MINI_CMA_SIZE=${MINI_CMA_SIZE:-12M}"
    fi
    local docker_args="$PLATFORM_ARGS''')
        text = replace_once(text, '                       $env_args"', '                       $env_args $camera_bundle_arg"')
    elif name.endswith("/os-build.sh"):
        if dependencies:
            text = replace_once(text, '    print_step "Building Rootfs"\n    sdk_build rootfs', '''    if [[ -f /build/shieldsigner-camera/image-overlay.py ]]; then
        export SHIELDSIGNER_CAMERA_SDK_DIR="$LUCKFOX_SDK_DIR"
        if [[ "${SHIELDSIGNER_KERNEL_PROBE_ONLY:-0}" == 1 ]]; then
            python3 /build/shieldsigner-camera/collect-kernel-probe.py "$LUCKFOX_SDK_DIR" /build/output/kernel-probe
            exit 0
        fi
        export SHIELDSIGNER_CAMERA_BUILDROOT_DIR="$(bash "$SEEDSIGNER_LUCKFOX_DIR/resolve-buildroot-dir.sh" "$LUCKFOX_SDK_DIR")"
        python3 /build/shieldsigner-camera/image-overlay.py --buildroot "$SHIELDSIGNER_CAMERA_BUILDROOT_DIR"
    fi
    print_step "Building Rootfs"
    sdk_build rootfs''')
        text = replace_once(text, '    # Non-dev (production) rootfs hardening:', '''    if [[ -f /build/shieldsigner-camera/image-overlay.py ]]; then
        print_step "Installing verified ShieldSigner Rust camera runtime"
        python3 /build/shieldsigner-camera/image-overlay.py --rootfs "$ROOTFS_DIR"
    fi

    # Non-dev (production) rootfs hardening:''')
        text = replace_once(text, '    # with CI via patch-oem-pre-hook.sh.\n    if [[ "$SEEDSIGNER_BUILD_VARIANT" == "non-dev" ]]; then',
                            '    # with CI via patch-oem-pre-hook.sh.\n    if [[ "$SEEDSIGNER_BUILD_VARIANT" == "non-dev" || -d /build/shieldsigner-camera ]]; then')
        text = replace_once(text, '    sdk_build firmware\n', '''    sdk_build firmware
    if [[ -f /build/shieldsigner-camera/image-overlay.py ]]; then
        python3 /build/shieldsigner-camera/image-overlay.py --verify "$ROOTFS_DIR"
    fi
''')
    else:
        text += '''
# ShieldSigner Rust camera: strip closed userspace after the SDK assembles OEM,
# before it is folded into the signed rootfs. Keep IQ JSON and open drivers.
if [ -f /build/shieldsigner-camera/image-overlay.py ]; then
    python3 /build/shieldsigner-camera/image-overlay.py --oem "$OEM_DIR"
fi
'''
    if memory and name.endswith("/os-build.sh"):
        text = replace_once(text, '    print_step "Building Kernel"\n    sdk_build kernel', '''    if [[ -f /build/shieldsigner-camera/zram-image-profile.py ]]; then
        python3 /build/shieldsigner-camera/zram-image-profile.py --kernel "$LUCKFOX_SDK_DIR"
    fi
    print_step "Building Kernel"
    sdk_build kernel''')
        text = replace_once(text, '        python3 /build/shieldsigner-camera/image-overlay.py --rootfs "$ROOTFS_DIR"', '''        python3 /build/shieldsigner-camera/image-overlay.py --rootfs "$ROOTFS_DIR"
        if [[ -f /build/shieldsigner-camera/zram-image-profile.py ]]; then
            python3 /build/shieldsigner-camera/zram-image-profile.py --rootfs "$ROOTFS_DIR" --sdk "$LUCKFOX_SDK_DIR"
        fi''')
        text = replace_once(text, '        python3 /build/shieldsigner-camera/image-overlay.py --verify "$ROOTFS_DIR"', '''        python3 /build/shieldsigner-camera/image-overlay.py --verify "$ROOTFS_DIR"
        if [[ -f /build/shieldsigner-camera/zram-image-profile.py ]]; then
            python3 /build/shieldsigner-camera/zram-image-profile.py --verify "$ROOTFS_DIR"
        fi''')
    if lcd and name.endswith("/os-build.sh"):
        text = replace_once(text, '        python3 /build/shieldsigner-camera/image-overlay.py --buildroot "$SHIELDSIGNER_CAMERA_BUILDROOT_DIR"', '''        python3 /build/shieldsigner-camera/image-overlay.py --buildroot "$SHIELDSIGNER_CAMERA_BUILDROOT_DIR"
        if [[ -f /build/shieldsigner-camera/lcd-image-profile.py ]]; then
            python3 /build/shieldsigner-camera/lcd-image-profile.py --buildroot "$SHIELDSIGNER_CAMERA_BUILDROOT_DIR"
        fi''')
        text = replace_once(text, '        python3 /build/shieldsigner-camera/image-overlay.py --rootfs "$ROOTFS_DIR"', '''        python3 /build/shieldsigner-camera/image-overlay.py --rootfs "$ROOTFS_DIR"
        if [[ -f /build/shieldsigner-camera/lcd-image-profile.py ]]; then
            python3 /build/shieldsigner-camera/lcd-image-profile.py --install "$ROOTFS_DIR"
        fi''')
        text = replace_once(text, '        python3 /build/shieldsigner-camera/image-overlay.py --verify "$ROOTFS_DIR"', '''        python3 /build/shieldsigner-camera/image-overlay.py --verify "$ROOTFS_DIR"
        if [[ -f /build/shieldsigner-camera/lcd-image-profile.py ]]; then
            python3 /build/shieldsigner-camera/lcd-image-profile.py --verify "$ROOTFS_DIR"
        fi''')
    if io and name.endswith("/os-build.sh"):
        text = replace_once(text, '    print_step "Building Kernel"\n    sdk_build kernel', '''    if [[ -f /build/shieldsigner-camera/configure-image-io-profile.py ]]; then
        export SHIELDSIGNER_IO_KERNEL_RECEIPT=/build/output/io-kernel-policy.json
        io_profile=$(python3 -c 'import json; print(json.load(open("/build/shieldsigner-camera/manifest.json")).get("ioProfile", "carrier"))')
        python3 /build/shieldsigner-camera/configure-image-io-profile.py --kernel-sdk "$LUCKFOX_SDK_DIR" --profile "$io_profile" --receipt "$SHIELDSIGNER_IO_KERNEL_RECEIPT"
    fi
    print_step "Building Kernel"
    sdk_build kernel''')
    if not cma:
        text = text.replace(' -e MINI_CMA_SIZE=${MINI_CMA_SIZE:-12M}', '')
    if not probe:
        text = text.replace(' -e SHIELDSIGNER_KERNEL_PROBE_ONLY=${SHIELDSIGNER_KERNEL_PROBE_ONLY:-0}', '')
        text = text.replace('        if [[ "${SHIELDSIGNER_KERNEL_PROBE_ONLY:-0}" == 1 ]]; then\n            python3 /build/shieldsigner-camera/collect-kernel-probe.py "$LUCKFOX_SDK_DIR" /build/output/kernel-probe\n            exit 0\n        fi\n', '')
    return text


def configure(checkout, mode):
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise ValueError("OS revision differs from reviewed camera hook pin")
    changes, result = [], []
    for name in FILES:
        original = subprocess.check_output(["git", "-C", str(checkout), "show", PIN + ":" + name]).decode()
        desired = patched(name, original)
        path = checkout / name
        prior_io_desired = patched(name, original, io=False)
        prior_lcd_desired = patched(name, original, lcd=False, io=False)
        prior_memory_desired = patched(name, original, memory=False, lcd=False, io=False)
        prior_desired = patched(name, original, probe=False, cma=False, memory=False, lcd=False, io=False)
        prior_probe_desired = patched(name, original, cma=False, memory=False, lcd=False, io=False)
        previous_dependency_hook = desired.replace('        export SHIELDSIGNER_CAMERA_SDK_DIR="$LUCKFOX_SDK_DIR"\n', '')
        if path.read_text() not in {original, desired, prior_io_desired, prior_lcd_desired, prior_memory_desired, prior_desired, prior_probe_desired, previous_dependency_hook, patched(name, original, dependencies=False, memory=False, lcd=False, io=False)}:
            raise ValueError("OS camera hook has unreviewed edits: " + name)
        data = desired if mode == "rust" else original
        changes.append((path, data))
        result.append({"file": name, "sha256": hashlib.sha256(data.encode()).hexdigest()})
    for path, data in changes:
        path.write_text(data)
    return {"osCommit": PIN, "cameraBackend": mode, "files": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--mode", choices=["rust", "vendor"], required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    text = json.dumps(configure(args.checkout, args.mode), indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(text)
    print(text, end="")
