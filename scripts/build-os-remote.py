#!/usr/bin/env python3
"""Build/stage public runtime inputs and launch the documented Proxmox image job."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import tempfile

from firmware_paths import ROOT, OS_WORK, STAGING, JOBS
SCRIPTS = ["build-os.sh", "configure-os-reader.py", "configure-os-camera.py",
           "prepare-camera-image.py", "camera-image-overlay.py", "run-os-image-job.sh",
           "firmware_paths.py"]


def run(*args, **kwargs):
    return subprocess.run([str(x) for x in args], cwd=ROOT, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("SHIELDSIGNER_BUILD_HOST"))
    parser.add_argument("--bundle", type=Path, default=os.environ.get("SHIELDSIGNER_CAMERA_BUNDLE"))
    parser.add_argument("--variant", choices=["production", "dev"], default=os.environ.get("SHIELDSIGNER_IMAGE_VARIANT", "production"))
    parser.add_argument("--kernel-probe", action="store_true", help="Stop after compiled kernel/config snapshot, before rootfs; no image")
    parser.add_argument("--name", help="Unique output name; existing attempts are never overwritten")
    args = parser.parse_args()
    if not args.host:
        parser.error("Set SHIELDSIGNER_BUILD_HOST or pass --host (documented SSH builder)")
    if args.host.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_.@:-]+", args.host):
        parser.error("Use an SSH host alias or user@host")
    if args.name and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.name):
        parser.error("Output name must start with a letter/digit and contain only letters, digits, dots, dashes and underscores")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not args.bundle:
        run("mise", "run", "camera:rust:arm")
        run("mise", "run", "camera:qr:native-build")
        args.bundle = STAGING / (args.name or stamp) / "camera-bundle"
        run("uv", "run", "--python", "3.13", "python", "scripts/prepare-camera-image.py",
            "--output", args.bundle, "--variant", args.variant, *(["--kernel-probe"] if args.kernel_probe else []))
    args.bundle = args.bundle.resolve()
    run("uv", "run", "--python", "3.13", "python", "scripts/prepare-camera-image.py",
        "--verify", args.bundle, stdout=subprocess.DEVNULL)
    manifest = json.loads((args.bundle / "manifest.json").read_text())
    if manifest.get("imageVariant", "production") != args.variant:
        parser.error("Bundle variant differs from requested image variant")
    if bool(manifest.get("kernelProofPending")) != args.kernel_probe:
        parser.error("Kernel-probe mode must match its explicitly probe-only bundle")
    sha = hashlib.sha256((args.bundle / "manifest.json").read_bytes()).hexdigest()
    name = args.name or ("rust-" + manifest["version"] + "-" + stamp)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        parser.error("Output name may contain only letters, digits, dots, dashes and underscores")
    remote_archive = "/tmp/shieldsigner-image-" + sha[:16] + ".tar.gz"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", args.host]
    # A live legacy runner might predate our flock. Check Docker before sending.
    preflight = '''set -eu
export PATH=/usr/local/bin:$PATH
command -v uv >/dev/null
if docker ps --format '{{.Names}}' | grep -q '^seedsigner-build-'; then
  echo 'An SDK image build is already running; preserve it and retry after it finishes' >&2
  exit 2
fi
'''
    run(*ssh, "pct exec 610 -- bash -s", input=preflight, text=True)
    OS_WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="image-transfer-", dir=OS_WORK) as temporary:
        archive = Path(temporary) / "payload.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(ROOT / "scripts", arcname="scripts", recursive=False)
            tar.add(args.bundle, arcname="camera-bundle", recursive=False)
            for script in SCRIPTS:
                tar.add(ROOT / "scripts" / script, arcname="scripts/" + script)
            tar.add(args.bundle / "manifest.json", arcname="camera-bundle/manifest.json")
            for entry in manifest["files"]:
                tar.add(args.bundle / entry, arcname="camera-bundle/" + entry)
        run("scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", archive,
            args.host + ":" + remote_archive)
    guest_root = Path("/opt/shieldsigner-build")
    guest_work = guest_root / OS_WORK.relative_to(ROOT)
    guest_archive = str(guest_work / "transfers" / (sha[:16] + ".tar.gz"))
    run(*ssh, "pct exec 610 -- mkdir -p " + shlex.quote(str(Path(guest_archive).parent)))
    run(*ssh, "pct push 610 " + shlex.quote(remote_archive) + " " + shlex.quote(guest_archive))
    run(*ssh, "rm -f " + shlex.quote(remote_archive))
    output = str(guest_work / name)
    bundle_path = str(guest_root / STAGING.relative_to(ROOT) / name / "camera-bundle")
    launch = '''set -eu
export PATH=/usr/local/bin:$PATH
cd /opt/shieldsigner-build
mkdir -p dist
exec 9>dist/os-image-build.lock
flock -n 9 || { echo 'Another image job owns the workspace/cache' >&2; exit 2; }
if docker ps --format '{{.Names}}' | grep -q '^seedsigner-build-'; then exit 2; fi
test ! -e @OUTPUT@
test ! -e @BUNDLE@
mkdir -p @OUTPUT@ @BUNDLE@
tar -xzf @ARCHIVE@ -C /opt/shieldsigner-build scripts
tar -xzf @ARCHIVE@ -C @BUNDLE@ --strip-components=1 camera-bundle
uv run --python 3.13 python scripts/prepare-camera-image.py --verify @BUNDLE@ >/dev/null
rm -f @ARCHIVE@
nohup env SHIELDSIGNER_IMAGE_LOCK_INHERITED=1 SHIELDSIGNER_BUILD_JOBS=6 \\
 SHIELDSIGNER_IMAGE_VARIANT=@VARIANT@ SHIELDSIGNER_KERNEL_PROBE_ONLY=@PROBE@ \\
 SHIELDSIGNER_OUTPUT_DIR=@OUTPUT@ SHIELDSIGNER_CAMERA_BUNDLE=@BUNDLE@ \\
 bash scripts/run-os-image-job.sh > @OUTPUT@/launcher.log 2>&1 < /dev/null &
pid=$!
printf '%s\\n' "$pid" > @OUTPUT@/launcher.pid
printf '{"pid":%s}\\n' "$pid"
'''
    for token, value in [("@OUTPUT@", output), ("@BUNDLE@", bundle_path), ("@ARCHIVE@", guest_archive), ("@VARIANT@", args.variant), ("@PROBE@", "1" if args.kernel_probe else "0")]:
        launch = launch.replace(token, shlex.quote(value))
    result = subprocess.check_output([*ssh, "pct exec 610 -- bash -s"], input=launch, text=True)
    job = {"kind": "shieldsigner-remote-image-job", "name": name, "artifactLayout": 1, "bundleManifestSha256": sha,
           "remoteOutput": output, "remoteBundle": bundle_path, "imageVariant": args.variant, "kernelProbeOnly": args.kernel_probe, "launcher": json.loads(result.strip().splitlines()[-1]),
           "scope": "Started only; inspect actual process/Docker and exit-code before claiming success"}
    destination = JOBS / (name + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(job, indent=2) + "\n")
    print(json.dumps(job, indent=2))


if __name__ == "__main__":
    main()
