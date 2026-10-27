#!/usr/bin/env python3
"""Extract automatic LSC target grids from full native AlscAutoConfig."""

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
from differential import ROOT, BINARY, HEAP, regs, f32

illum = importlib.import_module("lsc-illuminant")


class OriginalTables(illum.OriginalIlluminant):
    def __init__(self):
        super().__init__()
        self.symbols["AlscAutoConfig"] = self.resolve_symbol("AlscAutoConfig", 0x1288A0)

    def string(self, address):
        result = bytearray()
        for offset in range(64):
            char = self.uc.mem_read(address + offset, 1)[0]
            if char == 0:
                return bytes(result)
            result.append(char)
        raise AssertionError("Unterminated oracle string")

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("strcmp", "strcpy"):
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            right = self.string(b)
            if name == "strcpy":
                uc.mem_write(a, right + b"\0")
                result = a
            else:
                left = self.string(a)
                result = (left > right) - (left < right)
            uc.reg_write(regs.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        # Build SDK-compatible calibration pointers; JSON parser/constructor are
        # explicitly outside this oracle, but all automatic math executes.
        self.bump = HEAP + 0x20000
        ctx, root = HEAP + 0x60000, HEAP + 0x19000
        self.uc.mem_write(ctx, bytes(0xD800))
        self.uc.mem_write(root, bytes(32))
        self.uc.mem_write(ctx, struct.pack("<I", root))
        pointers, handle, raw, resolution, tables = [
            HEAP + x for x in (0x1000, 0x2000, 0x4000, 0x18300, 0x18400)
        ]
        self.uc.mem_write(pointers, struct.pack("<I", handle))
        self.uc.mem_write(handle, struct.pack("<4I", raw, resolution, 1, 0))
        self.uc.mem_write(raw, bytes(68))
        self.uc.mem_write(raw + 36, struct.pack("<2f", 1.0, 1.0))
        n = len(value["gains"])
        self.uc.mem_write(
            raw + 52, struct.pack("<4I", HEAP + 0x18000, n, HEAP + 0x18100, n)
        )
        self.uc.mem_write(HEAP + 0x18000, struct.pack("<" + "f" * n, *value["gains"]))
        self.uc.mem_write(HEAP + 0x18100, struct.pack("<" + "f" * n, *value["vig"]))
        self.uc.mem_write(resolution, bytes(48))
        self.uc.mem_write(resolution, b"2304x1296\0")
        self.uc.mem_write(
            resolution + 40, struct.pack("<II", tables, len(value["profiles"]))
        )
        for i, p in enumerate(value["profiles"]):
            address = HEAP + 0x30000 + i * 4096
            self.uc.mem_write(tables + i * 4, struct.pack("<I", address))
            self.uc.mem_write(address, bytes(100))
            self.uc.mem_write(address, f"p{i}".encode() + b"\0")
            self.uc.mem_write(address + 96, struct.pack("<f", p["vignetting"]))
            self.uc.mem_write(address + 100, struct.pack("<1156H", *p["samples"]))
        assert (
            self.invoke(
                "OrderLscProfilesByVignetting", [tables, len(value["profiles"])]
            )
            == 0
        )
        self.uc.mem_write(ctx + 0x2C, struct.pack("<II", pointers, 1))
        self.uc.mem_write(ctx + 0x54, b"2304x1296\0")
        self.uc.mem_write(ctx + 0x7C, struct.pack("<3f", value["gain"], 1.0, 1.0))
        self.uc.mem_write(ctx + 0xC0, struct.pack("<II", ctx + 0xC0, ctx + 0xC0))
        self.uc.mem_write(
            ctx + 0xD794, b"\x01"
        )  # Force fresh target, frame zero => no damping.
        self.invoke("AlscAutoConfig", [ctx], instructions=300000)
        target = bytes(self.uc.mem_read(ctx + 0x110, 2312))
        # Native automatic no-OTP output also equals target with frame-zero damping.
        assert bytes(self.uc.mem_read(ctx + 0x1320, 2312)) == target
        return dict(
            high=int(self.string(ctx + 0xD0)[1:]),
            low=int(self.string(ctx + 0xF0)[1:]),
            vignetting=self.uc.mem_read(ctx + 0xBC, 4)[::-1].hex(),
            samples=target.hex(),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x4C534354)
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    lsc = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "lsc_v2"
    ]
    cases = []
    for ill in lsc["alscCoef"]["illAll"]:
        profiles = [
            p for p in lsc["tbl"]["tableAll"] if p["illumination"] == ill["name"]
        ]
        assert len(profiles) == 2
        grids = [
            dict(
                vignetting=p["vignetting"],
                samples=sum(
                    [
                        p[k]["uCoeff"]
                        for k in [
                            "lsc_samples_red",
                            "lsc_samples_greenR",
                            "lsc_samples_greenB",
                            "lsc_samples_blue",
                        ]
                    ],
                    [],
                ),
            )
            for p in profiles
        ]
        for gain in [0.0, *ill["gains"], 128.0, 1.5, 3.0, 9.0]:
            cases.append(
                dict(profiles=grids, gains=ill["gains"], vig=ill["vig"], gain=gain)
            )
    profile_cases = len(cases)
    for i in range(256):
        count = rng.randrange(1, 6)
        profiles = [
            dict(
                vignetting=f32(rng.randrange(1, 20) / 10),
                samples=[rng.randrange(65536) for _ in range(1156)],
            )
            for _ in range(count)
        ]
        # Include duplicates to check stable equal-key ordering and endpoint choice.
        rng.shuffle(profiles)
        gains = [1.0, 2.0, 4.0, 8.0]
        vig = [f32(rng.uniform(0, 3)) for _ in gains]
        gain = rng.choice([0.0, 1.0, 1.5, 3.0, 6.0, 16.0])
        if i % 4 == 0:
            vig = [rng.choice(profiles)["vignetting"]] * 4
        cases.append(dict(profiles=profiles, gains=gains, vig=vig, gain=gain))
    arm = OriginalTables()
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "lsc-tables " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert json.loads(got) == want, f"Host/native mismatch case {i}"
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
        cases=len(cases),
        selectedProfileCases=profile_cases,
        gridBytesComparedPerCase=2312,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Full native OrderLscProfilesByVignetting and AlscAutoConfig, fresh forced target, frame zero, no OTP. Compare interpolated vignetting bits, both original selected profile indices, all four 289-entry target grids and equality with native undamped output.",
        boundaries=[
            "SDK pointer graph constructed directly; constructor/parser and calibration name lookup are separate.",
            "Original nearest/history/interpolation/grid loops execute; modeled allocation/free, string operations, logging; original uClibc sqrtf.",
            "Finite gain curves, 1..5 profiles; persistent cache/damping/OTP and live LSC remain separate.",
            "Physical CPU replay makes no ISP writes.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
