#!/usr/bin/env python3
"""Compare native AWB measurement transform conversion and scene IQ loading."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP


def bits(x):
    return f"{struct.unpack('<I', struct.pack('<f', x))[0]:08x}"


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    arm = OriginalArm(BINARY)
    cases = []
    expected = []
    rng = random.Random(0x41575446)

    def add(weights, rotation, matrix):
        cases.append(
            dict(
                weights=list(map(bits, weights)),
                rotation=list(map(bits, rotation)),
                matrix=list(map(bits, matrix)),
            )
        )
        arm.uc.mem_write(HEAP, struct.pack("<12f", *(weights + rotation)))
        arm.uc.mem_write(HEAP + 0x1000, bytes([0xA5]) * 24)
        arm.invoke(
            next(n for n in arm.symbols if "JsonXyParaFixed1" in n),
            [HEAP, HEAP + 0x1000],
        )
        want = bytes(arm.uc.mem_read(HEAP + 0x1000, 24))
        arm.uc.mem_write(HEAP, struct.pack("<16f", *matrix))
        arm.uc.mem_write(HEAP + 0x1000, bytes([0xA5]) * 24)
        arm.invoke(
            next(n for n in arm.symbols if "JsonRtYuvParaFixed1" in n),
            [HEAP, HEAP + 0x1000],
        )
        expected.append((want + bytes(arm.uc.mem_read(HEAP + 0x1000, 24))).hex())

    t = wb["autoPara"]["rgb2TcsPara"]
    add(
        t["pseudoLuminanceWeight"],
        t["rotationMat"],
        wb["autoPara"]["rgb2RotationYuvMat"],
    )
    for i in range(256):
        weights = [rng.uniform(-1, 2) for _ in range(3)]
        rotation = [rng.uniform(-20, 20) for _ in range(9)]
        matrix = [rng.uniform(-5000, 5000) for _ in range(16)]
        if i % 4 == 0:
            weights = [0.0, 0.5, 1.0]
            rotation = [(j - 4 + 0.5) / 4096 for j in range(9)]
            matrix = [(j - 8 + 0.5) / 512 for j in range(16)]
        add(weights, rotation, matrix)
    inputs = "".join(
        "awb-measurement-transforms " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )
    inputs += (
        "awb-measurement-iq-transforms " + json.dumps(wb, separators=(",", ":")) + "\n"
    )
    expected.append(expected[0])

    def compare(cmd):
        actual = subprocess.run(
            cmd, input=inputs, text=True, capture_output=True, check=True
        ).stdout.splitlines()
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                next(j // 2 for j, (x, y) in enumerate(zip(a, b)) if x != y),
            )

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    if "--arm" in sys.argv:
        d = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        compare(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={d},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        iqSha256=iq_sha,
        nativeCases=len(cases),
        iqLoaderCases=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        elfEntries=["0xc8210", "0xc9050"],
        scope="Complete RGB-to-XY and rotated-YUV transform records, including native fixed-point helpers",
        limitations=[
            "Finite input domain; full measurement assembly and live statistics enable remain separate."
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-transforms-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
