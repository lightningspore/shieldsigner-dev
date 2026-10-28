"""Benchmark installed ZBar and static native readers on identical private frames.

Decode timers exclude file loading and Python/native process startup. RSS is
whole-process high-water usage, not comparable isolated library allocation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import time

TARGET = b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def zbar(path, runs):
    from pyzbar.pyzbar import decode, ZBarSymbol
    pixels = path.read_bytes()
    if len(pixels) != 640 * 480:
        raise ValueError("Expected VGA luminance frame")
    times, matches, symbols = [], 0, 0
    for _ in range(runs):
        start = time.monotonic()
        result = decode((pixels, 640, 480), symbols=[ZBarSymbol.QRCODE], binary=True)
        times.append(time.monotonic() - start)
        matches += any(item.data == TARGET for item in result)
        symbols += len(result)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines()
                        if line.startswith('VmHWM:')))
    return {"decoder": "installed-zbar-pyzbar", "runs": runs, "matches": matches,
            "symbols": symbols, "firstSeconds": times[0], "medianSeconds": statistics.median(times),
            "minSeconds": min(times), "maxSeconds": max(times),
            "processCpuSeconds": usage.ru_utime + usage.ru_stime,
            "processMaxRssKiB": peak_rss}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zbar-frame", type=Path)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--quirc", type=Path)
    parser.add_argument("--quirc-float", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100:
        parser.error("Use 1..100 iterations")
    if args.zbar_frame:
        print(json.dumps(zbar(args.zbar_frame, args.iterations)))
        return
    if not args.directory or not args.native or not args.report or args.report.exists():
        parser.error("Supply --directory, --native and a new --report")
    frames = sorted(args.directory.glob("*.luma"))
    if not frames:
        parser.error("No luminance frames found")
    report = {"kind": "same-device-qr-decoder-benchmark", "width": 640, "height": 480,
              "input": "Identical Pillow L luminance bytes; no JPEG or preprocessing in timed calls",
              "scope": "Static public target, saved real camera frames; not live/animated app integration",
              "timing": "Per-call wall time; QR-only, default search settings, ZXing LocalAverage",
              "memory": "Current-executable /proc/self/status VmHWM, including Python for ZBar and native runtime for other readers; not isolated library overhead",
              "nativeSha256": hashlib.sha256(args.native.read_bytes()).hexdigest(),
              "zbarLibrarySha256": hashlib.sha256(Path('/usr/lib/libzbar.so.0.3.0').read_bytes()).hexdigest(),
              "cases": []}
    natives = {"zxing": args.native}
    if args.quirc:
        natives["quirc"] = args.quirc
    if args.quirc_float:
        natives["quirc-float"] = args.quirc_float
    report["nativeBinariesSha256"] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                       for name, path in natives.items()}
    order = ("zbar", *natives)
    for round_number, order in enumerate((order, tuple(reversed(order)))):
        for path in frames:
            for decoder in order:
                command = ([sys.executable, __file__, "--zbar-frame", str(path), "--iterations", str(args.iterations)]
                           if decoder == "zbar" else [str(natives[decoder]), str(path), "640", "480", str(args.iterations)])
                result = json.loads(subprocess.check_output(command, timeout=60))
                result.update(round=round_number, inputSha256=hashlib.sha256(path.read_bytes()).hexdigest())
                report["cases"].append(result)
                print(json.dumps(result), flush=True)
    with args.report.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
