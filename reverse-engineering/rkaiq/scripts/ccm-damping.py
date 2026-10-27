#!/usr/bin/env python3
"""Execute native CCM Damping sequences."""

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


def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


class OriginalDamping(OriginalArm):
    def __init__(self, path):
        super().__init__(path)
        self.symbols["ccm-damping"] = self.resolve_symbol("Damping", 0x10D6F8)

    def run(self, value):
        target, cache, converged = [HEAP + x for x in (0, 0x1000, 0x2000)]
        self.uc.mem_write(cache, struct.pack("<12f", *value["initial"]))
        output = []
        for frame in value["frames"]:
            self.uc.mem_write(target, struct.pack("<12f", *frame["target"]))
            self.uc.mem_write(converged, bytes([0xA5]))
            assert (
                self.invoke(
                    "ccm-damping",
                    [target, cache, target + 36, cache + 36],
                    [frame["damping"]],
                    stack=struct.pack("<I", converged),
                )
                == 0
            )
            output.append(
                dict(
                    result=bytes(self.uc.mem_read(cache, 48)).hex(),
                    converged=bool(self.uc.mem_read(converged, 1)[0]),
                )
            )
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    rng = random.Random(0x43434D44)
    cases = []
    for sequence in range(100):
        initial = [f32(rng.uniform(-100, 100)) for _ in range(12)]
        frames = []
        target = [f32(rng.uniform(-100, 100)) for _ in range(12)]
        for i in range(32):
            if sequence < 10:
                target = initial.copy()
                target[(sequence + i) % 12] = f32(
                    target[(sequence + i) % 12]
                    + rng.choice([0.0, 0.000009, 0.00001, 0.000011, -0.000011])
                )
            elif i % 8 == 0:
                target = [f32(rng.uniform(-100, 100)) for _ in range(12)]
            damping = [0.0, 1.0, 0.5, 0.9, 0.99][(sequence + i // 8) % 5]
            frames.append(dict(target=target.copy(), damping=f32(damping)))
        cases.append(dict(initial=initial, frames=frames))
    arm = OriginalDamping(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-damping " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = [
        json.loads(line)
        for line in subprocess.check_output(
            [str(binary)], input=lines, text=True
        ).splitlines()
    ]
    for i, (a, b) in enumerate(zip(actual, expected)):
        assert a == b, (i, a, b, cases[i])
    assert len(actual) == len(expected)
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-damping-"
            + uuid.uuid4().hex
            + ".txt"
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
                output = [
                    json.loads(line)
                    for line in subprocess.check_output(
                        adb + ["shell", board + " < " + remote], text=True
                    ).splitlines()
                ]
                assert output == actual
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        cases=len(cases),
        frames=sum(len(v["frames"]) for v in cases),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        seed="0x43434d44",
        scope="Complete native CCM Damping routine across persistent 32-frame sequences; all 48 matrix/offset bytes and convergence flag. No numerical or external-call stubs.",
        limitations=[
            "Finite matrix/offset inputs and damping in [0,1]; invalid Rust inputs rejected atomically.",
            "Outer-frame scheduling, damping-factor ownership and live CCM remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
