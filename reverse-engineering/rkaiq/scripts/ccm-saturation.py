#!/usr/bin/env python3
"""Compare CCM saturation adjustment with original ARM instructions."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid

from differential import ROOT, BINARY, HEAP, OriginalArm


class OriginalSaturation(OriginalArm):
    def run(self, value):
        self.uc.mem_write(HEAP, struct.pack("<9f", *value["matrix"]))
        self.invoke("Saturationadjust", [HEAP], [value["alpha"], value["saturation"]])
        return bytes(self.uc.mem_read(HEAP, 36)).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1000)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert 4 <= args.cases <= 4096
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x43434D41)
    cases = []
    for index in range(args.cases):
        matrix = [rng.uniform(-4, 4) for _ in range(9)]
        if index < 20:
            matrix = [float(i % 4 == 0) for i in range(9)]
        alpha = (
            rng.choice([0.0, 0.000009, 0.00001, 0.000011, 0.01, 0.5, 1.0])
            if index < 100
            else rng.random()
        )
        saturation = (
            rng.choice([0.0, 25.0, 50.0, 75.0, 100.0])
            if index < 100
            else rng.uniform(0, 100)
        )
        cases.append(dict(matrix=matrix, alpha=alpha, saturation=saturation))
    arm = OriginalSaturation(BINARY)
    expected = [arm.run(value) for value in cases]
    lines = "".join(
        "ccm-saturation " + json.dumps(value, separators=(",", ":")) + "\n"
        for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, "Host/native CCM mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-" + uuid.uuid4().hex + ".txt"
        )
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
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
                output = subprocess.check_output(
                    adb + ["shell", board + " < " + remote], text=True
                ).splitlines()
                assert output == actual, "Physical ARM/native CCM mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 36,
        "mismatches": 0,
        "seed": "0x43434d41",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Complete native Saturationadjust, all nine output float bit patterns; alpha [0,1] and saturation [0,100].",
        "limitations": [
            "Calibrated alpha/saturation ownership and live CCM integration remain separate.",
            "Physical ARM replay does not enable CCM on the camera or qualify image quality.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
