#!/usr/bin/env python3
"""Compare full native post-assembly binding for linear BayerNR/Gain1/no OTP."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, regs


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.logging = {
            p & ~1 for n, p in self.symbols.items() if n == "xcam_print_log"
        }

    def hook(self, uc, address, size, user):
        if address in self.logging:
            uc.reg_write(regs.UC_ARM_REG_R0, 0)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        c = bytearray(0x3700)
        cal = bytearray(0x100)
        remosaic = bytearray(20)
        blc = bytearray(32)
        struct.pack_into("<I", c, 0x88, HEAP + 0x10000)
        struct.pack_into("<I", c, 0x130, HEAP + 0x20000)
        struct.pack_into("<I", c, 0x3644, 1)
        struct.pack_into("<f", c, 0x5C, 100.0)
        struct.pack_into("<f", c, 0x60, v["digital_gain"])
        struct.pack_into("<4f", c, 0x354C, 1.5, 1.0, 1.0, 2.0)
        if v["software"] is not None:
            c[0x36A0] = 1
            struct.pack_into("<4f", c, 0x36BC, *v["software"])
        if v["remosaic"] is not None:
            remosaic[0] = remosaic[1] = 1
            struct.pack_into("<4f", remosaic, 4, *v["remosaic"])
        if v["blc"] is not None:
            b = v["blc"]
            struct.pack_into("<I", c, 0x6C, HEAP + 0x30000)
            blc[0] = b["enabled"]
            blc[10] = b["stage1_enabled"]
            struct.pack_into("<4h", blc, 2, *b["fixed"])
            struct.pack_into("<4h", blc, 12, *b["stage1"])
            struct.pack_into("<h", blc, 22, b["offset"])
            struct.pack_into("<f", blc, 24, b["gain"])
        cal[0xC] = 1
        struct.pack_into("<II", cal, 0x10, HEAP + 0x40000, 1)
        self.uc.mem_write(HEAP + 0x40000, struct.pack("<f", 50.0))
        for i, at in enumerate((0x18, 0x20, 0x28, 0x30)):
            pointer = HEAP + 0x40100 + i * 16
            struct.pack_into("<I", cal, at, pointer)
            self.uc.mem_write(pointer, struct.pack("<f", v["offsets"][i]))
        record = bytearray([0xA5]) * 1204
        record[0x3E] = 3
        for offset, data in (
            (0, c),
            (0x10000, remosaic),
            (0x20000, cal),
            (0x30000, blc),
            (0x50000, record),
            (0x60000, bytes([0xA5]) * 20),
        ):
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.invoke(
            next(n for n in self.symbols if "AwbReCfgPregnBlc" in n),
            [HEAP, 0, HEAP + 0x60000, HEAP + 0x50000],
        )
        assert bytes(self.uc.mem_read(HEAP, len(c))) == c
        assert bytes(self.uc.mem_read(HEAP + 0x60000, 16)) == struct.pack(
            "<4f", 1.5, 1.0, 1.0, 2.0
        )
        return bytes(self.uc.mem_read(HEAP + 0x50000, 1204)).hex()


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original()
    rng = random.Random(0x41574249)
    cases = []
    expected = []
    for i in range(128):
        blc = (
            None
            if i % 7 == 0
            else dict(
                enabled=bool(i % 2),
                fixed=[rng.randrange(0, 512) for _ in range(4)],
                stage1_enabled=bool(i % 3),
                stage1=[rng.randrange(0, 512) for _ in range(4)],
                offset=i % 64,
                gain=[0.5, 1.0, 1.333, 2.0][i % 4],
            )
        )
        v = dict(
            blc=blc,
            offsets=[rng.uniform(-10, 300) for _ in range(4)],
            digital_gain=[1.0, 1.5, 2.0][i % 3],
            remosaic=None if i % 3 else [1.5, 1.0, 1.0, 2.0],
            software=None if i % 4 else [1.25, 1.0, 1.0, 1.125],
        )
        cases.append(v)
        expected.append(arm.run(v))
    # Current camera checkpoint's actual BLC settings and disabled AWB BLC2.
    v = dict(
        blc=dict(
            enabled=False,
            fixed=[0] * 4,
            stage1_enabled=True,
            stage1=[256] * 4,
            offset=0,
            gain=1.0,
        ),
        offsets=[0.0] * 4,
        digital_gain=1.0,
        remosaic=None,
        software=None,
    )
    cases.append(v)
    expected.append(arm.run(v))
    inputs = "".join(
        "awb-measurement-binding " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(command):
        actual = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        ).stdout.splitlines()
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                next(j // 2 for j, (x, y) in enumerate(zip(a, b)) if x != y),
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
    final = bytes.fromhex(expected[-1])
    report = dict(
        binarySha256=sha,
        cases=len(cases),
        mismatches=0,
        arm="--arm" in sys.argv,
        checkpoint=dict(
            blc=list(struct.unpack_from("<4i", final, 0x10)),
            inverse=list(struct.unpack_from("<3H", final, 0x5A)),
            overexposure=struct.unpack_from("<i", final, 0x60)[0],
        ),
        scope="Full AwbReCfgPregnBlc return for linear BayerNR/Gain1 with no sensor OTP",
        limitations=[
            "Other input/working-mode/apply-position and OTP branches remain separate.",
            "AWB offsets are supplied already selected; original calibration interpolation executes on constant tables matching those inputs.",
            "Logging is an explicit adapter; remaining numerical bodies execute.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-binding-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
