"""Verify process-local Camera integration and clearly synthetic QR fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import tempfile

from PIL import Image
import qrcode

from shieldsigner_integration import camera_source, install_camera_backend

PAYLOAD = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


class FrozenFrame:
    def __init__(self, frame):
        self.frame = frame
        self.width, self.height = frame.size

    def read(self):
        return self.frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    path, _, _ = camera_source(args.app_root)
    original_hash = digest(path)
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(Path(args.config).resolve())
    module = install_camera_backend(args.app_root)
    assert install_camera_backend(args.app_root) is module
    from seedsigner.models.decode_qr import DecodeQR, DecodeQRStatus
    report = {"passed": False, "integration": module.__shieldsigner_camera_patch__,
              "opticalScanQualified": False, "syntheticQrCases": []}
    with tempfile.TemporaryDirectory(prefix="camera-source-check-", dir=Path(args.report).parent) as temporary:
        changed = Path(temporary) / "seedsigner/hardware/camera.py"
        changed.parent.mkdir(parents=True)
        changed.write_bytes(path.read_bytes() + b"\n# Changed source must be reviewed.\n")
        try:
            install_camera_backend(temporary)
        except ValueError:
            report["changedSourceRejected"] = True
        else:
            raise AssertionError("Changed upstream camera source was accepted")
    camera = module.Camera.__new__(module.Camera)
    camera._camera_rotation = 0
    try:
        camera.start_video_stream_mode()
        reader = camera._video_stream
        first = None
        seen = []
        raw = None
        started = time.monotonic()
        try:
            while first is None or time.monotonic() - first < 8:
                frame = camera.read_video_stream()
                if frame is not None:
                    if first is None:
                        first = time.monotonic()
                        report["realFrameDecodeStatus"] = int(DecodeQR().add_image(frame))
                    raw = frame
                    preview = camera.read_video_stream(as_image=True)
                    assert raw.size == (640, 480) and preview.size == (480, 640)
                    if not seen or seen[-1] != reader.sequence:
                        seen.append(reader.sequence)
                if time.monotonic() - started > 20:
                    raise TimeoutError("Integrated camera session exceeded deadline")
                time.sleep(.01)
        finally:
            stop = time.monotonic()
            camera.stop_video_stream_mode()
        assert reader.owner_exit_code == 0 and len(seen) >= 20
        report["capture"] = {"directory": reader.session_directory,
                             "firstFrameSeconds": first-started, "first": seen[0], "last": seen[-1],
                             "samples": len(seen), "received": reader.frames_received,
                             "stopSeconds": time.monotonic()-stop, "ownerExitCode": reader.owner_exit_code}
        # Freeze the real captured frame: compare preview geometry/pixels without
        # racing the reader, and benchmark rotation with the owner stopped.
        camera._video_stream = FrozenFrame(raw)
        rotations = []
        for setting, operation in [(0, Image.Transpose.ROTATE_90),
                                   (90, Image.Transpose.ROTATE_180),
                                   (180, Image.Transpose.ROTATE_270), (270, None)]:
            camera._camera_rotation = setting
            preview = camera.read_video_stream(as_image=True)
            expected = raw.transpose(operation) if operation is not None else raw
            assert preview.size == expected.size and preview.tobytes() == expected.tobytes()
            rotations.append({"setting": setting, "size": preview.size, "allPixelsPreserved": True})
        report["realFrameRotations"] = rotations
        before = time.monotonic()
        for _ in range(5):
            raw.rotate(90)
        cropped_seconds = (time.monotonic()-before)/5
        before = time.monotonic()
        for _ in range(5):
            raw.rotate(90, expand=True)
        expanded_seconds = (time.monotonic()-before)/5
        report["rotationBenchmark"] = {"croppedSecondsPerFrame": cropped_seconds,
                                        "expandedSecondsPerFrame": expanded_seconds}
        # No camera/optics claim: known generated pixels through actual Camera
        # preview and actual DecodeQR, including QRs near all four frame edges.
        qr = qrcode.make(PAYLOAD, box_size=6, border=4).convert("RGB")
        qr.save(args.report + ".public-qr.png")
        for x, y in [(12,12), (640-12-qr.width,12),
                     (12,480-12-qr.height), (640-12-qr.width,480-12-qr.height)]:
            fixture = Image.new("RGB", (640,480), "white")
            fixture.paste(qr, (x,y))
            camera._video_stream = FrozenFrame(fixture)
            for setting in [0,90,180,270]:
                camera._camera_rotation = setting
                preview = camera.read_video_stream(as_image=True)
                decoder = DecodeQR()
                status = decoder.add_image(preview)
                assert status == DecodeQRStatus.COMPLETE and decoder.get_address() == PAYLOAD
                report["syntheticQrCases"].append({"position":[x,y], "rotation":setting,
                                                   "size":preview.size, "decodedExpectedPublicAddress":True})
        camera._video_stream = None
        report["installedCameraUnchanged"] = digest(path) == original_hash
        assert report["installedCameraUnchanged"]
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        if camera._video_stream is not None and not isinstance(camera._video_stream, FrozenFrame):
            camera.stop_video_stream_mode()
        with open(args.report, "x") as output:
            json.dump(report, output, indent=2)
        print(json.dumps(report))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
