"""Time a fixed raw/crop/local-threshold cascade on the same real camera frames.

Stages stop at any decoded symbol, not a known-target match. Only the final
public-target match is reported. Native process startup, temporary I/O and
preprocessing are included in wall time. This is a prototype pipeline benchmark,
not a claim of final integrated application performance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import statistics
import subprocess
import tempfile
import time

from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol

TARGET = b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def cpu():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def read(decoder, path, pixels, size, readers):
    if decoder == "zbar":
        start = time.monotonic()
        symbols = decode((pixels, *size), symbols=[ZBarSymbol.QRCODE], binary=True)
        return {"symbols": len(symbols), "matched": any(x.data == TARGET for x in symbols),
                "decodeSeconds": time.monotonic()-start}
    result = json.loads(subprocess.check_output(
        [str(readers[decoder]), str(path), str(size[0]), str(size[1]), "1"], timeout=15))
    return {"symbols": result["symbols"], "matched": bool(result["matches"]),
            "decodeSeconds": result["medianSeconds"], "nativePeakRssKiB": result["processMaxRssKiB"]}


def attempt(decoder, path, pixels, readers, threshold, temporary):
    stages = []
    started, cpu_started = time.monotonic(), cpu()
    for stage in ("raw", "center-crop", "full-local-threshold"):
        stage_started = time.monotonic()
        if stage == "raw":
            stage_path, data, size = path, pixels, (640, 480)
        elif stage == "center-crop":
            image = Image.frombytes("L", (640, 480), pixels).crop((160, 120, 480, 360))
            data, size = image.tobytes(), image.size
            stage_path = temporary / "crop.luma"
            if decoder != "zbar":
                stage_path.write_bytes(data)
        else:
            stage_path, size = temporary / "local.luma", (640, 480)
            subprocess.check_output([str(threshold), str(path), "640", "480", str(stage_path)], timeout=15)
            data = stage_path.read_bytes() if decoder == "zbar" else None
        prepared = time.monotonic()
        result = read(decoder, stage_path, data, size, readers)
        stages.append({"stage": stage, "prepareSeconds": prepared-stage_started,
                       "wallSeconds": time.monotonic()-stage_started, **result})
        if result["symbols"]:
            break
    return {"matched": stages[-1]["matched"], "stoppedAt": stages[-1]["stage"],
            "wallSeconds": time.monotonic()-started, "cpuSeconds": cpu()-cpu_started,
            "stages": stages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--native-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    readers = {name: args.native_directory / binary for name, binary in
               [("zxing", "reader"), ("quirc", "quirc-default"), ("quirc-float", "quirc-float")]}
    threshold = args.native_directory / "threshold"
    frames = [(p, p.read_bytes()) for p in sorted(args.directory.glob("*.luma"))]
    if len(frames) != 4 or any(len(data) != 640*480 for _, data in frames):
        parser.error("This protocol requires four VGA luminance frames")
    order = ("zbar", *readers)
    report = {"kind": "successful-pipeline-same-camera-frames-benchmark",
              "input": "Same four private real-camera VGA luminance frames used in raw stress test",
              "protocol": "Two reversed-order rounds, three attempts/frame/decoder = 24 attempts each",
              "stages": ["Full raw frame", "Fixed center crop (160,120)-(480,360)",
                         "Full-frame ZXing HybridBinarizer local threshold, without QR decoding"],
              "timing": "Includes preprocessing, native process startup, loading and temporary I/O. Source frames loaded before timer. Child CPU included.",
              "stopRule": "Stop at any decoded symbol; known target is used only for result checking",
              "nativeSha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for name, path in {**readers, "threshold": threshold}.items()},
              "samples": []}
    with tempfile.TemporaryDirectory(prefix="qr-success-", dir="/tmp") as temporary:
        for round_number, names in enumerate((order, tuple(reversed(order)))):
            for path, pixels in frames:
                for decoder in names:
                    for iteration in range(3):
                        result = attempt(decoder, path, pixels, readers, threshold, Path(temporary))
                        report["samples"].append({"decoder": decoder, "round": round_number,
                                                  "iteration": iteration, "inputSha256": hashlib.sha256(pixels).hexdigest(),
                                                  **result})
    report["summary"] = {}
    for name in order:
        samples = [s for s in report["samples"] if s["decoder"] == name]
        summary = {"matches": sum(s["matched"] for s in samples), "attempts": len(samples),
                   "medianWallSeconds": statistics.median(s["wallSeconds"] for s in samples),
                   "medianCpuSeconds": statistics.median(s["cpuSeconds"] for s in samples),
                   "maxWallSeconds": max(s["wallSeconds"] for s in samples),
                   "stageCounts": {stage: sum(s["stoppedAt"] == stage for s in samples)
                                   for stage in ["raw", "center-crop", "full-local-threshold"]}}
        report["summary"][name] = summary
        print(json.dumps({"decoder": name, **summary}), flush=True)
    with args.report.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
