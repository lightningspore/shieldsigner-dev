#!/usr/bin/env python3
"""Execute the original single-camera factory's post-init binding to return.

Module lookup and AwbInitV32 are explicit boundaries supplying owned context
storage. The actual factory writes/return/stack guard execute in original ARM.
"""

import hashlib
import json
import struct
import subprocess
import sys
from differential import OriginalArm, BINARY, HEAP, ROOT, regs


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.symbols["single-awb-create"] = self.resolve_symbol(
            "create_context", entry=0xCD5F4
        )
        self.init = next(
            p & ~1 for n, p in self.symbols.items() if n.startswith("_Z10AwbInitV32")
        )
        self.calls = []

    def hook(self, uc, address, size, user):
        if address in (0xCD598, self.init):
            self.calls.append(address)
            if address == self.init:
                uc.mem_write(uc.reg_read(regs.UC_ARM_REG_R0), struct.pack("<I", HEAP))
                uc.reg_write(regs.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(regs.UC_ARM_REG_R0, HEAP + 0x10000)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, fill):
        c = bytes([fill]) * 0x36CC
        self.uc.mem_write(HEAP, c)
        self.uc.mem_write(HEAP + 0x20000, bytes(0x50))
        self.uc.mem_write(HEAP + 0x30000, bytes(4))
        self.calls = []
        self.invoke("single-awb-create", [HEAP + 0x30000, HEAP + 0x20000])
        assert self.calls == [0xCD598, self.init]
        assert bytes(self.uc.mem_read(HEAP + 0x30000, 4)) == struct.pack("<I", HEAP)
        after = bytearray(self.uc.mem_read(HEAP, len(c)))
        scale = struct.unpack_from("<I", after, 0x369C)[0]
        assert after[0x3698] == 0
        after[0x3698] = c[0x3698]
        after[0x369C:0x36A0] = c[0x369C:0x36A0]
        assert bytes(after) == c, "Unexpected post-init context modification"
        return scale


def main():
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    arm = Original()
    expected = [str(arm.run(fill)) for fill in (0, 0x5A, 0xA5, 0xFF)]

    def compare(command):
        p = subprocess.run(
            command,
            input="awb-single-camera-scale\n" * 4,
            capture_output=True,
            text=True,
            check=True,
        )
        assert p.stdout.splitlines() == expected

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
        kind="single-camera-awb-scale-binding",
        binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        cases=4,
        scale=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        elfEntry="0xbd5f4",
        scope="Original single-camera factory through normal return, preserving all context bytes except its scale and single/group-mode bindings",
        limitations=[
            "Module lookup and native AwbInitV32 are controlled success boundaries; no full calibration/startup initialization equivalence.",
            "Camera-group creator is separate and not used for this single-CIF route.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-single-camera-scale-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
