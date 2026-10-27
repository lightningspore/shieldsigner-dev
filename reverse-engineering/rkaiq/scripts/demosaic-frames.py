#!/usr/bin/env python3
"""Compare persistent linear color demosaic callback against original ARM code."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile

from differential import ROOT, BINARY, HEAP, regs
from exposure import RUNTIME

selection = importlib.import_module("demosaic-selection")


class OriginalFrame(selection.OriginalSelection):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get("xcam_print_log", 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    source = (
        ROOT
        / "dist/reverse-engineering/demosaic-selection-fixtures/sc3336-demosaic-subset.json"
    )
    value = json.loads(source.read_text())
    calibration = value.get("calibration", value.get("debayer_v2", value))
    if "param" in calibration:
        calibration = calibration["param"]
    header = (
        ROOT
        / ".tools/reverse-engineering/luckfox-sdk/media/isp/release_camera_engine_rkaiq_rv1106_arm-rockchip830-linux-uclibcgnueabihf/isp_iqfiles/include/iq_parser_v2/debayer_head.h"
    )
    if not header.exists():
        candidates = list((ROOT / ".tools/reverse-engineering").rglob("debayer_head.h"))
        assert len(candidates) == 1, candidates
        header = candidates[0]
    packed = selection.pack_record(
        selection.schema(header.read_text()), "CalibDbV2_Debayer_Tuning_t", calibration
    )
    rng = random.Random(0x4446524D)
    hardware = bytearray(rng.randbytes(112))
    hardware[0] = 0
    hardware[1] = 1
    frames = []
    gains = [
        [1.0, 1.0, 1.0],
        [2.0, 1.0, 1.0],
        [2.01, 1.0, 1.0],
        [0.5, 1.0, 1.0],
        [4.0, 2.0, 1.5],
        [16.0, 1.0, 1.0],
        [1.9999, 1.0, 1.0],
        None,
    ]
    for i in range(256):
        frames.append(
            {"gains": gains[(i // 3) % len(gains)], "reconfigure": i % 17 == 0}
        )
    payload = {"calibration": calibration, "hardware": hardware.hex(), "frames": frames}
    line = "demosaic-frames " + json.dumps(payload, separators=(",", ":")) + "\n"
    actual = json.loads(
        subprocess.check_output(
            [str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")],
            input=line,
            text=True,
        )
    )
    arm = OriginalFrame()
    arm.symbols["demosaic-frame"] = arm.resolve_symbol("processing", 0x124A2C)
    context, inp, exposure, out, hw = [
        HEAP + x for x in (0, 0x2000, 0x3000, 0x4000, 0x5000)
    ]
    arm.uc.mem_write(context, bytes(0x600))
    arm.uc.mem_write(context, b"\1")
    arm.uc.mem_write(context + 8, struct.pack("<i", 2))
    arm.uc.mem_write(context + 12, bytes(hardware))
    arm.uc.mem_write(context + 0x7C, packed)
    arm.uc.mem_write(context + 0x4C8, struct.pack("<i", 50))
    arm.uc.mem_write(inp, bytes(128))
    arm.uc.mem_write(inp, struct.pack("<I", context))
    arm.uc.mem_write(out, bytes(16))
    arm.uc.mem_write(out + 4, struct.pack("<I", hw))
    arm.uc.mem_write(hw, bytes(112))
    expected = []
    for frame in frames:
        if frame["reconfigure"]:
            arm.uc.mem_write(context, b"\1")
        arm.uc.mem_write(inp + 24, struct.pack("<I", exposure if frame["gains"] else 0))
        if frame["gains"]:
            arm.uc.mem_write(exposure, bytes(244))
            arm.uc.mem_write(exposure + 4, struct.pack("<3f", *frame["gains"]))
        assert arm.invoke("demosaic-frame", [inp, out]) == 0
        updated = arm.uc.mem_read(out, 1)[0] != 0
        expected.append(
            {
                "iso": struct.unpack("<i", arm.uc.mem_read(context + 0x4C8, 4))[0],
                "reconfigure": bool(arm.uc.mem_read(context, 1)[0]),
                "hardware": bytes(arm.uc.mem_read(hw, 112)).hex() if updated else None,
                "cache": bytes(arm.uc.mem_read(context + 12, 112)).hex(),
            }
        )
    assert actual == expected, next(
        (i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
        "length mismatch",
    )
    board_matches = False
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = "/shieldsigner-camera-tests/dev-0.0.33/demosaic-frames.private.txt"
        board_sha = subprocess.check_output(
            adb
            + [
                "shell",
                "sha256sum /shieldsigner-camera-tests/dev-0.0.33/bin/numeric-fixture",
            ],
            text=True,
        ).split()[0]
        assert (
            board_sha
            == hashlib.sha256(
                (
                    ROOT
                    / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture"
                ).read_bytes()
            ).hexdigest()
        )
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary) / "input"
            p.write_text(line)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                result = subprocess.check_output(
                    adb
                    + [
                        "shell",
                        "/shieldsigner-camera-tests/dev-0.0.33/bin/numeric-fixture < "
                        + remote,
                    ],
                    text=True,
                )
                assert json.loads(result) == actual
                board_matches = True
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "frames": len(frames),
        "updates": sum(x["hardware"] is not None for x in actual),
        "noOpFrames": sum(x["hardware"] is None for x in actual),
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "calibrationSubsetSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "hostMatchesPhysicalArm": board_matches,
        "physicalArmBinarySha256": board_sha,
        "hostBinarySha256": hashlib.sha256(
            (ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture").read_bytes()
        ).hexdigest(),
        "uclibcRuntimeSha256": hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        "sdkHeaderSha256": hashlib.sha256(header.read_bytes()).hexdigest(),
        "scope": "Complete native linear color-frame callback, ISO gate, selection, quantization and persistent cache; all 112 output/cache bytes compared.",
        "limitations": [
            "Monochrome, HDR and manual modes are outside this explicit automatic-color API.",
            "Physical ARM replay does not program the live ISP; queue integration remains next.",
            "Diagnostic logging is a modeled no-op; original selection/quantization and uClibc math execute.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
