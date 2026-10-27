#!/usr/bin/env python3
"""Compare original preprocessor continuation instructions with Rust dispatch."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import BINARY, HEAP, RETURN, ROOT, OriginalArm, f32, regs


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.symbols["prepared-continuation"] = 0xD4AE1

    def hook(self, uc, address, size, user):
        if address == 0xD803C:
            self.calculated = True
            # Gain wrapper has its own full original-body equivalence suite.
            # Supply its explicit current/previous result to isolate dispatch.
            for offset in (0x353C, 0x352C):
                uc.mem_write(HEAP + offset, struct.pack("<4f", *self.computed))
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        if address == 0xD12B0:  # PrintLog; no numerical policy.
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        if address == 0xD4260:  # Stop at ReconfigHwParaV32 entry.
            self.reconfigured = True
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        if address == 0xD4890:  # Common preprocessor epilogue.
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        ctx, cfg = bytearray(0x4000), bytearray(0x800)
        struct.pack_into("<I", ctx, 0x8C, HEAP + 0x8000)
        struct.pack_into("<I", ctx, 0x33AC, v["frame"])
        struct.pack_into("<i", cfg, 0x4B4, v["countdown"])
        ctx[0x334A], ctx[0x13C] = v["update"], v["complete"]
        ctx[0x36A0] = v["scale"] is not None
        struct.pack_into("<4f", ctx, 0x353C, *v["current"])
        struct.pack_into("<4f", ctx, 0x352C, *v["previous"])
        if v["scale"] is not None:
            struct.pack_into("<f", ctx, 0x3588, v["scale"][0])
            struct.pack_into("<f", ctx, 0x3594, v["scale"][1])
        self.uc.mem_write(HEAP, bytes(ctx))
        self.uc.mem_write(HEAP + 0x8000, bytes(cfg))
        self.uc.reg_write(regs.UC_ARM_REG_R4, HEAP)
        self.uc.reg_write(regs.UC_ARM_REG_R5, 0x334A)
        self.uc.reg_write(regs.UC_ARM_REG_R8, HEAP + 0x9000)
        self.calculated = self.reconfigured = False
        self.computed = v["computed"]
        self.invoke("prepared-continuation")
        after = bytearray(self.uc.mem_read(HEAP, len(ctx)))
        after_cfg = bytearray(self.uc.mem_read(HEAP + 0x8000, len(cfg)))
        result = dict(
            gain=list(struct.unpack_from("<4I", after, 0x353C)),
            previous=list(struct.unpack_from("<4I", after, 0x352C)),
            countdown=struct.unpack_from("<i", after_cfg, 0x4B4)[0],
            frame=struct.unpack_from("<I", after, 0x33AC)[0],
            calculated=self.calculated,
            reconfigure=self.reconfigured,
        )
        for offset, length in [(0x353C, 16), (0x352C, 16), (0x33AC, 4)]:
            after[offset : offset + length] = ctx[offset : offset + length]
        after_cfg[0x4B4:0x4B8] = cfg[0x4B4:0x4B8]
        assert after == ctx and after_cfg == cfg
        return result


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == manifest["binaries"][0]["sha256"]
    arm = Original()
    rng = random.Random(0x44495350)
    cases = []
    expected = []
    coverage = {}
    for i in range(1024):
        gain = lambda: [f32(rng.uniform(0.1, 8.0)) for _ in range(4)]
        v = dict(
            current=gain(),
            previous=gain(),
            computed=gain(),
            frame=[0, 1, 3, 0xFFFFFFFF][i // 4 % 4],
            countdown=[-2147483648, -1, 0, 1, 2, 2147483647][i // 16 % 6],
            update=bool(i % 2),
            complete=bool(i // 2 % 2),
            scale=None
            if i // 4 % 2
            else [[1.0, 1.0], [0.0, 0.0], [-1.0, 2.0], [0.5, 4.0]][i // 8 % 4],
        )
        out = arm.run(v)
        cases.append(v)
        expected.append(out)
        key = (
            f"update{v['update']}:complete{v['complete']}:scale{v['scale'] is not None}"
        )
        coverage[key] = coverage.get(key, 0) + 1
    assert not arm.calls
    inputs = "".join(
        "awb-dispatch " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )

    def compare(command):
        p = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        )
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, cases[i], a, b)

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
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
        arm=replay,
        coverage=coverage,
        elfStart="0xc4ae0",
        initialRegisters=dict(r4="context", r5="0x334a update offset", r8="disabled logging context"),
        scope="Original standard preprocessor post-preparation dispatch: countdown, calculate/reconfigure decisions, red/blue scaling and frame increment.",
        limitations=[
            "Native execution starts at post-PrepareMeasureResult instruction; preceding preprocessing is covered separately.",
            "Gain wrapper is adapted to an explicit computed result; its original-body suite is separate.",
            "Stops at hardware reconfiguration entry or common epilogue; no hardware configuration/publication is tested.",
            "Finite synthetic gains/scales; scaling overflow is checked by Rust and excluded from equivalence.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-dispatch-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
