"""Real camera + installed ScanScreen loops, with headless display/software cancel."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import threading
import time

from shieldsigner_integration import install_camera_backend


def main():
    parser = argparse.ArgumentParser()
    for name in ("app-root", "config", "report"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(Path(args.config).resolve())
    module = install_camera_backend(args.app_root)
    os.chdir(args.app_root)
    from seedsigner.gui.screens.scan_screens import ScanScreen
    from seedsigner.models.decode_qr import DecodeQR
    from seedsigner.models.threads import ThreadsafeCounter

    class Renderer:
        canvas_width = 240
        canvas_height = 240
        lock = threading.Lock()
        frames = 0

        def show_image(self, image, show_direct=False):
            assert show_direct and image.size == (240, 240)
            self.frames += 1
            # Bound the headless sink to a plausible display rate.
            time.sleep(0.03)

    class Decoder(DecodeQR):
        frames = 0

        def add_image(self, image):
            self.frames += 1
            return super().add_image(image)

    class SoftwareCancel:
        def check_for_low(self, key):
            return time.monotonic() >= deadline

    report = {
        "passed": False,
        "opticalScanQualified": False,
        "physicalDisplayQualified": False,
        "physicalButtonsQualified": False,
        "scanSourceSha256": hashlib.sha256(
            (
                Path(args.app_root) / "seedsigner/gui/screens/scan_screens.py"
            ).read_bytes()
        ).hexdigest(),
    }
    config = json.loads(Path(args.config).read_text())
    report["binarySha256"] = hashlib.sha256(
        Path(config["binary"]).read_bytes()
    ).hexdigest()
    report["helperSha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    errors = []
    old_hook = threading.excepthook
    threading.excepthook = lambda event: errors.append(str(event.exc_value))
    camera = module.Camera.get_instance()
    preview = None
    try:
        camera.start_video_stream_mode()
        reader = camera._video_stream
        screen = ScanScreen.__new__(ScanScreen)
        screen.camera = camera
        screen.decoder = Decoder()
        screen.frames_decode_status = ThreadsafeCounter()
        screen.frames_decoded_counter = ThreadsafeCounter()
        screen.hw_inputs = SoftwareCancel()
        sink = Renderer()
        preview = ScanScreen.LivePreviewThread(
            screen.decoder,
            sink,
            "Camera integration test",
            None,
            screen.frames_decode_status,
            screen.frames_decoded_counter,
        )
        screen.threads = [preview]
        deadline = time.monotonic() + 6
        started = time.monotonic()
        preview.start()
        screen._run()
        preview.stop()
        preview.join(timeout=3)
        assert not preview.is_alive() and not errors
        assert screen.decoder.frames >= 10 and sink.frames >= 10
        assert reader.owner_exit_code == 0 and camera._video_stream is None
        assert not Path(reader.socket_path).exists()
        events = []
        for line in (
            (Path(reader.session_directory) / "owner.log").read_text().splitlines()
        ):
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
            except ValueError:
                pass
        summaries = [
            event for event in events if event.get("event") == "automatic-ae-finished"
        ]
        assert len(summaries) == 1 and summaries[0]["success"]
        assert (
            summaries[0]["automaticWhiteBalance"]
            and summaries[0]["processedStatistics"] >= 10
        )
        report["controlSummary"] = summaries[0]
        report.update(
            passed=True,
            seconds=time.monotonic() - started,
            decodedFrames=screen.decoder.frames,
            renderedFrames=sink.frames,
            ownerExitCode=reader.owner_exit_code,
            previewJoined=True,
            sessionDirectory=reader.session_directory,
            limitations=[
                "Actual installed scan/preview code and QR decoder receive real frames.",
                "Display sink and cancellation inputs are software substitutes.",
                "No decoded contents are recorded and no successful optical target is claimed.",
            ],
        )
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        if preview is not None:
            preview.stop()
            if preview.ident is not None:
                preview.join(timeout=3)
        if camera._video_stream is not None:
            camera.stop_video_stream_mode()
        threading.excepthook = old_hook
        report["threadErrors"] = errors
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
