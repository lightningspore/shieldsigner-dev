#!/usr/bin/env python3
"""Compare eight actual native interpolation calls and threshold-change detection."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, RETURN, regs


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.symbols["limits-checkpoint"] = 0xD43C5

    def hook(self, uc, address, size, user):
        if address == 0xD45F8:
            self.completed = True
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        c = bytearray(0x3700)
        cal = bytearray(0x200)
        record = bytearray([v["fill"]]) * 1204
        if "initial" in v:
            struct.pack_into("<8H", record, 0x4A, *v["initial"])
        c[0x2E90 : 0x2E90 + 1204] = record
        struct.pack_into("<I", c, 0x130, HEAP + 0x10000)
        struct.pack_into("<I", c, 0x33D8, v["brightness"])
        struct.pack_into("<II", cal, 0xF4, HEAP + 0x20000, len(v["knots"]))
        self.uc.mem_write(
            HEAP + 0x20000, struct.pack("<" + "f" * len(v["knots"]), *v["knots"])
        )
        for i, offset in enumerate(
            (0xFC, 0x104, 0x10C, 0x114, 0x11C, 0x124, 0x12C, 0x134)
        ):
            address = HEAP + 0x21000 + i * 0x100
            struct.pack_into("<I", cal, offset, address)
            self.uc.mem_write(
                address, struct.pack("<" + "f" * len(v["knots"]), *v["values"][i])
            )
        self.uc.mem_write(HEAP, bytes(c))
        self.uc.mem_write(HEAP + 0x10000, bytes(cal))
        self.uc.reg_write(regs.UC_ARM_REG_R4, HEAP + 0x2E90)
        self.uc.reg_write(regs.UC_ARM_REG_R5, HEAP)
        self.uc.reg_write(regs.UC_ARM_REG_R10, 1)
        self.completed = False
        self.invoke("limits-checkpoint")
        assert self.completed
        after = bytes(self.uc.mem_read(HEAP, len(c)))
        assert after[:0x2EDA] == c[:0x2EDA] and after[0x2EEA:] == c[0x2EEA:]
        assert bytes(self.uc.mem_read(HEAP + 0x10000, len(cal))) == cal
        return dict(
            changed=self.uc.reg_read(regs.UC_ARM_REG_R10) == 0,
            record=after[0x2E90 : 0x2E90 + 1204].hex(),
        )


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original()
    rng = random.Random(0x41574C49)
    cases = []
    expected = []
    for i in range(256):
        count = 1 + i % 5
        knots = [float(j * 1000) for j in range(count)]
        values = [[rng.uniform(-10, 70000) for _ in knots] for _ in range(8)]
        if i % 5 == 0:
            values = [[float(j * 16)] * count for j in range(8)]
        v = dict(
            knots=knots,
            values=values,
            brightness=[0, 500, 1000, 4500, 10000][i % 5],
            fill=i,
        )
        if i % 5 == 0:
            v["initial"] = [j * 16 for j in range(8)]
        cases.append(v)
        expected.append(arm.run(v))
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    table = wb["autoPara"]["limitRange"]
    v = dict(
        knots=table["lumaValue"],
        values=[
            [x * 16 for x in table[k]]
            for k in ("maxR", "minR", "maxG", "minG", "maxB", "minB", "maxY", "minY")
        ],
        brightness=8192,
        fill=0xA5,
        iq=wb,
    )
    cases.append(v)
    expected.append(arm.run(v))
    inputs = "".join(
        "awb-measurement-limits " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(cmd):
        actual = [
            json.loads(line)
            for line in subprocess.run(
                cmd, input=inputs, text=True, capture_output=True, check=True
            ).stdout.splitlines()
        ]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                a["changed"],
                b["changed"],
                next(
                    (
                        j // 2
                        for j, (x, y) in enumerate(zip(a["record"], b["record"]))
                        if x != y
                    ),
                    None,
                ),
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
        iqLoaderCases=1,
        unchangedCases=sum(not e["changed"] for e in expected),
        mismatches=0,
        arm="--arm" in sys.argv,
        nativeCheckpoint="ELF 0xc43c4 through 0xc45f8",
        scope="Eight original interpolation calls, complete SDK record preservation and native change flag",
        limitations=[
            "Group/update gate and input selector checks precede this checkpoint; luma weighting and scheduling follow it.",
            "Explicit seeded register/stack/calibration ownership; stops before ConfigIncludeWei, not full hardware reconfiguration return.",
            "Finite, strictly ascending calibration tables only.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-limits-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
