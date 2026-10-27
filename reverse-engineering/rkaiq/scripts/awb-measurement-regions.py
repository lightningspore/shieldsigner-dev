#!/usr/bin/env python3
"""Execute native XY and rotated-YUV quantizers against complete Rust records."""

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
    arm = OriginalArm(BINARY)
    rng = random.Random(0x41575247)
    cases = []
    expected = []

    def add(xy, u, threshold, line, distance, fill):
        v = dict(
            xy=list(map(bits, xy)),
            u=list(map(bits, u)),
            threshold=list(map(bits, threshold)),
            line=list(map(bits, line)),
            distance=distance,
            fill=fill,
        )
        arm.uc.mem_write(HEAP, struct.pack("<8f", *xy))
        arm.uc.mem_write(HEAP + 0x1000, bytes([fill]) * 48)
        arm.invoke(
            next(n for n in arm.symbols if "JsonXyParaFixed3" in n),
            [HEAP, HEAP + 0x1000],
        )
        want = bytes(arm.uc.mem_read(HEAP + 0x1000, 48))
        arm.uc.mem_write(
            HEAP, struct.pack("<18fB3x", *(u + threshold + line), distance)
        )
        arm.uc.mem_write(HEAP + 0x1000, bytes([fill]) * 32)
        arm.invoke(
            next(n for n in arm.symbols if "JsonRtYuvParaFixed2" in n),
            [HEAP, HEAP + 0x1000],
        )
        cases.append(v)
        expected.append((want + bytes(arm.uc.mem_read(HEAP + 0x1000, 32))).hex())

    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    lights = wb["autoPara"]["lightSources"]
    for light in lights:
        x = light["xyRegion"]
        y = light["rtYuvRegion"]
        add(
            x["normal"] + x["big"],
            y["thcurve_u"],
            y["thcure_th"],
            y["lineVector"],
            y["disP1P2"],
            0,
        )
    for i in range(256):
        xy = [rng.uniform(-40, 40) for _ in range(8)]
        if i % 4 == 0:
            xy = [(j - 4 + 0.5) / 1024 for j in range(8)]
        add(
            xy,
            [rng.uniform(-10, 300) for _ in range(6)],
            [rng.uniform(-5, 5000) for _ in range(6)],
            [rng.uniform(-100, 5000) for _ in range(6)],
            i,
            i,
        )
    inputs = "".join(
        "awb-measurement-regions " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    inputs += (
        "awb-measurement-iq-regions " + json.dumps(wb, separators=(",", ":")) + "\n"
    )
    expected.append("".join(expected[: len(lights)]))

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
        realIqLights=len(lights),
        iqLoaderCases=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Complete 48-byte XY and 32-byte rotated-YUV records including preserved fields",
        limitations=[
            "UV polygon conversion and initial complete measurement assembly remain separate.",
            "Finite inputs only; native nonfinite conversion behavior is rejected.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-regions-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
