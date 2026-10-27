#!/usr/bin/env python3
"""Compare ISO binding with the actual linear prefix of awbProcessing.

Stops immediately after the native ISO store, before raw-statistics/proxy work.
AE proxies are absent; logs are adapters. Gain arithmetic is original ARM code.
"""

import hashlib
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, RETURN, regs, fhex, f32


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.logs = {p & ~1 for n, p in self.symbols.items() if n == "xcam_print_log"}
        self.reached = False

    def hook(self, uc, address, size, user):
        if address == 0x11FA14:
            self.reached = True
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        if address in self.logs:
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, gains):
        self.uc.mem_write(HEAP, bytes(0x3700))
        args = bytearray(0x100)
        struct.pack_into("<I", args, 0, HEAP + 0x20000)
        struct.pack_into("<I", args, 0x28, HEAP + 0x30000)
        self.uc.mem_write(HEAP + 0x10000, bytes(args))
        self.uc.mem_write(HEAP + 0x20000, struct.pack("<II", HEAP, 1))
        self.uc.mem_write(HEAP + 0x30000, struct.pack("<I", HEAP + 0x40000))
        source = bytearray(0x200)
        struct.pack_into("<3f", source, 0x2C, *gains)
        self.uc.mem_write(HEAP + 0x40000, bytes(source))
        self.reached = False
        self.invoke("awbProcessing", [HEAP + 0x10000, 0], instructions=100000)
        assert self.reached
        return struct.unpack("<I", self.uc.mem_read(HEAP + 0x5C, 4))[0]


def main():
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    arm = Original()
    rng = random.Random(0x41574249)
    cases = [
        [a, d, i]
        for a in (-2.0, 0.0, 0.5, 1.0, 1.25, 8.0, 64.0)
        for d in (0.0, 0.5, 1.0, 1.5)
        for i in (0.5, 1.0, 2.25)
    ]
    cases += [[f32(rng.uniform(-1, 32)) for _ in range(3)] for _ in range(256)]
    expected = [f"{arm.run(v):08x}" for v in cases]
    inputs = "".join(
        "awb-linear-iso " + ",".join(fhex(n) for n in v) + "\n" for v in cases
    )

    invalid = [
        "7fc00000,3f800000,3f800000",
        "3f800000,7f800000,3f800000",
        "3f800000,3f800000,ff800000",
        "7f7fffff,3f800000,3f800000",
    ]
    inputs += "".join("awb-linear-iso " + v + "\n" for v in invalid)
    expected += ["error:NonFinite"] * len(invalid)

    def compare(command):
        r = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        )
        assert r.stdout.splitlines() == expected

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
    import json

    report = dict(
        kind="native-linear-awb-iso-binding",
        cases=len(cases),
        checkedInputErrors=len(invalid),
        mismatches=0,
        arm="--arm" in sys.argv,
        binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        scope="Original awbProcessing entry through completed linear ISO store at context +0x5c",
        limitations=[
            "Stops before statistics/proxy/controller work; not a full wrapper invocation.",
            "Finite gains only; Rust rejects nonfinite input/output. HDR ISO selection is separate.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-linear-iso-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
