#!/usr/bin/env python3
"""Compare full native ConfigIncludeWei with scene-loaded extra-region curves."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = OriginalArm(BINARY)
    rng = random.Random(0x41574558)
    cases = []
    expected = []

    def add(v):
        iq = bytearray(0x300)
        for i, r in enumerate(v["regions"]):
            at = i * 40
            knots = HEAP + 0x10000 + i * 0x100
            weights = HEAP + 0x20000 + i * 0x100
            struct.pack_into("<I", iq, 0x13C + at, r["mode"])
            struct.pack_into(
                "<IIII",
                iq,
                0x150 + at,
                knots,
                len(r["knots"]),
                weights,
                len(r["weights"]),
            )
            arm.uc.mem_write(
                knots, struct.pack("<" + "f" * len(r["knots"]), *r["knots"])
            )
            arm.uc.mem_write(
                weights, struct.pack("<" + "f" * len(r["weights"]), *r["weights"])
            )
        arm.uc.mem_write(HEAP, bytes(iq))
        arm.uc.mem_write(HEAP + 0x5000, bytes([0xA5]) * 1204)
        arm.invoke(
            next(n for n in arm.symbols if "ConfigIncludeWei" in n),
            [HEAP, HEAP + 0x5000],
            floats=[v["brightness"]],
        )
        assert bytes(arm.uc.mem_read(HEAP, len(iq))) == iq
        cases.append(v)
        expected.append(bytes(arm.uc.mem_read(HEAP + 0x5000, 1204)).hex())

    for i in range(128):
        regions = []
        for j in range(7):
            n = 1 + (i + j) % 5
            regions.append(
                dict(
                    mode=1 if j == 0 or (i + j) % 3 else 3,
                    knots=[float(k * 1000) for k in range(n)],
                    weights=[rng.uniform(-0.25, 1.5) for _ in range(n)],
                )
            )
        add(
            dict(
                brightness=[0.0, 500.0, 1000.0, 2500.0, 10000.0][i % 5], regions=regions
            )
        )
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    regions = [
        dict(
            mode=1 if r["mode"] == "CALIB_AWB_EXCLUDE_WP_MODE" else 3,
            knots=r["weightInculde"]["lumaValue"],
            weights=r["weightInculde"]["weight"],
        )
        for r in wb["autoPara"]["extraWpRange"]
    ]
    add(dict(brightness=8192.0, regions=regions, iq=wb))
    inputs = "".join(
        "awb-measurement-exclusions " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(command):
        actual = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
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
        cases=len(cases),
        iqLoaderCases=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Complete native ConfigIncludeWei through return, seven weights and SDK record preservation",
        limitations=[
            "The first region is mode 1; native first-mode-3 stack value is uninitialized and the Rust API rejects it.",
            "Static region initialization and complete startup composition remain separate from this weight-equivalence comparison.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-exclusions-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
