#!/usr/bin/env python3
"""Replay private translated FAST statistics through fresh measurement caches.

Runs original software-result initialization, then original PrepareMeasureResult.
No camera writes occur. Caller must supply already associated translated data.
The pinned scene uses EXCLUDE (1) for every extra region: no include curves.
"""

import argparse
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path

from awb_reference import RUNTIME

from differential import BINARY, HEAP, ROOT

Original = importlib.import_module("awb-initial-gain-state").Original


def render(arm, n):
    c = bytes(arm.uc.mem_read(HEAP, 0x3700))

    def read(p, length):
        return bytes(arm.uc.mem_read(p, length))

    cfg = struct.unpack_from("<I", c, 0x8C)[0]
    out = bytearray(
        [
            c[0x334A],
            c[0x3348],
            read(cfg + 0x138, 1)[0],
            c[0x13C],
            c[0xF79],
            c[0x1A08],
            c[0x2BA0],
        ]
    )
    out.extend(c[0x334C:0x338C])
    out.extend(c[0x13D:0x23D])
    for offset, length in (
        (0x138, n),
        (0x134, n * 0xAC),
        (0x244, n * 4),
        (0x240, max(n, 2) * 4),
    ):
        out.extend(read(struct.unpack_from("<I", c, offset)[0], length))
    for start, end in (
        (0x3588, 0x3598),
        (0xF7C, 0x1A08),
        (0x2BA4, 0x2D10),
        (0x2D10, 0x2D44),
        (0x2D64, 0x2DE4),
        (0x2D44, 0x2D64),
    ):
        out.extend(c[start:end])
    return out.hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("translated", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--arm", action="store_true")
    args = ap.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == "421df6d09247848a7f733d25ef45b726bc6366c8fc12be84751f6b408c1d92cd"
    )
    raw = args.translated.read_bytes()
    assert len(raw) == 7680
    assert raw[0x1D70 + 28 : 0x1D70 + 39] == b"FASTAWBACT\0"
    assert raw[0x1D74] == 4 and struct.unpack_from("<i", raw, 0x1D78)[0] == -1
    assert struct.unpack_from("<4I", raw, 0x1D7C) == (0, 1, 2, 3)
    iq_path = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq = iq_path.read_bytes()
    assert (
        hashlib.sha256(iq).hexdigest()
        == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    )
    wb = json.loads(iq)["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"]
    assert all(
        r["mode"] == "CALIB_AWB_EXCLUDE_WP_MODE" for r in wb["autoPara"]["extraWpRange"]
    )
    n = len(wb["autoPara"]["lightSources"])
    threshold = wb["autoExtPara"]["smartRun"]["cfg"]["wbgainHwDiffTh"][0]
    v = dict(n=n, groups=4, fast_count=4, threshold=threshold, raw=raw.hex())

    def fixture(kind, value):
        result = subprocess.run(
            [str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")],
            input=kind + " " + json.dumps(value, separators=(",", ":")) + "\n",
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    expected = fixture("awb-fresh-preparation", v)
    if args.arm:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--platform",
            "linux/arm/v7",
            "--network=none",
            "--mount",
            f"type=bind,src={directory},dst=/bincheck,readonly",
            "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
            "/bincheck/numeric-fixture",
        ]
        result = subprocess.run(
            command,
            input="awb-fresh-preparation "
            + json.dumps(v, separators=(",", ":"))
            + "\n",
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(result.stdout) == expected
    initial = fixture("awb-initial-gain-state", dict(iq=wb, first=0))
    arm = Original()
    arm.run(0, initial)

    # Explicit calibrated strategy and raw-record bindings, not controller seeds.
    def word(address, value):
        arm.uc.mem_write(address, struct.pack("<I", value))

    cfg = HEAP + 0x14000
    arm.uc.mem_write(cfg + 0x138, bytes([n]))
    word(cfg + 4, 4)
    word(cfg + 0x398, 4)
    arm.uc.mem_write(cfg + 0x4B0, struct.pack("<f", threshold))
    arm.uc.mem_write(cfg + 0x480, struct.pack("<4I", 1, 1, 1, 1))
    assert render(arm, n) == expected["before"]
    word(HEAP + 0x2DEC, HEAP + 0x40000 + 0x1D70)
    arm.uc.mem_write(HEAP + 0x40000, raw)
    arm.invoke(
        next(name for name in arm.symbols if "PrepareMeasureResult" in name),
        [HEAP + 0x40000, HEAP],
        instructions=2000000,
    )
    actual = render(arm, n)
    assert actual == expected["after"], next(
        (i // 2 for i, (a, b) in enumerate(zip(actual, expected["after"])) if a != b),
        "length mismatch",
    )
    report = dict(
        kind="captured-fresh-awb-preparation",
        translatedSha256=hashlib.sha256(raw).hexdigest(),
        originalSha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        arm=args.arm,
        comparedBytes=len(actual) // 2,
        mismatches=0,
        scope="Fresh measurement caches before and after original PrepareMeasureResult on one associated FAST capture",
        limitations=[
            "No full controller or live gain publication in this check.",
            "Pinned seven-light scene; four FAST regions, group -1, all extra-region modes EXCLUDE.",
            "Translation and parameter association are checked separately before this replay.",
        ],
    )
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
