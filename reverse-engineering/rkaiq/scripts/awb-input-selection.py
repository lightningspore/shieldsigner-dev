#!/usr/bin/env python3
"""Compare native AWB input helpers and prepare startup source selection."""

import hashlib
import json
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, RETURN, regs


class Original(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.update = next(
            p & ~1 for n, p in self.symbols.items() if "UpdateAwbCalibV2Para" in n
        )
        self.logging = {
            p & ~1 for n, p in self.symbols.items() if n == "xcam_print_log"
        }
        self.stop = False

    def hook(self, uc, address, size, user):
        if self.stop and address == self.after_position:
            self.completed = True
            uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
            return
        if address == self.update or address in self.logging:
            uc.reg_write(regs.UC_ARM_REG_R0, 0)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        c = bytearray(0x3700)
        struct.pack_into("<I", c, 0x34, v["mode"])
        c[0x2ECE] = v["selector"]
        gain = bytearray(0x100)
        if v["gain"] is not None:
            struct.pack_into("<I", c, 0x6C, HEAP + 0x40000)
            struct.pack_into("<I", gain, 0x18, int(v["gain"], 16))
        self.uc.mem_write(HEAP + 0x40000, bytes(gain))
        self.uc.mem_write(HEAP, bytes(c))
        self.stop = False
        flags = []
        for name in ("calcInputBitIs12Bit", "calcInputRightShift212Bit"):
            self.uc.mem_write(HEAP + 0x8000, b"\xa5")
            self.invoke(
                next(n for n in self.symbols if name in n), [HEAP + 0x8000, HEAP]
            )
            flags.append(bool(self.uc.mem_read(HEAP + 0x8000, 1)[0]))
        record = bytes([0xA5]) * 1204
        c[0x2E90 : 0x2E90 + 1204] = record
        struct.pack_into("<I", c, 0x80, HEAP + 0x10000)
        struct.pack_into("<I", c, 0x130, HEAP + 0x20000)
        cal = bytearray(0x400)
        struct.pack_into("<I", cal, 4, v["source"])
        cal[8] = v["frame"]
        self.uc.mem_write(HEAP, bytes(c))
        self.uc.mem_write(HEAP + 0x10000, bytes(0x700))
        self.uc.mem_write(HEAP + 0x20000, bytes(cal))
        self.stop = True
        self.completed = False
        self.invoke(next(n for n in self.symbols if "AwbPrepareV32" in n), [HEAP])
        assert self.completed
        return dict(
            flags=flags,
            success=True,
            record=bytes(self.uc.mem_read(HEAP + 0x2E90, 1204)).hex(),
        )


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original()
    # The store immediately before this address publishes apply-position.
    arm.after_position = 0xD3B90
    cases = []
    expected = []
    for mode in (0, 16, 17, 31, 32, 33, 48):
        for source in (0, 1, 3, 4):
            for gain in (
                None,
                "00000000",
                "3f800000",
                "40000000",
                "7f800000",
                "ff800000",
                "7fc00000",
            ):
                for selector in (0, 1, 2, 3, 4):
                    frame = 0 if mode == 0 else (1 if mode < 32 else 2)
                    v = dict(
                        mode=mode,
                        source=source,
                        frame=frame,
                        gain=gain,
                        selector=selector,
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
    v = dict(mode=0, source=3, frame=0, gain="3f800000", selector=3, iq=wb)
    cases.append(v)
    expected.append(arm.run(v))
    inputs = "".join(
        "awb-input-selection " + json.dumps(v, separators=(",", ":")) + "\n"
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
            assert a == b, (
                i,
                a["flags"],
                b["flags"],
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
        iqSha256=iq_sha,
        cases=len(cases),
        iqLoaderCases=1,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Both input bit helpers plus native prepare startup source selection and complete SDK record preservation",
        limitations=[
            "Calibration update is an explicit success boundary; prepare stops after apply-position publication, before geometry.",
            "Checked startup domain uses valid raw frame/source selections; later exposure-dependent RawAuto selection is separate.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-input-selection-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
