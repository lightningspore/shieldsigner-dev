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


def stage(output):
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
                     "shieldsigner_process_log.py"]:
            add("payload/python/" + name, (ROOT / "firmware/rkaiq-rs/python" / name).read_bytes())
        add("payload/pipeline.json", (ROOT / "reverse-engineering/rkaiq/examples/pipeline-luckfox-sc3336-observed.json").read_bytes())
        add("payload/kernel-camera-abi.json", (ROOT / "reverse-engineering/rkaiq/image-sdk-kernel-abi-validation.json").read_bytes())
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
        source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        manifest = {"kind": "shieldsigner-camera-image-bundle", "version": version,
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
    args = parser.parse_args()
    print(json.dumps(stage(args.output.resolve()) if args.output else verify(args.verify.resolve()), indent=2))
