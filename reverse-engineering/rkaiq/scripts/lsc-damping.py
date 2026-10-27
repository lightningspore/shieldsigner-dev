#!/usr/bin/env python3
"""Verify no-OTP LSC temporal damping through full native AlscAutoConfig."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, f32

reference = importlib.import_module("lsc-tables")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    profiles = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["lsc_v2"]["tbl"]["tableAll"]
    grids = [
        sum(
            [
                p[k]["uCoeff"]
                for k in (
                    "lsc_samples_red",
                    "lsc_samples_greenR",
                    "lsc_samples_greenB",
                    "lsc_samples_blue",
                )
            ],
            [],
        )
        for p in profiles
    ]
    rng = random.Random(0x4C534344)
    arm = reference.OriginalTables()
    # Check the recovered threshold directly in the pinned machine-code image.
    assert bytes(arm.uc.mem_read(0x128CB8, 4)) == struct.pack("<f", 0.015)
    cases, expected = [], []
    for seq in range(16):
        previous = [rng.randrange(65536) for _ in range(1156)]
        target = grids[seq % len(grids)]
        for frame in range(32):
            if frame == 16:
                target = grids[(seq + 5) % len(grids)]
            value = dict(
                previous=previous.copy(),
                target=target,
                factor=f32([0.0, 0.25, 0.5, 0.9, 0.99, 1.0][seq % 6]),
                enabled=seq % 7 != 0,
                frame=frame if seq % 4 == 0 else frame + 2,
            )
            if seq == 14:
                # Convergence checks only endpoints, including a strict .015 boundary.
                value["target"] = target = [rng.randrange(65536) for _ in range(1156)]
                value["previous"] = [rng.randrange(65536) for _ in range(1156)]
                target[0] = target[-1] = 197 if frame % 2 else 198
                value["previous"][0] = value["previous"][-1] = 203 if frame % 2 else 202
            elif seq == 15:
                target = value["target"] = [0] * 1156
                value["previous"] = [65535] * 1156
                if frame % 2 == 0:
                    value["previous"][0] = value["previous"][-1] = 0
            native = arm.run(
                dict(
                    profiles=[dict(vignetting=1.0, samples=target)],
                    gains=[1.0],
                    vig=[1.0],
                    gain=1.0,
                    damping=value,
                )
            )
            previous = list(struct.unpack("<1156H", bytes.fromhex(native["samples"])))
            cases.append(value)
            expected.append(native)
    lines = "".join(
        "lsc-damping " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert json.loads(got) == want, f"Host/native mismatch frame {i}"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
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
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/lsc-" + uuid.uuid4().hex + ".txt"
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
                assert output == actual, "Physical ARM mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        sequences=16,
        frames=len(cases),
        convergedFrames=sum(x["converged"] for x in expected),
        gridBytesComparedPerFrame=2312,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Complete native AlscAutoConfig, forced fresh target, no OTP. Compare all four damped planes and convergence. Persistent previous grids, target changes, frame 0/1 gating, enable gate, factors 0..1, strict .015 endpoint boundary, zero/zero endpoints and full u16 extremes.",
        boundaries=[
            "Constructed SDK calibration pointers and supplied prior grid; persistent controller cache/constructor and callback remain separate.",
            "Same allocation, string, logging and original sqrt runtime boundaries as lsc-tables oracle; no algorithm substitutes.",
            "Physical CPU replay only; no ISP writes or live image-quality qualification.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
