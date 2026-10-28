#!/usr/bin/env python3
"""Install/verify the immutable camera bundle inside a staged Luckfox rootfs.

Runs on the Linux image builder, never on the signing device. OEM cleanup is
also invoked after the SDK stages vendor media files, before squashfs packing.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

INSTALL = "usr/lib/shieldsigner-camera"
IQ = "oem/usr/share/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
FORBIDDEN = ("librkaiq*", "librockit*", "librkrawstream*", "librkpostisp*", "librkyuvscaler*",
             "rkipc", "rkaiq_3A_server", "rkaiq_tool_server", "rkaiq-service", "RkLunch.sh",
             "RkLunch-stop.sh", "nv12_converter", "rockit.ko")
CAMERA_MODULES = ("rk_dvbm", "video_rkcif", "video_rkisp", "sc3336",
                  "phy-rockchip-csi2-dphy-hw", "phy-rockchip-csi2-dphy")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(bundle):
    data = json.loads((bundle / "manifest.json").read_text())
    for name, info in data["files"].items():
        path = bundle / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink():
            raise ValueError("Unsafe bundle entry")
        if digest(path) != info["sha256"]:
            raise ValueError("Camera bundle checksum mismatch: " + name)
    return data


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Unexpected pinned startup script shape: " + before[:60])
    return text.replace(before, after, 1)


def strip_vendor(tree):
    removed = []
    for pattern in FORBIDDEN:
        for path in sorted(tree.rglob(pattern)):
            if path.is_file() or path.is_symlink():
                removed.append(str(path.relative_to(tree)))
                path.unlink()
    return sorted(set(removed))


def validate_app(root, bundle):
    path = bundle / "payload/python/shieldsigner_integration.py"
    spec = importlib.util.spec_from_file_location("image_camera_integration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    camera, _, _ = module.camera_source(root / "opt/src")
    return {"cameraSourceSha256": digest(camera), "cameraSource": str(camera.relative_to(root))}


def configure_buildroot(buildroot, bundle):
    lock = json.loads((bundle / "dependencies.json").read_text())
    recipe = buildroot / "package/python-pycryptodomex/python-pycryptodomex.mk"
    hashes = recipe.with_suffix(".hash")
    original = recipe.read_text()
    old_site = "https://files.pythonhosted.org/packages/11/dc/e66551683ade663b5f07d7b3bc46434bf703491dbd22ee12d1f979ca828f"
    if digest(recipe) == lock["originalRecipeSha256"]:
        modified = replace_once(original, "PYTHON_PYCRYPTODOMEX_VERSION = 3.21.0", "PYTHON_PYCRYPTODOMEX_VERSION = " + lock["version"])
        modified = replace_once(modified, old_site, lock["site"])
    else:
        restored = original.replace("PYTHON_PYCRYPTODOMEX_VERSION = " + lock["version"], "PYTHON_PYCRYPTODOMEX_VERSION = 3.21.0").replace(lock["site"], old_site)
        if hashlib.sha256(restored.encode()).hexdigest() != lock["originalRecipeSha256"]:
            raise ValueError("Unreviewed pycryptodomex Buildroot recipe")
        modified = original
    content = "# Source pinned to the application requirement, verified against PyPI sdist.\n"
    content += "sha256  " + lock["sha256"] + "  " + lock["source"] + "\n"
    content += "# License checksums from the verified source archive.\n"
    content += "".join("sha256  " + sha + "  " + name + "\n" for name, sha in lock["licenseSha256"].items())
    if digest(hashes) != lock["originalHashFileSha256"] and hashes.read_text() != content:
        raise ValueError("Unreviewed pycryptodomex Buildroot hash file")
    recipe.write_text(modified)
    hashes.write_text(content)
    receipt = {"kind": "shieldsigner-image-python-dependency-input", "package": lock["package"],
               "version": lock["version"], "source": lock["source"], "sourceSha256": lock["sha256"],
               "recipeSha256": digest(recipe), "hashFileSha256": digest(hashes)}
    target = buildroot / "output/shieldsigner-dependency-inputs.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def kernel_inputs(bundle):
    proof = json.loads((bundle / "payload/kernel-camera-abi.json").read_text())
    sdk = Path(os.environ["SHIELDSIGNER_CAMERA_SDK_DIR"])
    revision = subprocess.check_output(["git", "-C", str(sdk), "rev-parse", "HEAD"], text=True).strip()
    config = sdk / "sysdrv/source/objs_kernel/.config"
    dtb = sdk / "sysdrv/out/bin/board_uclibc_rv1106/rv1103g-luckfox-pico-mini.dtb"
    if revision != proof["sdkRevision"] or digest(config) != proof["kernelConfigSha256"]:
        raise ValueError("Image kernel inputs differ from the reviewed actual SDK ABI proof")
    if digest(dtb) != proof["compiledDtbSha256"]:
        raise ValueError("Image compiled Mini DTB differs from reviewed model/ISP/sensor graph")
    return {"sdkRevision": revision, "kernelVersion": proof["kernelVersion"],
            "kernelConfigSha256": digest(config), "compiledDtbSha256": digest(dtb),
            "compiledDtbModel": proof["compiledDtbModel"],
            "builtinVideoBufferModules": ["videobuf2-common", "videobuf2-memops", "videobuf2-v4l2",
                                           "videobuf2-vmalloc", "videobuf2-cma-sg"]}


def install(root, bundle, data):
    app = validate_app(root, bundle)
    display_spec = importlib.util.spec_from_file_location("image_display_config", bundle / "configure-hothmi-display.py")
    display_module = importlib.util.module_from_spec(display_spec)
    display_spec.loader.exec_module(display_module)
    display_config = root / "opt/src/seedsigner/hardware/io_config.json"
    display_module.configure(display_config)
    destination = root / INSTALL
    destination.mkdir(parents=True, exist_ok=True)
    for name, info in data["files"].items():
        if not name.startswith("payload/"):
            continue
        target = destination / name[len("payload/"):]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundle / name, target)
        target.chmod(info["mode"])
    lock = json.loads((bundle / "dependencies.json").read_text())
    buildroot = Path(os.environ["SHIELDSIGNER_CAMERA_BUILDROOT_DIR"])
    if not (buildroot / "output/build" / (lock["package"] + "-" + lock["version"]) / ".stamp_target_installed").is_file():
        raise ValueError("Pinned pycryptodomex package was not installed by Buildroot")
    receipt = buildroot / "output/shieldsigner-dependency-inputs.json"
    shutil.copyfile(receipt, destination / "python-dependency-build.json")
    startup = root / "start-seedsigner.sh"
    text = startup.read_text()
    for function in ["start_camera_service", "stop_camera_service", "start_camera_service_later", "bootstrap_camera_graph"]:
        text = replace_once(text, function + "() {", function + "() {\n    [ ! -f /etc/shieldsigner-rust-camera ] || return 0")
    text = replace_once(text, '    python -u main.py >>"$APP_LOG" 2>&1 &',
                        '    /usr/bin/shieldsigner-launch >>"$APP_LOG" 2>&1 &')
    startup.write_text(text)
    startup.chmod(0o755)
    marker = root / "etc/shieldsigner-rust-camera"
    marker.write_text(data["version"] + "\n")
    os_release = root / "etc/seedsigner-os-release"
    identity = os_release.read_text() if os_release.exists() else ""
    if "SHIELDSIGNER_CAMERA_VERSION=" in identity:
        raise ValueError("Camera identity already present in staged OS release")
    identity += '\nSHIELDSIGNER_CAMERA_VERSION="' + data["version"] + '"\n'
    identity += 'SHIELDSIGNER_CAMERA_BUNDLE_SHA256="' + digest(bundle / "manifest.json") + '"\n'
    os_release.write_text(identity)
    init = root / "etc/init.d/S21appinit"
    init.write_text('''#!/bin/sh
# Open kernel camera drivers only. Capture/AE/AWB starts when the app opens Camera.
case "${1:-start}" in
  start|restart) /usr/lib/shieldsigner-camera/cold-camera-modules.sh ;;
  stop) : ;;
  *) exit 1 ;;
esac
''')
    init.chmod(0o755)
    launcher = root / "usr/bin/shieldsigner-launch"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text('''#!/bin/sh
set -eu
umask 077
mkdir -p /tmp/shieldsigner-camera
/usr/lib/shieldsigner-camera/cold-camera-modules.sh
unset SHIELDSIGNER_CAMERA_STREAM_FORMAT
export PYTHONPATH=/usr/lib/shieldsigner-camera/python${PYTHONPATH:+:$PYTHONPATH}
export SHIELDSIGNER_QR_READER=/usr/lib/shieldsigner-camera/shieldsigner-qr-reader
cd /opt/src
exec python3 -u /usr/lib/shieldsigner-camera/python/shieldsigner_integration.py \\
  --app-root /opt/src --config /usr/lib/shieldsigner-camera/owner.json \\
  --qr-reader /usr/lib/shieldsigner-camera/shieldsigner-qr-reader "$@"
''')
    launcher.chmod(0o755)
    removed = strip_vendor(root)
    changes = [startup, init, launcher, marker, display_config, os_release]
    record = {"kind": "shieldsigner-rust-camera-rootfs-install", "version": data["version"],
              "bundleManifestSha256": digest(bundle / "manifest.json"), **app,
              "kernelInputs": kernel_inputs(bundle),
              "startupSha256": {str(path.relative_to(root)): digest(path) for path in changes},
              "removedVendorRuntime": removed, "displaySpiHz": 10_000_000, "imageBootQualified": False}
    (destination / "image-installation.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def verify(root, bundle, data):
    record = json.loads((root / INSTALL / "image-installation.json").read_text())
    proof = json.loads((bundle / "payload/kernel-camera-abi.json").read_text())
    for field in ["sdkRevision", "kernelVersion", "kernelConfigSha256", "compiledDtbSha256", "compiledDtbModel"]:
        if record["kernelInputs"][field] != proof[field]:
            raise ValueError("Installed kernel provenance differs from reviewed SDK proof: " + field)
    if os.environ.get("SHIELDSIGNER_CAMERA_SDK_DIR") and record["kernelInputs"] != kernel_inputs(bundle):
        raise ValueError("Kernel inputs changed during image assembly")
    for name, info in data["files"].items():
        if name.startswith("payload/"):
            if digest(root / INSTALL / name[len("payload/"):]) != info["sha256"]:
                raise ValueError("Installed camera asset changed: " + name)
    for name, expected in record["startupSha256"].items():
        if digest(root / name) != expected:
            raise ValueError("Installed Rust startup changed: " + name)
    leftovers = [str(path.relative_to(root)) for pattern in FORBIDDEN for path in root.rglob(pattern)
                 if path.is_file() or path.is_symlink()]
    if leftovers:
        raise ValueError("Closed camera userspace survived image staging: " + ", ".join(leftovers))
    if not (root / IQ).is_file():
        raise ValueError("Selected SC3336 IQ calibration JSON missing")
    modules = []
    for name in CAMERA_MODULES:
        path = root / "oem/usr/ko" / (name + ".ko")
        raw = path.read_bytes()
        if raw[:6] != b"\x7fELF\x01\x01" or struct.unpack_from("<H", raw, 18)[0] != 40:
            raise ValueError("Camera kernel module is not ARM ELF: " + name)
        offset = raw.find(b"vermagic=")
        if offset < 0:
            raise ValueError("Kernel module has no version magic: " + name)
        magic = raw[offset+9:].split(b"\0", 1)[0].decode("ascii")
        if not magic.startswith("5.10.160 "):
            raise ValueError("Kernel module version differs from reviewed SDK: " + name)
        modules.append({"name": name, "sha256": digest(path), "vermagic": magic})
    if len({row["vermagic"] for row in modules}) != 1:
        raise ValueError("Camera modules have inconsistent kernel version magic")
    dependency = json.loads((root / INSTALL / "python-dependency-build.json").read_text())
    lock = json.loads((bundle / "dependencies.json").read_text())
    if dependency["version"] != lock["version"] or dependency["sourceSha256"] != lock["sha256"]:
        raise ValueError("Image Python dependency receipt does not match its locked source")
    display = json.loads((root / "opt/src/seedsigner/hardware/io_config.json").read_text())
    fox22 = [model for model in display["models"] if model.get("shortname") == "FOX_22"]
    if len(fox22) != 1 or fox22[0]["display"].get("spi_hz") != 10_000_000:
        raise ValueError("Reviewed HOTHMI SPI clock missing from image")
    validate_app(root, bundle)
    return {"kind": "shieldsigner-rust-camera-rootfs-verified", "version": data["version"],
            "bundleManifestSha256": digest(bundle / "manifest.json"), "closedCameraRuntimeAbsent": True,
            "selectedIqPresent": True, "openKernelModulesPresent": True,
            "moduleFiles": modules, "imageBootQualified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rootfs", type=Path)
    group.add_argument("--oem", type=Path)
    group.add_argument("--verify", type=Path)
    group.add_argument("--buildroot", type=Path)
    args = parser.parse_args()
    bundle = Path(__file__).resolve().parent
    data = manifest(bundle)
    if args.buildroot:
        result = configure_buildroot(args.buildroot.resolve(), bundle)
    elif args.oem:
        result = {"kind": "shieldsigner-rust-camera-oem-cleanup", "removed": strip_vendor(args.oem.resolve())}
    elif args.rootfs:
        result = install(args.rootfs.resolve(), bundle, data)
    else:
        result = verify(args.verify.resolve(), bundle, data)
    print(json.dumps(result, indent=2))
