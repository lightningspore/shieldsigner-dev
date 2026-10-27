#!/usr/bin/env python3
"""Compare full original FAST grouping and complete measurement configuration."""

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
        if address == 0xD9646:
            self.branch = "paired-gap"
        if address == 0xD97A8:
            self.groups = [
                list(
                    struct.unpack(
                        "<3i",
                        uc.mem_read(
                            uc.reg_read(regs.UC_ARM_REG_SP) + 0x4C + i * 12, 12
                        ),
                    )
                )
                for i in range(4)
            ]
        name = self.stubs.get(address)
        a, b, c = [
            uc.reg_read(r)
            for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1, regs.UC_ARM_REG_R2)
        ]
        if address in self.logging:
            uc.reg_write(regs.UC_ARM_REG_R0, 0)
        elif name == "malloc":
            assert a < 65536
            pointer = self.next
            self.next += (a + 15) & ~15
            uc.mem_write(pointer, bytes(a))
            uc.reg_write(regs.UC_ARM_REG_R0, pointer)
        elif name == "free":
            pass
        elif name == "strcpy":
            text = bytearray()
            while True:
                x = uc.mem_read(b + len(text), 1)[0]
                text.append(x)
                if x == 0:
                    break
                assert len(text) < 64
            uc.mem_write(a, bytes(text))
            uc.reg_write(regs.UC_ARM_REG_R0, a)
        elif name in ("__aeabi_idiv", "__aeabi_idivmod"):
            a = a if a < 0x80000000 else a - 0x100000000
            b = b if b < 0x80000000 else b - 0x100000000
            assert b != 0
            q = abs(a) // abs(b)
            q = -q if (a < 0) != (b < 0) else q
            uc.reg_write(regs.UC_ARM_REG_R0, q & 0xFFFFFFFF)
            if name == "__aeabi_idivmod":
                uc.reg_write(regs.UC_ARM_REG_R1, (a - q * b) & 0xFFFFFFFF)
        else:
            return super().hook(uc, address, size, user)
        uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))

    def run(self, v):
        cal = bytearray(0x200)
        cal[0xF0] = len(v["lights"])
        struct.pack_into("<I", cal, 0x174, HEAP + 0x30000)
        cfg = bytearray(0x500)
        cfg[0x139] = v["valid"]
        if v["manual"] is not None:
            struct.pack_into("<I", cfg, 0xC, 1)
            for i, row in enumerate(v["manual"]):
                struct.pack_into("<8i", cfg, 0x10 + i * 32, *row)
        lights = b"".join(struct.pack("<12i", *row) for row in v["lights"])
        self.uc.mem_write(HEAP, bytes(cal))
        self.uc.mem_write(HEAP + 0x10000, bytes(cfg))
        self.uc.mem_write(HEAP + 0x20000, bytes([0xA5]) * 1204)
        self.uc.mem_write(HEAP + 0x30000, lights)
        self.next = HEAP + 0x40000
        self.groups = None
        self.branch = "manual" if v["manual"] is not None else "balanced"
        self.invoke(
            next(n for n in self.symbols if "ConfigHwParaFstFF" in n),
            [HEAP, HEAP + 0x10000, 0, HEAP + 0x20000],
        )
        assert (
            bytes(self.uc.mem_read(HEAP, len(cal))) == cal
            and bytes(self.uc.mem_read(HEAP + 0x10000, len(cfg))) == cfg
            and bytes(self.uc.mem_read(HEAP + 0x30000, len(lights))) == lights
        )
        return dict(
            groups=self.groups,
            record=bytes(self.uc.mem_read(HEAP + 0x20000, 1204)).hex(),
        )


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original()
    rng = random.Random(0x46415354)
    cases = []
    expected = []
    branches = {}
    for i in range(256):
        n = 4 + i % 4
        lights = []
        for j in range(n):
            left = rng.randrange(-4000, 4000)
            if i % 5 == 0:
                left = j * 100
            lights.append(
                [
                    left,
                    left + rng.randrange(1, 400),
                    rng.randrange(0, 4000),
                    rng.randrange(-4000, 0),
                    left - 100,
                    left + 500,
                    rng.randrange(0, 5000),
                    rng.randrange(-5000, 0),
                    0x11223344,
                    0x556677,
                    123,
                    456,
                ]
            )
        manual = (
            [[rng.randrange(-8192, 8192) for _ in range(8)] for _ in range(4)]
            if i % 7 == 0
            else None
        )
        v = dict(lights=lights, valid=n if i % 3 else i % (n + 1), manual=manual)
        cases.append(v)
        expected.append(arm.run(v))
        branches[arm.branch] = branches.get(arm.branch, 0) + 1
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    lights = []
    for light in wb["autoPara"]["lightSources"]:
        values = light["xyRegion"]["normal"] + light["xyRegion"]["big"]
        arm.uc.mem_write(HEAP + 0x70000, struct.pack("<8f", *values))
        arm.uc.mem_write(HEAP + 0x71000, bytes(48))
        arm.invoke(
            next(n for n in arm.symbols if "JsonXyParaFixed3" in n),
            [HEAP + 0x70000, HEAP + 0x71000],
        )
        lights.append(list(struct.unpack("<12i", arm.uc.mem_read(HEAP + 0x71000, 48))))
    iq_index = len(cases)
    for manual in (False, True):
        selected = json.loads(json.dumps(wb))
        if manual:
            selected["autoPara"]["earlierAwbAct"]["mode"] = (
                "CALIB_AWB_EARLACT_XYREG_FIXED"
            )
        regions = selected["autoPara"]["earlierAwbAct"]["xyRegion"]
        v = dict(
            lights=lights,
            valid=len(lights),
            manual=[r["normal"] + r["big"] for r in regions] if manual else None,
            iq=selected,
        )
        cases.append(v)
        expected.append(arm.run(v))
        branches[arm.branch] = branches.get(arm.branch, 0) + 1
    assert set(branches) == {"manual", "balanced", "paired-gap"}
    inputs = "".join(
        "awb-fast-configuration " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(command):
        actual = [
            json.loads(line)
            for line in subprocess.run(
                command, input=inputs, text=True, capture_output=True, check=True
            ).stdout.splitlines()
        ]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                a["groups"],
                b["groups"],
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
        cases=len(cases),
        iqSha256=iq_sha,
        iqLoaderCases=2,
        branchCoverage=branches,
        iqGroups=expected[iq_index]["groups"],
        iqPhysicalLights=bytes.fromhex(expected[iq_index]["record"])[0x48],
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Full ConfigHwParaFstFF return, actual native sort/group memberships, merged regions and all SDK bytes",
        limitations=[
            "Calibrated region conversion and FAST scene loading are joined for IQ cases; whole startup record assembly remains separate.",
            "Allocation, memory/string, integer division and logging are explicit adapters; native grouping/sort/merge bodies execute.",
            "Automatic checked domain has four to seven calibrated lights.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-fast-configuration-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
