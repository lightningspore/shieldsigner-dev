#!/usr/bin/env python3
"""Compare automatic expert ISO selection and result preservation with ARM."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid

from differential import OriginalArm, ROOT, BINARY, HEAP


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    iq_path = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq = json.loads(iq_path.read_text())
    profile_knots = iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["adpcc_calib"][
        "DpccTuningPara"
    ]["Expert_Mode"]["SetEnable"]["ISO"]
    assert len(profile_knots) == 13 and all(
        float(v).is_integer() for v in profile_knots
    )
    profile_knots = list(map(int, profile_knots))
    assert all(a < b for a, b in zip(profile_knots, profile_knots[1:]))
    rng = random.Random(0x44505345)
    arm = OriginalArm(BINARY)
    cases = []
    expected = []
    for index in range(1000):
        table = bytearray(rng.randbytes(1404))
        knots = []
        knot = rng.randint(-100, 100)
        for row in range(13):
            knot += rng.randint(1, 1000)
            knots.append(knot)
        if index < 100:
            knots = profile_knots
        for row, knot in enumerate(knots):
            struct.pack_into("<i", table, row * 108, knot)
        points = [-(1 << 31), (1 << 31) - 1] + [
            v + delta for v in knots for delta in (-1, 0, 1)
        ]
        iso = points[index % len(points)]
        result = rng.randbytes(192)
        value = {"table": table.hex(), "iso": iso, "result": result.hex()}
        cases.append(value)
        base, out, exposure = HEAP, HEAP + 0x10000, HEAP + 0x20000
        arm.uc.mem_write(base, bytes(table))
        arm.uc.mem_write(out, result)
        arm.uc.mem_write(exposure, bytes(100))
        arm.uc.mem_write(exposure + 40, struct.pack("<i", iso))
        assert (
            arm.invoke(
                "_Z38Expert_mode_select_basic_params_by_ISOP20Adpcc_basic_params_sP24Adpcc_basic_cfg_params_sP14AdpccExpInfo_s",
                [base, out, exposure],
            )
            == 0
        )
        assert bytes(arm.uc.mem_read(base, 1404)) == table
        native = bytes(arm.uc.mem_read(out, 192))
        assert native[103:] == result[103:]
        expected.append(native.hex())
    lines = "".join(
        "dpcc-select " + json.dumps(value, separators=(",", ":")) + "\n"
        for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/dpcc-select-"
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
            p.write_text(lines)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                assert (
                    subprocess.check_output(
                        adb + ["shell", board + " < " + remote], text=True
                    ).splitlines()
                    == actual
                )
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 192,
        "profileIsoGridCases": 100,
        "profileSha256": hashlib.sha256(iq_path.read_bytes()).hexdigest(),
        "mismatches": 0,
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "coverage": [
            "Exact knots and +/-1 neighbors",
            "Below/above entire table including i32 endpoints",
            "Arbitrary selected values, source padding and prior result bytes",
            "Native preserves all bytes after the 103-byte basic configuration",
        ],
        "scope": "Complete automatic expert selector and copy helper; ISO supplied through linear exposure slot.",
        "limitations": [
            "Calibration table initialization/JSON loading, Fast/manual modes, BPT/PDAF selection and live ISP submission remain separate.",
            "Malformed knot order is rejected by Rust before output mutation; native degenerate tables are outside the comparison.",
            "Profile-derived cases use its ISO grid with synthetic configuration bytes, not full profile initialization.",
            "Physical ARM replay does not enable DPCC on the camera.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
