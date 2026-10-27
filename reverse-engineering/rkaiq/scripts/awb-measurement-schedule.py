#!/usr/bin/env python3
"""Compare complete native time-share measurement records, including untouched bytes."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, regs


class Original(OriginalArm):
    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "strcpy":
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            data = bytearray()
            while True:
                x = uc.mem_read(b + len(data), 1)[0]
                data.append(x)
                if x == 0:
                    break
                assert len(data) < 64
            uc.mem_write(a, bytes(data))
            uc.reg_write(regs.UC_ARM_REG_R0, a)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        cal = bytearray(0x200)
        strategy = bytearray(0x480)
        struct.pack_into("<HH", cal, 0x38, v["uv_enabled"], 0)
        struct.pack_into("<H", cal, 0x3C, v["yuv_enabled"])
        cal[0x44] = v["capacity"]
        for at, offset, key in (
            (0x154, 0x3000, "rt_yuv"),
            (0x158, 0x4000, "uv"),
            (0x174, 0x5000, "xy"),
        ):
            struct.pack_into("<I", cal, at, HEAP + offset)
            self.uc.mem_write(HEAP + offset, bytes.fromhex(v[key]))
        if v["xy_detection"] is not None:
            strategy[0x94] = 1
            struct.pack_into("<I", strategy, 0x90, int(v["xy_detection"]))
        struct.pack_into("<I", strategy, 0x398, len(v["groups"]))
        for i, g in enumerate(v["groups"]):
            struct.pack_into("<7I", strategy, 0x39C + i * 28, *g["indices"])
            strategy[0x40C + i * 7 : 0x413 + i * 7] = bytes(g["rt_yuv"])
            struct.pack_into("<I", strategy, 0x428 + i * 4, g["count"])
        strategy[0x440:0x480] = bytes.fromhex(v["signature"])
        self.uc.mem_write(HEAP, bytes(cal))
        self.uc.mem_write(HEAP + 0x1000, bytes(strategy))
        self.uc.mem_write(HEAP + 0x2000, bytes.fromhex(v["record"]))
        symbol = next(n for n in self.symbols if "ConfigHwParaTimeShare" in n)
        self.invoke(symbol, [HEAP, HEAP + 0x1000, 0, HEAP + 0x2000])
        assert bytes(self.uc.mem_read(HEAP, len(cal))) == cal
        assert bytes(self.uc.mem_read(HEAP + 0x1000, len(strategy))) == strategy
        return bytes(self.uc.mem_read(HEAP + 0x2000, 1204)).hex()


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    rng = random.Random(0x41575343)
    arm = Original(BINARY)
    cases = []
    expected = []

    def blob(n):
        return bytes(rng.randrange(256) for _ in range(n)).hex()

    for i in range(360):
        groups = []
        for j in range(1 + i % 4):
            groups.append(
                dict(
                    count=(i // 4 + j) % 5,
                    indices=[
                        15 if (i + j + k) % 5 == 0 else (i + j + k) % 7
                        for k in range(7)
                    ],
                    rt_yuv=[bool((i + j + k) % 2) for k in range(7)],
                )
            )
        record = bytearray.fromhex(blob(1204))
        struct.pack_into("<i", record, 0x450, -1 if i % 3 == 0 else i % len(groups))
        name = b"NORMAL" if i % 2 else b"TIMESHARE-LIGHTS"
        v = dict(
            record=record.hex(),
            groups=groups,
            rt_yuv=blob(7 * 32),
            uv=blob(7 * 36),
            xy=blob(7 * 48),
            signature=(name + b"\0" + bytes.fromhex(blob(63 - len(name)))).hex(),
            uv_enabled=i % 4,
            yuv_enabled=i % 3,
            capacity=(i // 7) % 5,
            xy_detection=[None, False, True][(i // 3) % 3],
        )
        cases.append(v)
        expected.append(arm.run(v))
    inputs = "".join(
        "awb-measurement-schedule " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(cmd):
        actual = subprocess.run(
            cmd, input=inputs, text=True, capture_output=True, check=True
        ).stdout.splitlines()
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                next((j // 2 for j, (x, y) in enumerate(zip(a, b)) if x != y), None),
            )

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    if "--arm" in sys.argv:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
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
                f"type=bind,src={directory},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        cases=len(cases),
        mismatches=0,
        arm="--arm" in sys.argv,
        elfEntry="0xc9240",
        scope="Full 1204-byte time-share output record and unchanged calibration/strategy",
        limitations=[
            "Calibrated regions and time-share groups are explicit inputs; IQ loading and initial complete measurement configuration remain separate.",
            "Logging level zero; strcpy/memset are explicit standard-library adapters.",
            "No live AWB measurement enable or physical configuration association is claimed.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-schedule-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
