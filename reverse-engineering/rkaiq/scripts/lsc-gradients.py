#!/usr/bin/env python3
"""Compare native LSC sector-gradient calculation and context preservation."""

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


class OriginalGradients(OriginalArm):
    def run(self, value):
        rng = random.Random(value["seed"])
        self.uc.mem_write(HEAP, rng.randbytes(0x1D00))
        self.uc.mem_write(HEAP + 0x1CB8, struct.pack("<16H", *value["x"]))
        self.uc.mem_write(HEAP + 0x1CD8, struct.pack("<16H", *value["y"]))
        before = bytes(self.uc.mem_read(HEAP, 0x1D00))
        assert self.invoke("AlscManualGrad", [HEAP]) == 0
        after = bytearray(self.uc.mem_read(HEAP, 0x1D00))
        result = bytes(after[0x1C28:0x1C68]).hex()
        after[0x1C28:0x1C68] = before[0x1C28:0x1C68]
        assert bytes(after) == before, "Unexpected geometry context mutation"
        return result


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
    rng = random.Random(0x4C534347)
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    resolution = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["lsc_v2"]["common"]["resolutionAll"][0]
    cases = [
        dict(x=resolution["lsc_sect_size_x"], y=resolution["lsc_sect_size_y"], seed=0)
    ]
    for index in range(args.cases - 1):
        x = [rng.randrange(1, 65536) for _ in range(16)]
        y = [rng.randrange(1, 65536) for _ in range(16)]
        if index < 32:
            x = [1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 127, 128, 255, 256, 32768, 65535]
            rng.shuffle(x)
        cases.append(dict(x=x, y=y, seed=rng.randrange(0xFFFFFFFF)))
    arm = OriginalGradients(BINARY)
    expected = [arm.run(value) for value in cases]
    lines = "".join(
        "lsc-gradients " + json.dumps(value, separators=(",", ":")) + "\n"
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
        "bytesComparedPerCase": 64,
        "mismatches": 0,
        "seed": "0x4c534347",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Complete native AlscManualGrad, all 32 u16 gradient values and preservation of every other context byte. Actual selected-resolution sectors plus varied positive u16 lengths.",
        "limitations": [
            "Automatic resolution/sector selection and live LSC remain separate. Zero lengths rejected before Rust output; native partial-error writes are not replicated.",
            "Physical ARM replay does not enable LSC on the camera or qualify image quality.",
        ],
    }
    report["iqSha256"] = hashlib.sha256(iq.read_bytes()).hexdigest()
    report["selectedProfileCases"] = 1
    report["resolutionName"] = resolution["name"]
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
