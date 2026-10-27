#!/usr/bin/env python3
"""Persistent full DPCC processing-callback comparison for the linear profile."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import uuid

from differential import ROOT, BINARY, HEAP

reference = importlib.import_module("dpcc-automatic")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    calibration = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["adpcc_calib"]["DpccTuningPara"]
    arm = reference.OriginalAutomatic()
    schema = reference.schema_full(
        (ROOT / ".tools/reverse-engineering/headers/adpcc_head.h").read_text()
    )
    source, _ = reference.pack_full(
        schema, "CalibDbDpccV20_t", calibration, arm, [HEAP + 0x60000]
    )
    arm.uc.mem_write(HEAP + 0x20000, source)
    arm.uc.mem_write(HEAP + 0x1000, bytes(4))
    assert (
        arm.invoke(
            "_Z9AdpccInitPP14AdpccContext_sP21CamCalibDbV2Context_s",
            [HEAP + 0x1000, HEAP],
        )
        == 0
    )
    context = HEAP + 0x40000
    inp, out, result, exposure = [
        HEAP + x for x in (0x10000, 0x11000, 0x12000, 0x13000)
    ]
    arm.uc.mem_write(inp, bytes(64))
    arm.uc.mem_write(inp, struct.pack("<I", context))
    arm.uc.mem_write(out, bytes(16))
    arm.uc.mem_write(out + 4, struct.pack("<I", result))
    arm.uc.mem_write(result, bytes(192))
    arm.symbols["dpcc-frame"] = arm.resolve_symbol("processing", 0x12A67C)
    choices = [
        [1.0, 1.0, 1.0],
        [2.0, 1.0, 1.0],
        [2.01, 1.0, 1.0],
        [0.5, 1.0, 1.0],
        [3.14159, 1.25, 1.1],
        [16.0, 1.0, 1.0],
        None,
        [1.99999, 1.003, 1.001],
    ]
    frames = []
    expected = []
    for index in range(256):
        gains = choices[(index // 3) % len(choices)]
        force = index % 17 == 0
        frames.append({"gains": gains, "reconfigure": force})
        if force:
            arm.uc.mem_write(context + 0x1960, b"\1")
        arm.uc.mem_write(inp + 24, struct.pack("<I", exposure if gains else 0))
        if gains:
            arm.uc.mem_write(exposure, struct.pack("<4f", 0.003, *gains) + bytes(228))
        arm.invoke("dpcc-frame", [inp, out])
        expected.append(
            {
                "iso": struct.unpack("<i", arm.uc.mem_read(context + 48, 4))[0],
                "updated": bool(arm.uc.mem_read(out, 1)[0]),
                "reconfigure": bool(arm.uc.mem_read(context + 0x1960, 1)[0]),
                "result": bytes(arm.uc.mem_read(result, 192)).hex(),
            }
        )
    line = (
        "dpcc-frames "
        + json.dumps(
            {"calibration": calibration, "frames": frames}, separators=(",", ":")
        )
        + "\n"
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = json.loads(subprocess.check_output([str(binary)], input=line, text=True))
    assert actual == expected, next(
        (i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
        "length mismatch",
    )
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/dpcc-frames-"
            + uuid.uuid4().hex
            + ".txt"
        )
        board_sha = subprocess.check_output(
            adb + ["shell", "sha256sum " + board], text=True
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
                assert (
                    json.loads(
                        subprocess.check_output(
                            adb + ["shell", board + " < " + remote], text=True
                        )
                    )
                    == actual
                )
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "frames": len(frames),
        "updates": sum(x["updated"] for x in expected),
        "noOpFrames": sum(not x["updated"] for x in expected),
        "mismatches": 0,
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Full persistent native linear color DPCC callback, ISO/reconfiguration gate, supported auto-expert processing and all 192 result bytes.",
        "limitations": [
            "Allocator, explicit SDK calibration lookup and diagnostic logging retain the documented native-init oracle boundaries.",
            "No HDR/manual/enabled-PDAF/sensor-side DPCC coverage.",
            "Physical replay does not exercise the live ISP queue.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
