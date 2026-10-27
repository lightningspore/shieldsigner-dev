#!/usr/bin/env python3
"""Execute native nearest CCM illuminant selection."""

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


class OriginalIlluminant(OriginalArm):
    def __init__(self, path):
        super().__init__(path)
        self.stubs[self.symbols["xcam_print_log"] & ~1] = "xcam_print_log"

    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "xcam_print_log":
            from differential import regs

            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        source, gains, result = [HEAP + x for x in (0, 0x10000, 0x11000)]
        for i, p in enumerate(value["candidates"]):
            self.uc.mem_write(source + i * 56, bytes(56))
            self.uc.mem_write(source + i * 56 + 4, struct.pack("<2f", *p))
        self.uc.mem_write(gains, struct.pack("<2f", *value["gains"]))
        self.uc.mem_write(result, bytes.fromhex("a5a5a5a5"))
        status = self.invoke(
            "illuminant_index_estimation_ccm",
            [len(value["candidates"]), source, gains, result],
        )
        assert status in (0, 0xFFFFFFFF)
        return dict(
            index=struct.unpack("<I", self.uc.mem_read(result, 4))[0],
            matched=status == 0,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    rng = random.Random(0x43434D49)
    cases = [
        dict(candidates=[], gains=[1.0, 1.0]),
        dict(candidates=[[0.0, 0.0]], gains=[4000.0, 4000.0]),
        dict(candidates=[[0.0, 0.0], [2.0, 0.0]], gains=[1.0, 0.0]),
        dict(candidates=[[1.0, 1.0], [1.0, 1.0]], gains=[1.0, 1.0]),
    ]
    for _ in range(996):
        candidates = [
            [f32(rng.uniform(-10, 10)), f32(rng.uniform(-10, 10))]
            for _ in range(rng.randrange(1, 15))
        ]
        gains = (
            rng.choice(candidates)
            if rng.randrange(4) == 0
            else [f32(rng.uniform(-20, 20)), f32(rng.uniform(-20, 20))]
        )
        cases.append(dict(candidates=candidates, gains=gains))
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    tuning = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ccm_calib_v2"
    ]["TuningPara"]
    candidates = [[f32(v) for v in p["awbGain"]] for p in tuning["aCcmCof"]]
    profile_cases = 0
    for gains in candidates + [
        [f32((a + b) / 2) for a, b in zip(x, y)]
        for x, y in zip(candidates, candidates[1:])
    ]:
        cases.append(dict(candidates=candidates, gains=gains))
        profile_cases += 1
    arm = OriginalIlluminant(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-illuminant " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-illuminant-"
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
        seed="0x43434d49",
        scope="Complete native illuminant_index_estimation_ccm; selected index and success/no-match status. Diagnostic logging is the sole modeled dependency.",
        limitations=[
            "Finite calibrated/current gain pairs; nonfinite Rust inputs rejected.",
            "Gain-to-saturation calibration, temporal state and live CCM remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
