"""Pass only when a real camera frame decodes the supplied public QR target."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from shieldsigner_integration import install_camera_backend

PUBLIC_TARGET = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        parser.error("--seconds must be between 1 and 3600")
    if args.report.exists():
        parser.error("Report already exists; choose a new filename")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config).resolve()
    with config_path.open() as source:
        config = json.load(source)
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(config_path)
    module = install_camera_backend(args.app_root)
    from seedsigner.models.decode_qr import DecodeQR, DecodeQRStatus
    camera = module.Camera.get_instance()
    report = {"kind": "known-public-target-optical-camera-check", "matched": False,
              "opticalScanQualified": False, "framesExamined": 0, "otherCompletedOrInvalid": 0,
              "cameraBinarySha256": hashlib.sha256(Path(config["binary"]).read_bytes()).hexdigest(),
              "integration": module.__shieldsigner_camera_patch__,
              "scope": "One known public static address through real camera, ISP, Rust controls and installed DecodeQR; no synthetic image input"}
    started = time.monotonic()
    reader = None
    code = 2
    try:
        camera.start_video_stream_mode()
        reader = camera._video_stream
        last_sequence = None
        while time.monotonic() - started < args.seconds:
            frame = camera.read_video_stream()
            if frame is None or reader.sequence == last_sequence:
                time.sleep(.01)
                continue
            last_sequence = reader.sequence
            report["framesExamined"] += 1
            decoder = DecodeQR()
            status = decoder.add_image(frame)
            if status == DecodeQRStatus.COMPLETE and decoder.get_address() == PUBLIC_TARGET:
                report["matched"] = report["opticalScanQualified"] = True
                report["matchAfterSeconds"] = time.monotonic() - started
                code = 0
                break
            if status in (DecodeQRStatus.COMPLETE, DecodeQRStatus.INVALID):
                # Never report unrelated QR contents or seed/wallet payloads.
                report["otherCompletedOrInvalid"] += 1
    except KeyboardInterrupt:
        report["interrupted"] = True
        code = 130
    except Exception as exc:
        report["errorType"] = type(exc).__name__
        code = 1
    finally:
        try:
            camera.stop_video_stream_mode()
        except Exception as exc:
            report["cleanupErrorType"] = type(exc).__name__
            code = 1
        if reader is not None:
            report["sessionDirectory"] = reader.session_directory
            report["ownerExitCode"] = reader.owner_exit_code
        report["passed"] = code == 0 and report["matched"]
        report["durationSeconds"] = time.monotonic() - started
        with args.report.open("x") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    print(json.dumps(report))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
