#!/usr/bin/env python3
"""Run the joined Rust gain calculation on a private translated capture.

Optional ADB execution uses a temporary input file because this board only
supports PTYs, whose canonical-input line limit truncates the fixture protocol.
No camera device is opened and no gains are submitted by this replay command.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iq", type=Path)
    ap.add_argument("translated", type=Path)
    ap.add_argument("--sample-scale", type=int, required=True)
    ap.add_argument("--iso", type=float, required=True)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--adb", help="Serial of board on which to compare Rust execution")
    ap.add_argument("--board-binary", default="/tmp/shieldsigner-numeric-awb-replay")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    iq = json.loads(args.iq.read_text())
    wb = iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"]
    payload = dict(
        iq=wb,
        raw=args.translated.read_bytes().hex(),
        dimensions=[args.width, args.height],
        sample_scale=args.sample_scale,
        iso=args.iso,
    )
    line = "awb-captured-gain " + json.dumps(payload, separators=(",", ":")) + "\n"
    result = subprocess.run(
        [str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")],
        input=line,
        text=True,
        capture_output=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert "error" not in report, report
    if args.adb:
        assert re.fullmatch(r"/tmp/[A-Za-z0-9_.-]+", args.board_binary)
        adb = ["adb", "-s", args.adb]
        remote = "/tmp/ss-awb-replay-" + uuid.uuid4().hex + ".private.txt"
        with tempfile.TemporaryDirectory(prefix="ss-awb-replay-") as directory:
            local = Path(directory) / "input.private.txt"
            local.write_text(line)
            local.chmod(0o600)
            try:
                subprocess.run(
                    adb + ["push", str(local), remote], capture_output=True, check=True
                )
                result = subprocess.run(
                    adb + ["shell", args.board_binary + " < " + remote],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                actual = json.loads(result.stdout)
                assert actual == report, "Host/board replay differs"
            finally:
                subprocess.run(
                    adb + ["shell", "rm -f " + remote], capture_output=True, check=True
                )
        report["hostMatchesBoard"] = True
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
