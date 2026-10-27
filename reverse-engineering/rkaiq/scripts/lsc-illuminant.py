#!/usr/bin/env python3
"""Native LSC nearest selection and intrusive 15-frame history oracle."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, regs, f32, u32
from exposure import RUNTIME


class OriginalIlluminant(OriginalArm):
    def __init__(self):
        self.math = OriginalArm(RUNTIME, tls=True)
        super().__init__(BINARY)
        self.stubs[self.symbols["xcam_print_log"] & ~1] = "xcam_print_log"
        for name, entry in [
            ("illuminant_index_estimation", 0x128498),
            ("UpdateDominateIlluList", 0x128528),
            ("StableIlluEstimation", 0x128576),
        ]:
            self.symbols[name] = self.resolve_symbol(name, entry)
        self.bump = HEAP + 0x20000

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("malloc", "free", "sqrtf", "xcam_print_log"):
            if name == "malloc":
                count = uc.reg_read(regs.UC_ARM_REG_R0)
                assert 0 < count <= 28
                pointer = self.bump
                self.bump += (count + 7) & ~7
                assert self.bump < HEAP + 0xF0000
                uc.mem_write(pointer, bytes(count))
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            elif name == "free":
                assert HEAP + 0x20000 <= uc.reg_read(regs.UC_ARM_REG_R0) < self.bump
            elif name == "sqrtf":
                value = struct.unpack(
                    "<f", struct.pack("<I", uc.reg_read(regs.UC_ARM_REG_S0))
                )[0]
                self.math.invoke("sqrtf", floats=[value])
                uc.reg_write(
                    regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0)
                )
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        self.bump = HEAP + 0x20000
        count = len(value["calibrated"])
        self.uc.mem_write(HEAP, struct.pack("<II", HEAP + 0x1000, count))
        for i, gains in enumerate(value["calibrated"]):
            handle, raw = HEAP + 0x2000 + i * 32, HEAP + 0x4000 + i * 256
            self.uc.mem_write(HEAP + 0x1000 + i * 4, struct.pack("<I", handle))
            self.uc.mem_write(handle, struct.pack("<I", raw))
            self.uc.mem_write(raw + 36, struct.pack("<2f", *gains))
        head, current, out = HEAP + 0x10000, HEAP + 0x11000, HEAP + 0x11100
        self.uc.mem_write(head, struct.pack("<II", head, head))
        results = []
        for frame in value["frames"]:
            self.uc.mem_write(current, struct.pack("<2f", *frame))
            self.uc.mem_write(out, struct.pack("<I", 0xA5A5A5A5))
            status = self.invoke("illuminant_index_estimation", [HEAP, current, out])
            nearest = u32(self.uc.mem_read(out, 4))
            assert status in (0, 0xFFFFFFFF)
            if status == 0:
                self.invoke("UpdateDominateIlluList", [head, nearest, 15])
                self.invoke("StableIlluEstimation", [head, 15, count, out])
                selected = u32(self.uc.mem_read(out, 4))
            else:
                assert nearest == 0xA5A5A5A5
                nearest = selected = None
            history = []
            previous, node = head, u32(self.uc.mem_read(head, 4))
            while node != head:
                following, backward, index = struct.unpack(
                    "<III", self.uc.mem_read(node, 12)
                )
                assert backward == previous and len(history) < 15
                history.append(index)
                previous, node = node, following
            assert u32(self.uc.mem_read(head + 4, 4)) == previous
            results.append(
                dict(
                    nearest=nearest,
                    selected=selected,
                    stable=status == 0 and len(history) == 15,
                    history=history,
                )
            )
        return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == "b62e80f7f6c3f104548c91a02429c2ca9734dada97179938240e2075778465fb"
    )
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    ill = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "lsc_v2"
    ]["alscCoef"]["illAll"]
    profile = [p["wbGain"] for p in ill]
    rng = random.Random(0x4C534349)
    cases = [
        dict(calibrated=[], frames=[[1.0, 1.0]] * 32),
        dict(calibrated=[[0.0, 0.0]], frames=[[20_000_000.0, 0.0], [0.0, 0.0]] * 32),
        dict(
            calibrated=[[0.0, 0.0], [2.0, 0.0], [4.0, 0.0]],
            frames=[[float(i % 3) * 2, 0.0] for i in range(64)],
        ),
        dict(calibrated=[[0.0, 0.0], [2.0, 0.0]], frames=[[1.0, 0.0]] * 64),
    ]
    for i in range(100):
        cal = (
            profile
            if i < 10
            else [
                [f32(rng.uniform(-10, 10)), f32(rng.uniform(-10, 10))]
                for _ in range(rng.randrange(1, 8))
            ]
        )
        frames = [
            rng.choice(cal)
            if rng.randrange(3)
            else [f32(rng.uniform(-10, 10)), f32(rng.uniform(-10, 10))]
            for _ in range(64)
        ]
        cases.append(dict(calibrated=cal, frames=frames))
    arm = OriginalIlluminant()
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "lsc-illuminant " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert json.loads(got) == want, f"Host/native mismatch sequence {i}"
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
        sequences=len(cases),
        frames=sum(len(c["frames"]) for c in cases),
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        sqrtRuntimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        selectedProfileSequences=10,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Complete native nearest estimation, UpdateDominateIlluList and StableIlluEstimation; original uClibc sqrtf. Compare each selected index and full ordered intrusive history including backward links. Empty/no-match and 15-frame mode/ties covered.",
        boundaries=[
            "Modeled malloc/free arena and suppressed logging; no algorithm stubs.",
            "Finite inputs, at most seven illuminants; calibration changes require history reset.",
            "Physical CPU replay only; automatic table interpolation and live LSC remain separate.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
