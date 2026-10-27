#!/usr/bin/env python3
"""Compare fresh automatic software-result initialization with original ARM.

Only logging and allocation are host adapters. Calibration loading is already
covered separately; this test supplies its lines/reference gains explicitly.
Saved-site I/O and complete camera-session initialization are outside this test.
"""

import hashlib
import json
import struct
import subprocess
import sys

from differential import BINARY, HEAP, ROOT, regs
from awb_reference import OriginalAwb


class Original(OriginalAwb):
    def __init__(self):
        super().__init__(stdlib=True)
        self.logs = {
            p & ~1: n
            for n, p in self.symbols.items()
            if n in ("xcam_get_awb_log_level", "xcam_print_log")
        }
        self.cursor = HEAP + 0x60000

    def hook(self, uc, address, size, user):
        name = self.logs.get(address, self.stubs.get(address))
        if name in ("malloc", "free", "xcam_get_awb_log_level", "xcam_print_log"):
            a = uc.reg_read(regs.UC_ARM_REG_R0)
            if name == "malloc":
                assert 0 < a < 0x10000
                uc.mem_write(self.cursor, bytes([0xA5]) * a)
                uc.reg_write(regs.UC_ARM_REG_R0, self.cursor)
                self.cursor += (a + 15) & ~15
            elif name == "xcam_get_awb_log_level":
                uc.mem_write(a, b"\0")
                uc.mem_write(uc.reg_read(regs.UC_ARM_REG_R1), b"\0")
            elif name == "free":
                raise AssertionError("Fresh initialization must not free allocations")
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, first, expected):
        self.cursor = HEAP + 0x60000
        c, cfg = bytearray(0x3700), bytearray(0x800)

        def put(b, o, *v):
            struct.pack_into("<" + "I" * len(v), b, o, *v)

        put(c, 0x38, 5)
        c[0x3C] = 1
        put(c, 0x8C, HEAP + 0x14000)
        heads = (0x3478, 0x3490, 0x3498, 0x355C, 0x3564, 0x3598, 0x35A0)
        for h in heads:
            put(c, h, HEAP + h, HEAP + h)
        cfg[0x139] = len(expected["gains"])
        put(cfg, 0x13C, first)
        put(cfg, 0x368, HEAP + 0x20000)
        put(cfg, 0x4B4, expected["countdown"])
        for i, line in enumerate(expected["lines"]):
            put(cfg, 0x348 + i * 16, *line)
        for i, gain in enumerate(expected["gains"]):
            self.uc.mem_write(
                HEAP + 0x20000 + i * 0xE4 + 0x80, struct.pack("<4I", *gain)
            )
        self.uc.mem_write(HEAP, bytes(c))
        self.uc.mem_write(HEAP + 0x10000, struct.pack("<II", 0, 1))
        self.uc.mem_write(HEAP + 0x11000, struct.pack("<8I", 1, 0, 0, 0, 0, 0, 0, 0))
        self.uc.mem_write(HEAP + 0x12000, bytes(0x400))
        self.uc.mem_write(HEAP + 0x14000, bytes(cfg))
        self.uc.mem_write(HEAP + 0x16000, bytes(20))
        status = self.invoke(
            next(n for n in self.symbols if "InitinalSwResParaCom2" in n),
            [HEAP + 0x10000, HEAP + 0x11000, HEAP + 0x12000, HEAP + 0x14000],
            stack=struct.pack("<II", HEAP + 0x16000, HEAP),
        )
        assert status == 0, status

        def words(offset, count=1):
            return list(
                struct.unpack(
                    "<" + "I" * count, self.uc.mem_read(HEAP + offset, count * 4)
                )
            )

        for h in heads:
            assert words(h, 2) == [HEAP + h] * 2
        actual = dict(
            current=words(0x353C, 4),
            previous=words(0x3578, 4),
            low_current=words(0x353C, 4),
            temperature=words(0x3658, 3),
            frame=words(0x33AC)[0],
            countdown=struct.unpack("<i", self.uc.mem_read(HEAP + 0x144B4, 4))[0],
            history_lengths=[0, 0, 0],
            diagnostics=[words(o)[0] for o in (0x3484, 0x3488, 0x33CC, 0x33F8, 0x343C)],
        )
        assert actual == {k: expected[k] for k in actual}, (first, actual, expected)
        return actual


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    iq = json.loads(
        (
            ROOT
            / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
        ).read_text()
    )
    wb = iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"]
    cases = [
        json.dumps(dict(iq=wb, first=i), separators=(",", ":"))
        for i in range(len(wb["autoPara"]["lightSources"]))
    ]
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    inputs = "".join("awb-initial-gain-state " + v + "\n" for v in cases)
    result = subprocess.run(
        [str(binary)], input=inputs, text=True, capture_output=True, check=True
    )
    arm = Original()
    expected = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(expected) == len(cases)
    for i, v in enumerate(expected):
        arm.run(i, v)
    if "--arm" in sys.argv:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
        command = [
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
        result = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        )
        assert [json.loads(line) for line in result.stdout.splitlines()] == expected
    report = dict(
        kind="fresh-automatic-gain-state",
        cases=len(cases),
        mismatches=0,
        arm="--arm" in sys.argv,
        originalSha256=sha,
        scope="Software-result initializer; allocation/logging adapters; not full session initialization",
        limitations=[
            "Fresh automatic non-bypass state only, with remosaic disabled.",
            "Compares current/previous gains, gain-derived temperature, dispatcher fields, empty histories and five scalar diagnostics; not every context byte.",
            "Calibration loading is checked separately; saved-site loading, measurement caches and numeric preprocessing remain session inputs.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-initial-gain-state-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
