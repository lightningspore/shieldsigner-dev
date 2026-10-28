"""Evaluate ZXing against private lossless camera frames on the desktop.

Only public-target matches, hashes and timing enter the report. No payloads or
images are copied. Desktop success does not qualify Luckfox integration/speed.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

from PIL import Image
import zxingcpp

TARGET = b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    frames = sorted(args.input_directory.glob("*.png"))
    if not frames:
        parser.error("No lossless PNG camera frames found")
    report = {"kind": "desktop-raw-camera-decoder-comparison",
              "decoder": "zxing-cpp", "version": importlib.metadata.version("zxing-cpp"),
              "scope": "Desktop decode only; not Luckfox performance or app integration",
              "frames": []}
    for path in frames:
        with Image.open(path) as image:
            result = {"sourceSha256": hashlib.sha256(path.read_bytes()).hexdigest(), "settings": {}}
            for name in ("LocalAverage", "GlobalHistogram", "FixedThreshold"):
                started = time.monotonic()
                symbols = zxingcpp.read_barcodes(image, formats=zxingcpp.BarcodeFormat.QRCode,
                                               binarizer=getattr(zxingcpp.Binarizer, name))
                result["settings"][name] = {
                    "matched": any(symbol.bytes == TARGET for symbol in symbols),
                    "symbolCount": len(symbols), "desktopSeconds": time.monotonic() - started}
            report["frames"].append(result)
    with args.report.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps({name: sum(frame["settings"][name]["matched"] for frame in report["frames"])
                      for name in report["frames"][0]["settings"]}))


if __name__ == "__main__":
    main()
