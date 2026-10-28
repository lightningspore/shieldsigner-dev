"""Real pinned-image ScanScreen loops with a headless display/software cancel.

Camera, preview conversion, QR extraction, rendering and scan-loop methods are
the actual pinned application implementation. Screen construction is bypassed
to substitute only physical display/button boundaries. No payloads or scene
images are saved; a clipped target is expected to miss and cancel.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import threading
import time

from shieldsigner_integration import install_camera_backend


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("app-root", "config", "reader", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=3)
    parser.add_argument("--runtime-profile", choices=["luckfox_22", "luckfox_40", "luckfox_pi"], default="luckfox_22")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 10 or args.report.exists():
        parser.error("Use 1..10 seconds and a new report filename")
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(args.config.resolve())
    os.environ["SHIELDSIGNER_QR_READER"] = str(args.reader.resolve())
    module = install_camera_backend(args.app_root)
    client = module.__shieldsigner_qr_client__
    from seedsigner.models.settings import Settings
    Settings.RUNTIME_PROFILE = args.runtime_profile
    os.chdir(args.app_root)
    # Import the actual GUI/scan code and font resources; do not replace modules
    # to make an incomplete runtime look compatible.
    from seedsigner.gui.screens.scan_screens import ScanScreen
    from seedsigner.models.decode_qr import DecodeQR, DecodeQRStatus
    from seedsigner.models.threads import ThreadsafeCounter

    sources = [args.app_root / "seedsigner" / name for name in (
        "hardware/camera.py", "models/decode_qr.py", "gui/screens/scan_screens.py")]
    before = {str(p.relative_to(args.app_root)): digest(p) for p in sources}
    config = json.loads(args.config.read_text())
    report = {"passed": False, "opticalScanQualified": False,
              "physicalDisplayQualified": False, "physicalButtonsQualified": False,
              "runtimeProfileOverride": args.runtime_profile,
              "cameraBinarySha256": digest(config["binary"]),
              "nativeQrBinarySha256": digest(args.reader),
              "appSourcesSha256": before, "helperSha256": digest(__file__),
              "scope": "Pinned app real Camera/ScanScreen._run/LivePreviewThread rendering; only physical display/buttons and full Screen construction substituted"}

    class HeadlessRenderer:
        canvas_width = 240
        canvas_height = 240
        lock = threading.Lock()

        def __init__(self):
            self.frames = 0
            self.sizes = set()

        def show_image(self, image, show_direct=False):
            assert show_direct and 0 < image.width <= 240 and 0 < image.height <= 240
            self.frames += 1
            self.sizes.add(image.size)
            time.sleep(.03)

    class CountingDecoder(DecodeQR):
        def __init__(self):
            super().__init__()
            self.frames = 0
            self.status_counts = {}

        def add_image(self, image):
            status = super().add_image(image)
            self.frames += 1
            self.status_counts[int(status)] = self.status_counts.get(int(status), 0) + 1
            return status

    class SoftwareCancel:
        triggered = False

        def check_for_low(self, key):
            self.triggered |= time.monotonic() >= deadline
            return self.triggered

    def timed_out(_signal, _frame):
        raise TimeoutError("Pinned scan loop did not reach software cancellation deadline")

    camera = module.Camera.get_instance()
    preview, stream = None, None
    errors = []
    old_hook, old_alarm = threading.excepthook, signal.getsignal(signal.SIGALRM)
    threading.excepthook = lambda event: errors.append(type(event.exc_value).__name__)
    signal.signal(signal.SIGALRM, timed_out)
    signal.setitimer(signal.ITIMER_REAL, args.seconds + 10)
    try:
        camera.start_video_stream_mode(resolution=(480, 480), framerate=6, format="bgr")
        stream = camera._video_stream
        screen = ScanScreen.__new__(ScanScreen)
        screen.camera = camera
        screen.decoder = CountingDecoder()
        screen.frames_decode_status = ThreadsafeCounter()
        screen.hw_inputs = SoftwareCancel()
        sink = HeadlessRenderer()
        preview = ScanScreen.LivePreviewThread(screen.decoder, sink, "Camera integration test", None,
                                               screen.frames_decode_status)
        screen.threads = [preview]
        started = time.monotonic()
        deadline = started + args.seconds
        preview.start()
        result = screen._run()
        preview.stop()
        preview.join(timeout=3)
        report.update(seconds=time.monotonic()-started, decodedFrames=screen.decoder.frames,
                      decodeStatusCounts=screen.decoder.status_counts, renderedFrames=sink.frames,
                      renderedSizes=[list(size) for size in sorted(sink.sizes)],
                      previewJoined=not preview.is_alive(), softwareCancelTriggered=screen.hw_inputs.triggered,
                      screenReturnedCancel=result is False, backendInfo=stream.backend_info,
                      sessionDirectory=stream.session_directory, receivedFrames=stream.frames_received,
                      ownerExitCode=stream.owner_exit_code, qrWorkerClosedOnCameraStop=client._process is None)
        assert not preview.is_alive() and not errors
        assert screen.decoder.frames >= 3 and sink.frames >= 3
        assert screen.hw_inputs.triggered and result is False
        assert screen.decoder.status_counts == {int(DecodeQRStatus.FALSE): screen.decoder.frames}
        assert stream.owner_exit_code == 0 and camera._video_stream is None
        assert client._process is None and client.stats["errors"] == 0 and client.stats["calls"] > 0
        assert not Path(stream.socket_path).exists()
        events = []
        for line in (Path(stream.session_directory)/"owner.log").read_text().splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
            except ValueError:
                pass
        summaries = [value for value in events if value.get("event") == "automatic-ae-finished"]
        assert len(summaries) == 1 and summaries[0]["success"]
        assert summaries[0]["automaticWhiteBalance"] and summaries[0]["processedStatistics"] >= 3
        report["controlSummary"] = {key: summaries[0][key] for key in (
            "success", "processedStatistics", "parameterSubmissions", "automaticWhiteBalance")}
        report["passed"] = True
    except Exception as exc:
        report["errorType"] = type(exc).__name__
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if preview is not None:
            preview.stop()
            if preview.ident is not None:
                preview.join(timeout=3)
        if camera._video_stream is not None:
            camera.stop_video_stream_mode()
        client.close()
        threading.excepthook = old_hook
        signal.signal(signal.SIGALRM, old_alarm)
        report["threadErrors"] = errors
        report["nativeQrStats"] = dict(client.stats)
        report["installedSourcesUnchanged"] = before == {str(p.relative_to(args.app_root)): digest(p) for p in sources}
        assert report["installedSourcesUnchanged"]
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
