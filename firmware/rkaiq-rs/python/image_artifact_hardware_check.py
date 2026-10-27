"""Verify streaming's default no-image policy and explicit diagnostic opt-in."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from shieldsigner_video_stream import PiVideoStream


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    report = {
        "passed": False,
        "cases": [],
        "binarySha256": hashlib.sha256(Path(config["binary"]).read_bytes()).hexdigest(),
    }
    previous = os.environ.pop("SHIELDSIGNER_CAMERA_SAVE_IMAGE", None)
    try:
        for diagnostic in (False, True):
            if diagnostic:
                os.environ["SHIELDSIGNER_CAMERA_SAVE_IMAGE"] = "1"
            else:
                os.environ.pop("SHIELDSIGNER_CAMERA_SAVE_IMAGE", None)
            reader = PiVideoStream(owner_config=config).start()
            seen = []
            started = time.monotonic()
            try:
                while len(seen) < 8:
                    frame = reader.read()
                    if frame is not None:
                        assert frame.size == (640, 480)
                        if not seen or seen[-1] != reader.sequence:
                            seen.append(reader.sequence)
                    if time.monotonic() - started > 15:
                        raise TimeoutError(
                            "No live frames for image-artifact policy test"
                        )
                    time.sleep(0.02)
            finally:
                reader.stop()
            assert reader.owner_exit_code == 0 and not Path(reader.socket_path).exists()
            base = Path(reader.session_directory) / "frame"
            metadata = json.loads(base.with_suffix(".json").read_text())
            assert metadata["sceneImageSaved"] is diagnostic
            assert base.exists() is diagnostic
            if diagnostic:
                assert base.stat().st_size == metadata["bytes"] == 460800
            report["cases"].append(
                {
                    "diagnosticImageRequested": diagnostic,
                    "imageFileExists": base.exists(),
                    "reportedSceneImageSaved": metadata["sceneImageSaved"],
                    "liveFrames": len(seen),
                    "ownerExitCode": reader.owner_exit_code,
                    "directory": reader.session_directory,
                }
            )
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        if previous is None:
            os.environ.pop("SHIELDSIGNER_CAMERA_SAVE_IMAGE", None)
        else:
            os.environ["SHIELDSIGNER_CAMERA_SAVE_IMAGE"] = previous
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
