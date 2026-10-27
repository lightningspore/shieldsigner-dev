#!/usr/bin/env python3
"""Compare AWB prepare geometry after an explicit calibration-update boundary."""

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
        self.update = next(
            p & ~1 for n, p in self.symbols.items() if "UpdateAwbCalibV2Para" in n
        )

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if (
            address == self.update
            or address in self.logging
            or name == "xcam_print_log"
        ):
            uc.reg_write(regs.UC_ARM_REG_R0, 0)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        if name == "__aeabi_idiv":
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            a = a if a < 0x80000000 else a - 0x100000000
            b = b if b < 0x80000000 else b - 0x100000000
            assert b != 0
            value = abs(a) // abs(b)
            value = -value if (a < 0) != (b < 0) else value
            uc.reg_write(regs.UC_ARM_REG_R0, value & 0xFFFFFFFF)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        c = bytearray(0x36CC)
        strategy = bytearray(0x700)
        cal = bytearray(0x400)
        algorithm = bytearray(0x600)
        for at, value in (
            (0x80, HEAP + 0x10000),
            (0x8C, HEAP + 0x20000),
            (0x130, HEAP + 0x30000),
            (0x40, v["width"]),
            (0x44, v["height"]),
            (0x33AC, 1),
            (0x369C, v["scale"]),
            (0x2EC4, v["downsample"]),
        ):
            struct.pack_into("<I", c, at, value)
        struct.pack_into("<f", strategy, 0x608, v["count"])
        struct.pack_into("<f", strategy, 0x254, v["absolute"])
        struct.pack_into("<I", cal, 0x5C, 0 if v["manual"] is None else 1)
        if v["manual"] is not None:
            struct.pack_into("<4f", strategy, 0x70, *v["manual"])
        if v["multi"] is not None:
            cal[0x280] = 1
            for i, window in enumerate(v["multi"]):
                struct.pack_into("<4f", cal, 0x240 + i * 16, *window)
        for offset, data in (
            (0, c),
            (0x10000, strategy),
            (0x20000, algorithm),
            (0x30000, cal),
        ):
            self.uc.mem_write(HEAP + offset, bytes(data))
        status = self.invoke(
            next(n for n in self.symbols if "AwbPrepareV32" in n), [HEAP]
        )
        status = status if status < 0x80000000 else status - 0x100000000
        if status:
            return dict(status=status)
        out = bytes(self.uc.mem_read(HEAP, len(c)))
        algo = bytes(self.uc.mem_read(HEAP + 0x20000, len(algorithm)))
        return dict(
            status=0,
            window=list(struct.unpack_from("<4H", out, 0x2ED0)),
            downsample=struct.unpack_from("<I", out, 0x2EC4)[0],
            block=list(out[0x33B8:0x33BA]),
            dimensions=list(struct.unpack_from("<2I", out, 0x33BC)),
            multi=[
                list(struct.unpack_from("<4H", out, 0x30F4 + i * 8)) for i in range(4)
            ]
            if v["multi"] is not None
            else None,
            count=struct.unpack_from("<I", algo, 0x1F0)[0],
            absolute=struct.unpack_from("<I", algo, 0x49C)[0],
        )


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original()
    rng = random.Random(0x41574745)
    cases = []
    expected = []
    for i in range(256):
        width = [640, 2304, 2336, 2337, 4096][i % 5]
        height = [480, 1296, 2048][i % 3]
        manual = (
            None
            if i % 4 == 0
            else [
                rng.uniform(0, 0.2),
                rng.uniform(0, 0.2),
                rng.uniform(0.4, 0.7),
                rng.uniform(0.4, 0.7),
            ]
        )
        if i % 13 == 0:
            manual = [0.8, 0.0, 0.5, 1.0]
        v = dict(
            width=width,
            height=height,
            manual=manual,
            downsample=i % 2,
            multi=None
            if i % 3 == 0
            else [
                [0.0, 0.0, 1.0, 1.0],
                [0.1, 0.2, 0.3, 0.4],
                [0.0, 0.0, 0.0, 0.0],
                [0.2, 0.1, 0.5, 0.3],
            ],
            scale=1 + i % 3,
            count=0.002,
            absolute=0.01,
        )
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
    v = dict(
        width=2304,
        height=1296,
        manual=None,
        downsample=1,
        multi=None,
        scale=1,
        count=wb["autoExtPara"]["probCalcWp"]["wpNumPercTh"],
        absolute=wb["autoPara"]["wpDiffLumaWeight"]["wpDiffWeiEnableTh"][
            "wpDiffWeiNoTh"
        ],
        iq=wb,
    )
    cases.append(v)
    expected.append(arm.run(v))
    inputs = "".join(
        "awb-measurement-geometry " + json.dumps(v, separators=(",", ":")) + "\n"
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
            assert a == b, (i, a, b)

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
        cases=len(cases),
        iqLoaderCases=1,
        iqSha256=iq_sha,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="AwbPrepareV32 window/downsampling/multiwindow/count geometry after calibration success",
        limitations=[
            "Calibration update is an explicit success boundary; prior input selector/bit-depth setup is bypassed using preconfigured context.",
            "Logging and signed integer division are explicit adapters; full original prepare returns normally.",
            "Input dimensions are positive u16 and count arithmetic remains within signed i32; complete measurement startup is separate.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-geometry-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
