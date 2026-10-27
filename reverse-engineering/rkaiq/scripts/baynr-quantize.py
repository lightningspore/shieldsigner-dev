#!/usr/bin/env python3
"""Full native Bayer spatial NR fixed-register quantization oracle."""

import argparse
import hashlib
import json
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
        self.stubs[self.symbols["bayer2dnr_fix_printf_V23"] & ~1] = (
            "bayer2dnr_fix_printf_V23"
        )
        self.math_calls = 0

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("expf", "bayer2dnr_fix_printf_V23"):
            if name == "expf":
                value = struct.unpack(
                    "<f", struct.pack("<I", uc.reg_read(regs.UC_ARM_REG_S0))
                )[0]
                self.math.invoke("expf", floats=[value])
                uc.reg_write(
                    regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0)
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
            self.invoke(
                "bayer2dnr_fix_transfer_V23", [selected, result, strength, exposure]
            )
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
        return self.uc.mem_read(result, 152).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x42415946)
    cases = []
    for case in range(1000):
        selected = bytearray(rng.randbytes(252))
        exposure = bytearray(rng.randbytes(88))
        strength = bytearray(rng.randbytes(16))
        selected[0] = case % 2
        selected[132] = (case // 2) % 2
        selected[156] = case % 4
        selected[168] = (case // 4) % 2
        selected[240] = (case // 8) % 2
        for p in (136, 140, 144, 148, 172, 244, 248):
            value = rng.uniform(0.01, 16)
            if case % 20 < 10:
                value = [0.0, 0.001, 0.5, 1.0, 2.0, 16.0, 32.0, -1.0, -10.0, 0.01][
                    case % 20
                ]
            struct.pack_into("<f", selected, p, f32(value))
        for i in range(16):
            struct.pack_into(
                "<i",
                selected,
                4 + i * 4,
                rng.choice([-1, 0, 1, 65535, 65536, rng.randrange(65536)]),
            )
            struct.pack_into("<i", selected, 68 + i * 4, rng.randrange(-1000, 100000))
        struct.pack_into("<i", exposure, 0, case % 3)
        struct.pack_into("<i", exposure, 8, (case // 3) % 2)
        struct.pack_into("<i", exposure, 12, (case // 6) % 2)
        struct.pack_into(
            "<3f", exposure, 16, *[f32(rng.uniform(0.00001, 1)) for _ in range(3)]
        )
        struct.pack_into("<f", exposure, 64, [-1.0, 0.0, 1.0, 2.0][case % 4])
        struct.pack_into(
            "<3i", exposure, 68, *[rng.randrange(1, 204801) for _ in range(3)]
        )
        struct.pack_into(
            "<f",
            strength,
            8,
            f32(
                rng.choice(
                    [
                        0.0,
                        -0.5,
                        0.000001,
                        0.1,
                        0.5,
                        1.0,
                        2.0,
                        10.0,
                        rng.uniform(0.01, 5),
                    ]
                )
            ),
        )
        strength[12] = case % 2
        cases.append(
            dict(
                selected=selected.hex(),
                result=rng.randbytes(152).hex(),
                strength=strength.hex(),
                exposure=exposure.hex(),
            )
        )
    arm = OriginalFix()
    expected = [arm.run(v) for v in cases]
    assert arm.math_calls == 8 * len(cases)
    lines = "".join(
        "baynr-fix " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/baynr-" + uuid.uuid4().hex + ".txt"
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
        fixedRecordBytesComparedPerCase=152,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        expRuntimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        nativeExpCalls=arm.math_calls,
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Complete native bayer2dnr_fix_transfer_V23 with original uClibc expf. Every fixed-result byte compared including padding and inactive digital-gain slots; selected/strength/exposure inputs checked unchanged.",
        boundaries=[
            "Only final diagnostic printer suppressed; no algorithm or math substitutes.",
            "Finite selected/strength metadata, exposure mode 0..2, positive finite ISO*time products. Zero/nonpositive strength, zero filter/edge, negative/out-of-range tuning, HDR gain control, gray spatial weights, BAY3D flags and BLC predgain gates included.",
            "Synthetic SDK records; actual calibration/strength policy, persistent controller and live BAYNR remain separate. HDR/gray arithmetic coverage is not camera qualification.",
            "Physical CPU replay makes no ISP writes and loads no vendor library.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
