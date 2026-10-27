#!/usr/bin/env python3
"""Execute native CCM AE/AWB input deadband sequences."""

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


class OriginalInput(OriginalArm):
    def run(self, value):
        baseline, current = HEAP, HEAP + 12
        self.uc.mem_write(baseline, struct.pack("<3f", *value["baseline"]))
        output = []
        for frame in value["frames"]:
            self.uc.mem_write(current, struct.pack("<3f", *frame["current"]))
            status = self.invoke(
                "JudgeCcmRes3aConverge",
                [baseline, current],
                [frame["gainTolerance"], frame["wbTolerance"]],
            )
            assert status in (0, 1)
            output.append(
                dict(
                    records=bytes(self.uc.mem_read(baseline, 24)).hex(),
                    changed=bool(status),
                )
            )
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    rng = random.Random(0x43434D49)
    cases = []
    for sequence in range(100):
        baseline = [1.0, 1.0, 1.0]
        frames = []
        for i in range(32):
            gain_tolerance, wb_tolerance = (
                [0.2, 0.0]
                if sequence < 10
                else rng.choice([[0.0, 0.0], [0.2, 0.1], [1.0, 1.0], [0.01, 0.05]])
            )
            if i % 8 == 0:
                current = baseline.copy()
            elif i % 8 == 1:
                current = [
                    baseline[0] + gain_tolerance,
                    baseline[1] + wb_tolerance,
                    baseline[2],
                ]
            elif i % 8 == 2:
                current = [baseline[0], baseline[1] + 0.03, baseline[2] + 0.04]
            else:
                current = [
                    rng.uniform(0.5, 8),
                    rng.uniform(0.5, 4),
                    rng.uniform(0.5, 4),
                ]
            frames.append(
                dict(
                    current=[f32(v) for v in current],
                    gainTolerance=f32(gain_tolerance),
                    wbTolerance=f32(wb_tolerance),
                )
            )
        cases.append(dict(baseline=baseline, frames=frames))
    arm = OriginalInput(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-input " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-input-"
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
        seed="0x43434d49",
        scope="Complete native JudgeCcmRes3aConverge across persistent 32-frame sequences; all 24 input/baseline bytes and change flag. No numerical or external-call stubs.",
        limitations=[
            "Finite records and nonnegative tolerances; invalid Rust inputs rejected atomically.",
            "Joined outer CCM controller and live submission remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
