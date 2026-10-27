#!/usr/bin/env python3
"""Full native chroma NR fixed-register quantization oracle."""

import argparse
import hashlib
import json
import importlib
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, regs, f32
from exposure import RUNTIME


class OriginalFix(OriginalArm):
    def __init__(self):
        assert (
            hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
            == "b62e80f7f6c3f104548c91a02429c2ca9734dada97179938240e2075778465fb"
        )
        self.math = OriginalArm(RUNTIME, tls=True)
        super().__init__(BINARY)
        self.stubs[self.symbols["cnr_fix_printf_V30"] & ~1] = "cnr_fix_printf_V30"
        self.math_calls = 0

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("log", "cnr_fix_printf_V30"):
            if name == "log":
                value = struct.unpack(
                    "<d", struct.pack("<Q", uc.reg_read(regs.UC_ARM_REG_D0))
                )[0]
                self.math.invoke("log", doubles=[value])
                uc.reg_write(
                    regs.UC_ARM_REG_D0, self.math.uc.reg_read(regs.UC_ARM_REG_D0)
                )
                self.math_calls += 1
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        selected, result, strength, exposure = [
            HEAP + x for x in (0, 0x10000, 0x11000, 0x12000)
        ]
        for name, address in [
            ("selected", selected),
            ("result", result),
            ("strength", strength),
            ("exposure", exposure),
        ]:
            self.uc.mem_write(address, bytes.fromhex(value[name]))
        assert (
            self.invoke("cnr_fix_transfer_V30", [selected, result, exposure, strength])
            == 0
        )
        for name, address in [
            ("selected", selected),
            ("strength", strength),
            ("exposure", exposure),
        ]:
            assert (
                self.uc.mem_read(address, len(bytes.fromhex(value[name]))).hex()
                == value[name]
            ), f"{name} mutated"
        return self.uc.mem_read(result, 66).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x434E5246)
    cases = []
    cal = json.loads(
        (
            ROOT
            / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
        ).read_text()
    )["main_scene"][0]["sub_scene"][0]["scene_isp32"]["cnr_v30"]
    prep = importlib.import_module("cnr-calibration").OriginalCalibration(BINARY)
    select = importlib.import_module("cnr-selection").OriginalSelection(BINARY)
    prepared = [
        prep.run(dict(calibration=cal, noise=noise, table=bytes(2396).hex()))["table"]
        for noise in ("LSNR", "HSNR")
    ]
    for case in range(1000):
        selected = bytearray(rng.randbytes(180))
        strength = bytearray(rng.randbytes(16))
        exposure = rng.randbytes(88)
        if case < 26:
            v = dict(
                table=prepared[case // 13],
                output=bytes(180).hex(),
                exposure=exposure.hex(),
                mode=0,
                iso=[50 * (1 << (case % 13)), 50, 50],
            )
            selected = bytearray.fromhex(select.run(v)["output"])
        else:
            selected[0] = case % 2
            selected[52] = (case // 2) % 2
            selected[1], selected[2] = [(2, 2), (4, 4), (8, 6), (255, 0)][case % 4]
            for p in [*range(4, 52, 4), *range(56, 180, 4)]:
                struct.pack_into("<f", selected, p, f32(rng.uniform(-2, 16)))
            # Keep ordinary filter widths representative while deliberately
            # exercising zero/negative/rounding-sensitive widths in edge cases.
            for p in (4, 12, 36):
                value = rng.uniform(0.002, 0.1)
                if case % 20 < 6:
                    value = [0.0, -0.01, 0.000001, 0.0004, 0.0039, 0.5][case % 20]
                struct.pack_into("<f", selected, p, f32(value))
        factor = (
            1.0
            if case < 26
            else rng.choice(
                [0.0, -0.5, 0.000001, 0.1, 0.5, 1.0, 2.0, 10.0, rng.uniform(0.01, 5)]
            )
        )
        struct.pack_into("<f", strength, 8, f32(factor))
        strength[12] = 1 if case < 26 else case % 2
        cases.append(
            dict(
                selected=selected.hex(),
                result=rng.randbytes(66).hex(),
                strength=strength.hex(),
                exposure=exposure.hex(),
            )
        )
    edge_start = len(cases)
    for offset, scale in [
        (4, 1023),
        (8, 1024),
        (12, 1023),
        (16, 8),
        (20, 64),
        (24, 16),
        (28, 128),
        (32, 1024),
        (36, 1023),
        (40, 16),
        (44, 128),
        (48, 128),
        (56, 1024),
        (60, 1),
        (64, 1024),
        (68, 16),
        (72, 8),
        (76, 128),
        (80, 64),
        (88, 64),
        (140, 128),
    ]:
        for threshold in [0.5, 1.5, 7.5, 15.5, 127.5, 255.5, 1023.5]:
            center = struct.unpack("<I", struct.pack("<f", threshold / scale))[0]
            for adjacent in [-1, 0, 1]:
                v = dict(cases[0])
                selected = bytearray.fromhex(v["selected"])
                struct.pack_into("<I", selected, offset, center + adjacent)
                v["selected"] = selected.hex()
                v["result"] = rng.randbytes(66).hex()
                cases.append(v)
    arm = OriginalFix()
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "cnr-fix " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert got == want, (
            f"Host/native mismatch case {i}: {[j for j, (a, b) in enumerate(zip(bytes.fromhex(got), bytes.fromhex(want))) if a != b]}"
        )
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
            "/shieldsigner-camera-tests/dev-0.0.34/cnr-" + uuid.uuid4().hex + ".txt"
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
        cases=len(cases),
        unalteredProfileCases=26,
        roundingBoundaryCases=len(cases) - edge_start,
        fixedRecordBytesComparedPerCase=66,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        logRuntimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        nativeLogCalls=arm.math_calls,
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Complete native cnr_fix_transfer_V30, all 66 fixed-result bytes including retained SDK padding; immutable selected, strength and exposure inputs. Original uClibc double log instructions execute.",
        boundaries=[
            "Diagnostic cnr_fix_printf_V30 suppressed; no algorithm/math substitutes.",
            "Original SC3336 profile selections plus varied finite strengths, scalars, filter modes, rounding/clipping edges, reversed gaussian weights and poisoned padding.",
            "Fixed conversion only; persistent controller and live CNR remain separate. Physical CPU replay loads no vendor library and makes no ISP writes.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
