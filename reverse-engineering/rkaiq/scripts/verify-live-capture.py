#!/usr/bin/env python3
"""Run existing native live-module and saved AWB checks as one private-artifact task."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
MODULES = ("baynr", "lsc", "ccm", "dpcc", "demosaic")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("base", type=Path)
    p.add_argument("--modules", nargs="+", choices=MODULES, default=list(MODULES))
    p.add_argument("--min-submissions", type=int, default=0)
    args = p.parse_args()

    def path(s):
        return Path(str(args.base) + s)

    def run(script, arguments, report):
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / script),
                *map(str, arguments),
                "--report",
                str(report),
            ],
            text=True,
            capture_output=True,
        )
        if process.returncode:
            sys.stderr.write(process.stdout + process.stderr)
            raise SystemExit(process.returncode)
        return json.loads(report.read_text())

    summaries = {}
    for module in args.modules:
        report = path(".native-" + module + ".json")
        source = path(".log") if module == "demosaic" else args.base
        summary = run(module + "-live-check.py", [source], report)
        assert summary["passed"]
        summaries[module] = str(report)
        print("PASS:", module, flush=True)
    raw = path(".stats.raw").read_bytes()
    assert len(raw) in (13036, 13040)
    configuration = struct.unpack_from("<I", raw, 0x32E8)[0]
    report = path(".native-awb.json")
    translation = run(
        "awb-captured-translation.py",
        [
            path(".stats.raw"),
            path(".awb-effective-sdk.bin"),
            path(".awb-translated.bin"),
            "--configuration-id",
            configuration,
        ],
        report,
    )
    assert translation["bytesCompared"] == 7680 and translation["mismatches"] == 0
    summaries["awbTranslation"] = str(report)
    control_report = path(".awb-check.json")
    control = run(
        "awb-live-capture-check.py",
        [
            args.base,
            "--native-report",
            report,
            "--min-submissions",
            args.min_submissions,
        ],
        control_report,
    )
    assert control["passed"]
    summaries["control"] = str(control_report)
    path(".live-check.json").write_text(
        json.dumps(
            dict(
                passed=True,
                reports=summaries,
                limitations=[
                    "Private local artifact orchestration; individual native oracle boundaries remain authoritative.",
                    "Does not establish optical decoding or complete image-quality equivalence.",
                ],
            ),
            indent=2,
        )
        + "\n"
    )
    print("PASS: final AWB translation and live controller bookkeeping", flush=True)


if __name__ == "__main__":
    main()
