"""Strict real-camera public-target optical check through the pinned image app.

Reuses optical_camera_check's unchanged live-frame/content check. Adds only
explicit board profile selection, native-worker selection and source/cleanup
evidence. No synthetic frame, preprocessing replacement or app-file edit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from shieldsigner_integration import install_camera_backend
import optical_camera_check


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("app-root", "config", "reader", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--runtime-profile", choices=["luckfox_22", "luckfox_40", "luckfox_pi"], default="luckfox_22")
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    app_root = args.app_root.resolve()
    config = args.config.resolve()
    report_path = args.report.resolve()
    reader = args.reader.resolve()
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(config)
    os.environ["SHIELDSIGNER_QR_READER"] = str(reader)
    sources = [app_root / "seedsigner" / name for name in
               ("hardware/camera.py", "models/decode_qr.py")]
    before = {str(path.relative_to(app_root)): digest(path) for path in sources}
    module = install_camera_backend(app_root)
    client = module.__shieldsigner_qr_client__
    from seedsigner.models.settings import Settings
    Settings.RUNTIME_PROFILE = args.runtime_profile
    old_argv = sys.argv
    try:
        sys.argv = ["optical_camera_check.py", "--app-root", str(app_root), "--config", str(config),
                    "--report", str(report_path), "--seconds", str(args.seconds)]
        code = optical_camera_check.main()
    finally:
        client.close()
        sys.argv = old_argv
    report = json.loads(report_path.read_text())
    report.update(kind="pinned-image-native-public-target-optical-check",
                  expectedPublicTarget=optical_camera_check.PUBLIC_TARGET,
                  runtimeProfileOverride=args.runtime_profile,
                  nativeQrBinarySha256=digest(reader),
                  appSourcesSha256=before,
                  installedSourcesUnchanged=before == {str(path.relative_to(app_root)): digest(path) for path in sources},
                  nativeWorkerClosed=client._process is None,
                  nativeQrStats=dict(client.stats),
                  helperSha256=digest(__file__),
                  strictOpticalHelperSha256=digest(optical_camera_check.__file__),
                  limitations=["One physical known-public static address and current scene only; no synthetic input.",
                               "Explicit runtime-profile override does not qualify image/device-tree autodetection.",
                               "No physical LCD/buttons, image flashing, power cycle or broad lighting qualification."])
    report["passed"] &= (report["installedSourcesUnchanged"] and report["nativeWorkerClosed"]
                         and client.stats["errors"] == 0 and report["ownerExitCode"] == 0)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return code if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
