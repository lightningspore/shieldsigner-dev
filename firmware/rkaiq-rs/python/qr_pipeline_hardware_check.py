"""Compare QR preprocessing on identical live frames, with optional SHARP A/B.

Reports only matches against the bundled public target. Camera images and
unrelated decoded payloads are never written to the report.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import time

from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol
from shieldsigner_video_stream import PiVideoStream

TARGET = b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def jpeg(image, grayscale=False, quality=85):
    with io.BytesIO() as buffer:
        image = image.convert("L") if grayscale else image
        image.save(buffer, format="JPEG", quality=quality, subsampling=0)
        buffer.seek(0)
        with Image.open(buffer) as decoded:
            return decoded.copy()


def compare(frame):
    results = {}
    for name, prepare in (
        ("raw", lambda: frame),
        ("jpeg_rgb_85", lambda: jpeg(frame)),
        ("jpeg_gray_85", lambda: jpeg(frame, grayscale=True)),
        ("jpeg_rgb_75", lambda: jpeg(frame, quality=75)),
        ("jpeg_gray_75", lambda: jpeg(frame, grayscale=True, quality=75)),
        ("jpeg_gray_60", lambda: jpeg(frame, grayscale=True, quality=60)),
    ):
        start = time.monotonic()
        image = prepare()
        prepared = time.monotonic()
        symbols = decode(image, symbols=[ZBarSymbol.QRCODE], binary=True)
        results[name] = {
            "matched": any(symbol.data == TARGET for symbol in symbols),
            "symbolCount": len(symbols),
            "prepareSeconds": prepared - start,
            "decodeSeconds": time.monotonic() - prepared,
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--compare-sharp", action="store_true")
    parser.add_argument("--private-frame-directory", type=Path,
                        help="Explicitly save private lossless frames for offline diagnosis")
    args = parser.parse_args()
    if not 1 <= args.frames <= 30 or args.report.exists():
        parser.error("Use 1..30 frames and a new report filename")
    config = json.loads(args.config.read_text())
    if args.private_frame_directory:
        args.private_frame_directory.mkdir(parents=True, exist_ok=False)
    report = {"kind": "paired-live-frame-qr-comparison", "target": "bundled-public-address",
              "binarySha256": hashlib.sha256(Path(config["binary"]).read_bytes()).hexdigest(),
              "imagesSaved": bool(args.private_frame_directory), "profiles": []}
    old_modules = os.environ.get("SHIELDSIGNER_IQ_MODULES")
    old_format = os.environ.get("SHIELDSIGNER_CAMERA_STREAM_FORMAT")
    profiles = [("all", "all")]
    if args.compare_sharp:
        profiles.append(("without_sharp", "bay3d,ynr,cnr"))
    try:
        os.environ.pop("SHIELDSIGNER_CAMERA_STREAM_FORMAT", None)
        for name, modules in profiles:
            os.environ["SHIELDSIGNER_IQ_MODULES"] = modules
            stream = PiVideoStream(owner_config=config)
            item = {"name": name, "moduleSelection": modules, "frames": []}
            report["profiles"].append(item)
            try:
                stream.start()
                time.sleep(3)
                last = None
                deadline = time.monotonic() + 90
                while len(item["frames"]) < args.frames:
                    if stream.error:
                        raise RuntimeError("Camera reader failed: " + str(stream.error))
                    if time.monotonic() > deadline:
                        raise TimeoutError("Camera frame comparison deadline")
                    with stream._lock:
                        sequence, frame = stream.sequence, stream.frame
                    if frame is None or sequence == last:
                        time.sleep(.02)
                        continue
                    last = sequence
                    if args.private_frame_directory:
                        frame.save(args.private_frame_directory / (name + "-" + str(sequence) + ".png"))
                    item["frames"].append({"sequence": sequence, "results": compare(frame)})
                item["complete"] = True
            except Exception as exc:
                item["errorType"] = type(exc).__name__
                raise
            finally:
                try:
                    stream.stop()
                finally:
                    item["ownerExitCode"] = stream.owner_exit_code
            item["matches"] = {variant: sum(frame["results"][variant]["matched"]
                                           for frame in item["frames"])
                               for variant in item["frames"][0]["results"]}
            print(json.dumps({"profile": name, "matches": item["matches"]}), flush=True)
    finally:
        for key, value in [("SHIELDSIGNER_IQ_MODULES", old_modules),
                           ("SHIELDSIGNER_CAMERA_STREAM_FORMAT", old_format)]:
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        with args.report.open("x") as output:
            json.dump(report, output, indent=2)
            output.write("\n")


if __name__ == "__main__":
    main()
