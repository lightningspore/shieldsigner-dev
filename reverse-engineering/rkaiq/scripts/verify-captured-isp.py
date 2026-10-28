"""Replay all nine captured ISP blocks against original ARM module callbacks.

No device access. The supplied capture may predate the current executable;
hashes identify it, and this tool never claims a new camera run occurred.
Optional AWB trace also executes the current Rust fixture and joined native
initialization. All bulky/native records stay in the requested private output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="Private frame prefix, with .log/.initial.* sidecars")
    parser.add_argument("--trace-dir", type=Path)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    args.private_output.mkdir(parents=True, exist_ok=False)
    report = {"kind": "captured-isp-native-reference-replay", "newHardwareCapture": False,
              "ownerLogSha256": digest(Path(str(args.base) + ".log")),
              "initialParametersSha256": digest(Path(str(args.base) + ".initial.bin")),
              "checks": {}}

    def invoke(name, command):
        destination = args.private_output / (name + ".json")
        with (args.private_output / (name + ".log")).open("w") as output:
            subprocess.run([sys.executable, *map(str, command), "--report", str(destination)],
                           cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, check=True)
        result = json.loads(destination.read_text())
        report["checks"][name] = {"reportSha256": digest(destination),
                                  "passed": result.get("passed", result.get("mismatches", -1) == 0)}
        return result

    for name in ["cnr", "baynr", "lsc", "ccm", "dpcc", "demosaic", "new-blocks"]:
        source = Path(str(args.base) + ".log") if name == "demosaic" else args.base
        invoke(name, [SCRIPTS / (name + "-live-check.py"), source])
    raw = Path(str(args.base) + ".stats.raw")
    parameter = struct.unpack_from("<I", raw.read_bytes(), 0x32E8)[0]
    invoke("awb-translation", [SCRIPTS / "awb-captured-translation.py", raw,
           Path(str(args.base) + ".awb-effective-sdk.bin"), Path(str(args.base) + ".awb-translated.bin"),
           "--configuration-id", parameter])
    if args.trace_dir:
        result = invoke("awb-joined", [SCRIPTS / "awb-joined-captured.py", "--trace-dir", args.trace_dir,
                        "--native-initialization", "--hardware-reference", "--require-match"])
        report["checks"]["awb-joined"].update(
            passed=result["mismatchingFrames"] == 0,
            frames=len(result["frames"]),
            rustFixtureSha256=result["rustFixtureSha256"])
    report["modulesCompared"] = ["CCM", "LSC", "DPCC", "BAYNR", "BAY3D", "YNR", "CNR", "SHARP", "DEMOSAIC"]
    report["passed"] = all(check["passed"] for check in report["checks"].values())
    report["scope"] = "Captured startup/runtime module outputs and converter bytes through original ARM; optional joined AWB executes current Rust fixture. This is replay of the supplied capture, not a new physical run."
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
