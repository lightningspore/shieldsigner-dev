#!/usr/bin/env python3
"""Compare fresh zero-reserved time-share initialization with original ARM."""

import hashlib
import json
import subprocess
import sys
from awb_reference import OriginalAwb, RUNTIME
from differential import BINARY, HEAP, ROOT, regs


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "__aeabi_idivmod":
            self.runtime.invoke(
                "__aeabi_idivmod",
                [uc.reg_read(regs.UC_ARM_REG_R0), uc.reg_read(regs.UC_ARM_REG_R1)],
            )
            for reg in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1):
                uc.reg_write(reg, self.runtime.uc.reg_read(reg))
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def main():
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == "421df6d09247848a7f733d25ef45b726bc6366c8fc12be84751f6b408c1d92cd"
    )
    arm = Original()
    cases = []
    expected = []
    symbol = next(n for n in arm.symbols if "AwbTimeShareInit" in n)
    for total in range(1, 8):
        for capacity in range(1, 5):
            if (total + capacity - 1) // capacity > 4:
                continue
            arm.uc.mem_write(HEAP, bytes(164))
            arm.invoke(symbol, [total, capacity, 0, HEAP])
            cases.append((total, capacity))
            expected.append(bytes(arm.uc.mem_read(HEAP, 164)).hex())
    inputs = "".join(f"awb-schedule-init {n} {c}\n" for n, c in cases)

    def compare(command):
        r = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        )
        actual = r.stdout.splitlines()
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (cases[i], a, b)

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
        kind="fresh-zero-reserved-awb-schedule",
        binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        runtimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        cases=len(cases),
        bytesEach=164,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Complete original AwbTimeShareInit with zeroed fresh table and zero reserved lights",
        limitations=[
            "Nonzero reserved-light policy and configurations requiring more than four groups are excluded.",
            "No camera writes or outer reconfiguration policy in this comparison.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-schedule-init-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
