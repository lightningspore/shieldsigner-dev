#!/usr/bin/env python3
"""Execute native symmetric CCM luma-curve generation."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, regs
from exposure import RUNTIME


def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


class OriginalLuma(OriginalArm):
    def __init__(self, path):
        super().__init__(path)
        self.math = OriginalArm(RUNTIME, tls=True)
        self.floor_calls = 0

    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "floorf":
            value = struct.unpack(
                "<f", struct.pack("<I", uc.reg_read(regs.UC_ARM_REG_S0))
            )[0]
            self.math.invoke("floorf", floats=[value])
            self.floor_calls += 1
            uc.reg_write(regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0))
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        table, curve, updated = [HEAP + x for x in (0, 0x10000, 0x20000)]
        for i, row in enumerate(value["rows"]):
            self.uc.mem_write(
                table + i * 72, struct.pack("<18f", row["iso"], *row["curve"])
            )
        self.uc.mem_write(curve, struct.pack("<17f", *value["curve"]))
        self.uc.mem_write(updated, bytes([0xA5]))
        assert (
            self.invoke(
                "YAlpSymAutoCfg",
                [
                    len(value["rows"]),
                    table,
                    value["previousUpper"],
                    int(value["force"]),
                ],
                [value["previousWeight"], value["iso"]],
                stack=struct.pack("<II", curve, updated),
            )
            == 0
        )
        return dict(
            updated=bool(self.uc.mem_read(updated, 1)[0]),
            curve=bytes(self.uc.mem_read(curve, 68)).hex(),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == manifest["uclibcRuntime"]["memberSha256"]
    )
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x43434D4C)
    cases = []
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    source = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ccm_calib_v2"
    ]["lumaCCM"]["y_alp_sym"]["gain_yalp_curve"]
    actual = [dict(iso=r["iso"], curve=r["y_alpha_curve"]) for r in source]
    for i in range(1000):
        rows = (
            actual
            if i < 100
            else [
                dict(
                    iso=float(50 * (j + 1)),
                    curve=[rng.randrange(1025) for _ in range(17)],
                )
                for j in range(rng.randrange(2, 14))
            ]
        )
        iso = f32(
            rng.choice(
                [
                    rows[0]["iso"] - 1,
                    rows[-1]["iso"] + 1,
                    rng.choice(rows)["iso"],
                    rng.uniform(rows[0]["iso"], rows[-1]["iso"]),
                ]
            )
        )
        cases.append(
            dict(
                rows=rows,
                iso=iso,
                curve=[rng.randrange(1025) for _ in range(17)],
                previousWeight=f32(rng.choice([0.0, 0.5, 1.0, rng.random()])),
                previousUpper=rng.randrange(len(rows)),
                force=i % 3 == 0,
            )
        )
    for change in [0, 1, 2]:
        row = [10.0] * 17
        row[0] += change
        cases.append(
            dict(
                rows=[dict(iso=50.0, curve=row), dict(iso=100.0, curve=row)],
                iso=50.0,
                curve=[10.0] * 17,
                previousWeight=0.0,
                previousUpper=1,
                force=True,
            )
        )
    profile_cases = 100
    arm = OriginalLuma(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-luma " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-luma-"
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
        selectedProfileCases=profile_cases,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        seed="0x43434d4c",
        scope="Complete native YAlpSymAutoCfg and pinned uClibc floorf; all 68 curve bytes and update flag.",
        limitations=[
            "Finite ordered tables of at least two rows; malformed Rust inputs rejected.",
            "Asymmetric curves, caller-owned prior bracket/weight and live CCM remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    report["floorCalls"] = arm.floor_calls
    report["uclibcRuntimeSha256"] = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    report["updatedCases"] = sum(v["updated"] for v in expected)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
