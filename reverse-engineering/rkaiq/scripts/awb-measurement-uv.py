#!/usr/bin/env python3
"""Compare the actual inline UV polygon loop from native calibration update."""

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
        self.symbols["uv-checkpoint"] = 0xD240F

    def hook(self, uc, address, size, user):
        if address == 0xD24D2:
            self.completed = True
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        super().hook(uc, address, size, user)

    def run(self, u, v):
        calibration = bytearray(0x200)
        calibration[0xF0] = 1
        struct.pack_into("<I", calibration, 0x158, HEAP + 0x2000)
        source = bytearray(0x480)
        struct.pack_into("<I", source, 0x43C, HEAP + 0x3000)
        light = bytearray(0xFC)
        struct.pack_into("<8f", light, 0x28, *(u + v))
        self.uc.mem_write(HEAP, bytes(calibration))
        self.uc.mem_write(HEAP + 0x1000, bytes(source))
        self.uc.mem_write(HEAP + 0x2000, bytes([0xA5]) * 36)
        self.uc.mem_write(HEAP + 0x3000, bytes(light))
        self.uc.reg_write(regs.UC_ARM_REG_R5, HEAP)
        self.uc.reg_write(regs.UC_ARM_REG_R6, HEAP + 0x1000)
        self.completed = False
        self.invoke("uv-checkpoint")
        assert self.completed
        for offset, original in ((0, calibration), (0x1000, source), (0x3000, light)):
            assert bytes(self.uc.mem_read(HEAP + offset, len(original))) == original
        return bytes(self.uc.mem_read(HEAP + 0x2000, 36)).hex()


def bits(x):
    return f"{struct.unpack('<I', struct.pack('<f', x))[0]:08x}"


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    cases = []
    expected = []
    arm = Original()
    rng = random.Random(0x5556504F)

    def add(u, v):
        cases.append(dict(u=list(map(bits, u)), v=list(map(bits, v))))
        expected.append(arm.run(u, v))

    for light in wb["autoPara"]["lightSources"]:
        add(light["uvRegion"]["u"], light["uvRegion"]["v"])
    pinned = "".join(expected)
    for i in range(400):
        u = [rng.uniform(-10, 5000) for _ in range(4)]
        v = [rng.uniform(-10, 5000) for _ in range(4)]
        if i % 4 == 0:
            v = [128.0] * 4
        if i % 4 == 1:
            u = [(j + 0.5) / 16 for j in range(4)]
            v = [(3 - j + 0.5) / 16 for j in range(4)]
        if i % 4 == 2:
            v[1] = v[0]
        add(u, v)
    inputs = "".join(
        "awb-measurement-uv " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )
    inputs += "awb-measurement-iq-uv " + json.dumps(wb, separators=(",", ":")) + "\n"
    expected.append(pinned)

    def compare(cmd):
        actual = subprocess.run(
            cmd, input=inputs, text=True, capture_output=True, check=True
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
    report = dict(
        binarySha256=sha,
        iqSha256=iq_sha,
        nativeCases=len(cases),
        iqLoaderCases=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        nativeCheckpoint="ELF 0xc240e through 0xc24d2",
        scope="Complete original inline UV loop including Q4 coordinates, polygon closure and inverse slopes",
        limitations=[
            "Register/stack/calibration ownership is explicitly seeded; execution stops before adjacent XY conversion, not full UpdateAwbCalibV2Para return.",
            "Finite inputs; complete startup assembly and live measurement enable remain separate.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-measurement-uv-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
