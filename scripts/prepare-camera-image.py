#!/usr/bin/env python3
"""Stage a checksummed development camera runtime for the pinned OS builder."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INSTALL = "/usr/lib/shieldsigner-camera"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_static_arm(path):
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 40:
        raise ValueError("Expected 32-bit little-endian ARM ELF: " + str(path))
    offset = struct.unpack_from("<I", data, 28)[0]
    size, count = struct.unpack_from("<HH", data, 42)
    for i in range(count):
        values = struct.unpack_from("<IIIIIIII", data, offset + i*size)
        if values[0] == 3:
            raise ValueError("Camera runtime must not require a dynamic interpreter")
        if values[0] == 2:
            for position in range(values[1], values[1] + values[4], 8):
                if struct.unpack_from("<I", data, position)[0] == 1:
                    raise ValueError("Camera runtime has a dynamic library dependency")



def validate_memory_proof(proof, memory_profile, kernel_probe):
    if memory_profile == "none" or kernel_probe:
        return
    if memory_profile != "zram16-lzo":
        raise ValueError("Unknown image memory profile")
    required = {"CONFIG_SWAP": "y", "CONFIG_ZSMALLOC": "m", "CONFIG_ZRAM": "m",
                "CONFIG_CRYPTO_LZO": "y", "CONFIG_ZRAM_WRITEBACK": "n",
                "CONFIG_ZRAM_MEMORY_TRACKING": "n", "CONFIG_ZSMALLOC_STAT": "n"}
    if proof.get("memoryProfile") != memory_profile or any(proof.get("requiredKernelConfig", {}).get(key) != value for key, value in required.items()):
        raise ValueError("Persistent zram requires its separately reviewed exact compiled-kernel ABI proof")



def validate_io_proof(proof, io_profile, kernel_probe):
    if io_profile == "carrier" or kernel_probe:
        return
    uart = proof.get("compiledUart2", [])
    if (proof.get("ioProfile") != "base-fork" or len(uart) != 1
            or uart[0].get("path") != "/serial@ff4c0000"
            or uart[0].get("status") != "disabled" or uart[0].get("enabled") is not False):
        raise ValueError("Base-fork requires its exact compiled UART2-disabled ABI proof")

def stage_lcd_inputs(staged, add):
    source = staged / "_lcd_vendor_inputs"
    source.mkdir()
    crate = ROOT / "firmware/lcd-rs"
    for name in ["Cargo.toml", "Cargo.lock", "build.rs"]:
        shutil.copyfile(crate/name, source/name)
    shutil.copytree(crate/"src", source/"src")
    (source/"python").mkdir()
    shutil.copyfile(crate/"python/shieldsigner_lcd_driver.py", source/"python/shieldsigner_lcd_driver.py")
    shutil.copyfile(ROOT/"LICENSE", source/"LICENSE")
    # Download only locked, checksummed public crate sources. The actual target
    # build is offline, and does not depend on a populated builder Cargo cache.
    subprocess.run(["mise", "exec", "--", "cargo", "vendor", "--locked", "--versioned-dirs", "vendor"],
                   cwd=source, check=True, stdout=subprocess.DEVNULL)
    (source/".cargo").mkdir(exist_ok=True)
    (source/".cargo/config.toml").write_text('[source.crates-io]\nreplace-with="vendored-sources"\n[source.vendored-sources]\ndirectory="vendor"\n[net]\noffline=true\n')
    inputs = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlink in vendored LCD source")
        if path.is_file():
            name = str(path.relative_to(source))
            add("lcd-source/"+name, path.read_bytes())
            inputs[name] = digest(path)
            if name.startswith("vendor/") and path.name.upper().startswith(("LICENSE", "COPYING", "NOTICE", "UNLICENSE")):
                add("payload/licenses/lcd-vendored/"+name[len("vendor/"):],path.read_bytes())
    source_sha = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    recipes = {}
    for name in ["Config.in", "shieldsigner-lcd.mk"]:
        path = ROOT/"scripts/image-profiles/lcd-package"/name
        add("lcd-package/"+name,path.read_bytes())
        recipes[name] = digest(path)
    helper = ROOT/"scripts/image-profiles/lcd-image-profile.py"
    add("lcd-image-profile.py",helper.read_bytes())
    recipes["helper"] = digest(helper)
    recipe_sha = hashlib.sha256(json.dumps({"sources":source_sha,"recipes":recipes},sort_keys=True).encode()).hexdigest()
    lock_sha = digest(source/"Cargo.lock")
    shutil.rmtree(source)
    return {"sourceManifestSha256":source_sha,"buildRecipeSha256":recipe_sha,
            "cargoLockSha256":lock_sha,"rustTarget":"armv7-unknown-linux-uclibceabihf",
            "compilerRustVersion":"1.82.0","pythonAbi3Minimum":"3.11","libc":"uclibc"}

def stage(output, variant="production", kernel_probe=False, memory_profile="none", lcd_backend="python", io_profile="carrier", app_startup=None, frontend_backend="python"):
    if frontend_backend not in ("python", "rust") or (frontend_backend == "rust" and lcd_backend != "rust"):
        raise ValueError("Native frontend requires the Rust extension package (lcd-backend rust)")
    app_startup = app_startup or ("held" if variant == "dev" else "automatic")
    if app_startup not in ("automatic", "held"):
        raise ValueError("Unknown app startup policy")
    if io_profile not in ("carrier", "base-fork"):
        raise ValueError("Unknown IO profile")
    if lcd_backend not in ("python", "rust"):
        raise ValueError("Unknown LCD backend")
    if memory_profile not in ("none", "zram16-lzo"):
        raise ValueError("Unknown camera image memory profile")
    if output.exists():
        raise ValueError("Choose a new immutable bundle directory: " + str(output))
    version = re.search(r'^version = "([^"]+)"', (ROOT / "firmware/rkaiq-rs/Cargo.toml").read_text(), re.M).group(1)
    binaries = {
        "camera-probe": ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/camera-probe",
        "shieldsigner-qr-reader": ROOT / "dist/reverse-engineering/qr-native-build/cmake/shieldsigner-qr-reader",
    }
    for path in binaries.values():
        validate_static_arm(path)
    files = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="camera-bundle-", dir=output.parent) as temporary:
        staged = Path(temporary)

        def add(name, contents, mode=0o644):
            path = staged / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            path.chmod(mode)
            files[name] = {"sha256": digest(path), "bytes": path.stat().st_size, "mode": mode}

        for name, path in binaries.items():
            add("payload/" + name, path.read_bytes(), 0o755)
        for name in ["shieldsigner_integration.py", "shieldsigner_video_stream.py",
                     "shieldsigner_qr_decoder.py", "shieldsigner_camera_compat.py",
                     "shieldsigner_process_log.py", "shieldsigner_native_stream.py",
                     "shieldsigner_native_camera.py"]:
            add("payload/python/" + name, (ROOT / "firmware/rkaiq-rs/python" / name).read_bytes())
        add("payload/pipeline.json", (ROOT / "reverse-engineering/rkaiq/examples/pipeline-luckfox-sc3336-observed.json").read_bytes())
        proof_name = "image-sdk-kernel-abi-development-validation.json" if variant == "dev" and not kernel_probe else "image-sdk-kernel-abi-validation.json"
        if memory_profile == "zram16-lzo" and not kernel_probe:
            proof_name = "image-sdk-kernel-abi-development-zram-validation.json" if variant == "dev" else "image-sdk-kernel-abi-zram-validation.json"
        if io_profile == "base-fork" and not kernel_probe:
            proof_name = proof_name.replace("-validation.json", "-base-fork-validation.json")
        proof_bytes = (ROOT / "reverse-engineering/rkaiq" / proof_name).read_bytes()
        validate_memory_proof(json.loads(proof_bytes), memory_profile, kernel_probe)
        validate_io_proof(json.loads(proof_bytes), io_profile, kernel_probe)
        add("payload/kernel-camera-abi.json", proof_bytes)
        if memory_profile == "zram16-lzo":
            add("zram-image-profile.py", (ROOT / "scripts/image-profiles/zram-image-profile.py").read_bytes())
            for name in ["S20zram", "enable-zram-image.sh.in"]:
                add("image-profiles/" + name, (ROOT / "scripts/image-profiles" / name).read_bytes())
        add("configure-image-io-profile.py", (ROOT / "scripts/configure-image-io-profile.py").read_bytes())
        if io_profile == "base-fork":
            add("base-fork-io-config.json", (ROOT / "firmware/bench-profiles/base-fork-io-config.json").read_bytes())
        add("collect-kernel-probe.py", (ROOT / "scripts/collect-image-kernel-probe.py").read_bytes())
        owner = {"binary": INSTALL + "/camera-probe", "plan": INSTALL + "/pipeline.json",
                 "iq": "/oem/usr/share/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json",
                 "parameters": "/dev/video20", "image": "/dev/video11", "statistics": "/dev/video19",
                 "output_directory": "/tmp/shieldsigner-camera"}
        add("payload/owner.json", (json.dumps(owner, indent=2) + "\n").encode())
        modules = (ROOT / "reverse-engineering/rkaiq/scripts/cold-camera-modules.sh").read_text()
        modules = modules.replace("udevadm settle --timeout=10", '''if command -v udevadm >/dev/null 2>&1; then
  udevadm settle --timeout=10
else
  mdev -s
fi''')
        add("payload/cold-camera-modules.sh", modules.encode(), 0o755)
        add("payload/licenses/ShieldSigner-MIT.txt", (ROOT / "LICENSE").read_bytes())
        add("payload/licenses/ZXing-Apache-2.0.txt", (ROOT / ".tools/zxing-cpp-3.1.1/LICENSE").read_bytes())
        notices = staged / "runtime-notices"
        subprocess.run(["uv", "run", "--python", "3.13", "python",
                        str(ROOT / "reverse-engineering/rkaiq/scripts/collect-runtime-notices.py"),
                        "--output", str(notices)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        for path in sorted(notices.rglob("*")):
            if path.is_file():
                add("payload/licenses/runtime/" + str(path.relative_to(notices)), path.read_bytes())
        shutil.rmtree(notices)
        add("dependencies.json", (ROOT / "scripts/camera-image-dependencies.json").read_bytes())
        dependency_lock = json.loads((ROOT / "scripts/camera-image-dependencies.json").read_text())
        for name, sha in dependency_lock["licenseSha256"].items():
            path = ROOT / "scripts/image-licenses/pycryptodomex-3.23.0" / name
            if digest(path) != sha:
                raise ValueError("Image dependency license hash mismatch: " + name)
            add("payload/licenses/pycryptodomex-3.23.0/" + name, path.read_bytes())
        add("configure-hothmi-display.py", (ROOT / "scripts/configure-hothmi-display.py").read_bytes())
        add("image-overlay.py", (ROOT / "scripts/camera-image-overlay.py").read_bytes(), 0o755)
        if frontend_backend == "rust":
            add("native-frontend-smoke.py", (ROOT/"scripts/image-profiles/native-frontend-smoke.py").read_bytes())
        lcd_inputs = stage_lcd_inputs(staged, add) if lcd_backend == "rust" else None
        source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        manifest = {"kind": "shieldsigner-camera-image-bundle", "version": version,
                    "imageVariant": variant, "appStartup": app_startup, "kernelProofPending": kernel_probe, "cameraCmaSize": "12M",
                    "memoryProfile": memory_profile, "frontendBackend": frontend_backend, "lcdBackend": lcd_backend, "lcdInputs": lcd_inputs, "ioProfile": io_profile,
                    "memoryRuntimePolicy": ({"smallRam": True, "nativeReadOnlyCodeLock": True, "memlockLimitKiB": 4096} if memory_profile == "zram16-lzo" else None),
                    "sourceCommit": source_commit, "sourceDirty": dirty,
                    "applicationCommit": "efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f",
                    "osCommit": "e7589465aff172f4f510ad46d18776ccc8d2c203",
                    "zxingCommit": "287c85df6f961c8efbfb5ffd736cd9457b8b890e",
                    "qualification": "Development snapshot. File hashes establish contents, not a physical image boot or final release qualification.",
                    "files": files}
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copytree(staged, output)
    return manifest


def verify(bundle):
    result = json.loads((bundle / "manifest.json").read_text())
    frontend = result.get("frontendBackend", "python")
    if frontend not in ("python", "rust") or (frontend == "rust" and result.get("lcdBackend") != "rust"):
        raise ValueError("Invalid frontend/extension package selection")
    for name, info in result["files"].items():
        path = bundle / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink():
            raise ValueError("Unsafe camera bundle entry")
        if digest(path) != info["sha256"]:
            raise ValueError("Camera bundle hash mismatch: " + name)
    for name in ["camera-probe", "shieldsigner-qr-reader"]:
        validate_static_arm(bundle / "payload" / name)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    parser.add_argument("--variant", choices=["production", "dev"], default="production")
    parser.add_argument("--kernel-probe", action="store_true")
    parser.add_argument("--memory-profile", choices=["none", "zram16-lzo"], default="none")
    parser.add_argument("--lcd-backend", choices=["python", "rust"], default="python")
    parser.add_argument("--frontend-backend", choices=["python", "rust"], default="python")
    parser.add_argument("--io-profile", choices=["carrier", "base-fork"], default="carrier")
    parser.add_argument("--app-startup", choices=["automatic", "held"], help="Default: held for dev, automatic for production")
    args = parser.parse_args()
    print(json.dumps(stage(args.output.resolve(), args.variant, args.kernel_probe, args.memory_profile, args.lcd_backend, args.io_profile, args.app_startup, args.frontend_backend) if args.output else verify(args.verify.resolve()), indent=2))
